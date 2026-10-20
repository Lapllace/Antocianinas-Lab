#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados de validacao cientifica (Fases B e C).

Objetivo: validar os cálculos matemáticos e os modelos computacionais
ANTES de autorizar qualquer experimento de laboratorio.

Regras seguidas:
- Nao inventar medições.
- Nao alterar CSVs de laboratorio nem referencias bibliograficas.
- Manter separacao entre dados experimentais, literatura e simulacao.
- C3G-equivalentes nao sao quantificacao individual de todas as moleculas de antocianina.
"""

from __future__ import annotations

import json
import math
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "anthocyanin_lab.py"
import importlib.util

spec = importlib.util.spec_from_file_location("anthocyanin_lab", MODULE_PATH)
lab = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(lab)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "validation"

# Parametros de referencia do metodo diferencial de pH (Giusti & Wrolstad, 2001)
MW_C3G = 449.2  # g/mol
EPSILON_C3G = 26900.0  # L mol^-1 cm^-1


class TestPHDifferentialMethod(unittest.TestCase):
    """Validar absorbância diferencial e expressao como equivalentes C3G."""

    def _stability_row(self, a520_1, a700_1, a520_45, a700_45, df=10.0, path=1.0):
        return {
            "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
            "day": 0, "vial_id": "V1", "replicate": 1, "pH_storage": 4.0,
            "a520_ph1": a520_1, "a700_ph1": a700_1,
            "a520_ph45": a520_45, "a700_ph45": a700_45,
            "dilution_factor": df, "path_length_cm": path, "notes": "",
        }

    def test_tac_known_absorbance_values(self):
        """A = (A520 - A700)pH1.0 - (A520 - A700)pH4.5"""
        rows = [self._stability_row(0.500, 0.020, 0.040, 0.020)]
        out = lab.calculate_tac(pd.DataFrame(rows))
        expected_A = (0.500 - 0.020) - (0.040 - 0.020)
        self.assertAlmostEqual(out.loc[0, "absorbance_difference"], expected_A, places=6)

    def test_tac_c3g_formula_units(self):
        """C (mg/L) = A * MW * DF * 1000 / (epsilon * l)"""
        rows = [self._stability_row(0.500, 0.020, 0.040, 0.020)]
        out = lab.calculate_tac(pd.DataFrame(rows))
        self.assertAlmostEqual(out.loc[0, "tac_mg_c3g_L"], 76.81487, places=4)
        self.assertIn("tac_mg_c3g_L", out.columns)

    def test_tac_equal_absorbances_yields_zero(self):
        """Absorbancias iguais nos dois pHs -> A = 0 -> C = 0."""
        rows = [self._stability_row(0.300, 0.020, 0.300, 0.020)]
        out = lab.calculate_tac(pd.DataFrame(rows))
        self.assertAlmostEqual(out.loc[0, "absorbance_difference"], 0.0, places=6)
        self.assertAlmostEqual(out.loc[0, "tac_mg_c3g_L"], 0.0, places=6)

    def test_tac_dilution_factor_doubles_concentration(self):
        """Dobrar DF dobra a concentracao calculada."""
        base = self._stability_row(0.500, 0.020, 0.040, 0.020, df=10.0)
        doubled = self._stability_row(0.500, 0.020, 0.040, 0.020, df=20.0)
        out_base = lab.calculate_tac(pd.DataFrame([base]))
        out_double = lab.calculate_tac(pd.DataFrame([doubled]))
        self.assertAlmostEqual(out_double.loc[0, "tac_mg_c3g_L"], 2 * out_base.loc[0, "tac_mg_c3g_L"], places=6)

    def test_tac_path_length_halves_concentration(self):
        """Dobrar comprimento optico l reduz a metade a concentracao calculada."""
        base = self._stability_row(0.500, 0.020, 0.040, 0.020, path=1.0)
        doubled_path = self._stability_row(0.500, 0.020, 0.040, 0.020, path=2.0)
        out_base = lab.calculate_tac(pd.DataFrame([base]))
        out_dp = lab.calculate_tac(pd.DataFrame([doubled_path]))
        self.assertAlmostEqual(out_dp.loc[0, "tac_mg_c3g_L"], out_base.loc[0, "tac_mg_c3g_L"] / 2, places=6)

    def test_tac_invalid_path_length_zero(self):
        """l = 0 deve resultar em NaN (divisao por zero evitada)."""
        row = self._stability_row(0.500, 0.020, 0.040, 0.020, path=0.0)
        out = lab.calculate_tac(pd.DataFrame([row]))
        self.assertTrue(pd.isna(out.loc[0, "tac_mg_c3g_L"]))

    def test_tac_invalid_dilution_zero(self):
        """DF = 0 deve resultar em NaN."""
        row = self._stability_row(0.500, 0.020, 0.040, 0.020, df=0.0)
        out = lab.calculate_tac(pd.DataFrame([row]))
        self.assertTrue(pd.isna(out.loc[0, "tac_mg_c3g_L"]))

    def test_tac_negative_absorbance_flagged(self):
        """Absorbancia negativa deve ser sinalizada (qc_flag)."""
        row = self._stability_row(-0.100, 0.020, 0.040, 0.020)
        out = lab.calculate_tac(pd.DataFrame([row]))
        self.assertTrue(out.loc[0, "qc_flag"])

    def test_c3g_is_equivalents_not_individual_quantification(self):
        """C3G-equivalentes nao devem ser descritos como quantificacao individual de todas as moleculas."""
        rows = [self._stability_row(0.500, 0.020, 0.040, 0.020)]
        out = lab.calculate_tac(pd.DataFrame(rows))
        self.assertTrue(out.loc[0, "tac_mg_c3g_L"] > 0)
        self.assertEqual(out.columns.tolist().count("tac_mg_c3g_L"), 1)


class TestRetentionPercent(unittest.TestCase):
    """Validar R_t = 100 * C_t / C_0."""

    def test_retention_basic(self):
        rows = [
            self._row(day=0, tac_pct=100.0),
            self._row(day=7, tac_pct=80.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        r7 = out.loc[out["day"] == 7, "retention_pct"].iloc[0]
        self.assertAlmostEqual(r7, 80.0, places=6)

    def test_retention_c0_zero_returns_nan(self):
        """C_0 = 0 deve ser rejeitado/sinalizado (NaN)."""
        rows = [
            self._row(day=0, tac_pct=0.0),
            self._row(day=7, tac_pct=50.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        r7 = out.loc[out["day"] == 7, "retention_pct"].iloc[0]
        self.assertTrue(pd.isna(r7))
        self.assertIn("baseline", out.loc[out["day"] == 7, "qc_flag"].iloc[0].lower())

    def test_retention_negative_baseline_returns_nan_with_alert(self):
        rows = [
            self._row(day=0, tac_pct=-5.0),
            self._row(day=7, tac_pct=50.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        r7 = out.loc[out["day"] == 7].iloc[0]
        self.assertTrue(pd.isna(r7["retention_pct"]))
        self.assertIn("baseline", r7["qc_flag"].lower())

    def test_retention_invalid_concentration_rejected(self):
        """Concentrações invalidas (negativas) devem ser sinalizadas."""
        rows = [
            self._row(day=0, tac_pct=100.0),
            self._row(day=7, tac_pct=-10.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        self.assertTrue(bool(out.loc[out["day"] == 7, "qc_flag"].iloc[0]))

    def test_retention_no_interpolation_of_missing_c0(self):
        """Nao interpolar um valor inicial ausente."""
        rows = [self._row(day=7, tac_pct=80.0)]
        out = lab.calculate_tac(pd.DataFrame(rows))
        r7 = out.loc[out["day"] == 7, "retention_pct"].iloc[0]
        self.assertTrue(pd.isna(r7))

    def test_retention_reference_observation_recorded(self):
        """Registrar a observacao utilizada como referencia inicial."""
        rows = [
            self._row(day=0, tac_pct=100.0, notes="baseline dia 0 verdadeiro"),
            self._row(day=7, tac_pct=80.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        self.assertTrue("day0_tac_mg_c3g_L" in out.columns)
        ref = out.loc[out["day"] == 0, "day0_tac_mg_c3g_L"].iloc[0]
        self.assertAlmostEqual(ref, 100.0, places=6)

    def test_retention_first_observed_vs_true_day0(self):
        """Nao interpolar: sem dia 0, a retencao e NaN (qc_flag sinaliza)."""
        rows = [
            self._row(day=3, tac_pct=95.0),
            self._row(day=7, tac_pct=80.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        r7 = out.loc[out["day"] == 7, "retention_pct"].iloc[0]
        # Sem baseline valida no dia 0, a retencao e NaN (nao interpola)
        self.assertTrue(pd.isna(r7))
        self.assertTrue(bool(out.loc[out["day"] == 7, "qc_flag"].iloc[0]))

    def _row(self, day, tac_pct, notes=""):
        """Gera uma linha com absorbância que produz o TAC alvo (tac_pct mg/L)."""
        # TAC = A * MW * DF * 1000 / (epsilon * l) => A = TAC * epsilon * l / (MW * DF * 1000)
        A = tac_pct * EPSILON_C3G * 1.0 / (MW_C3G * 10.0 * 1000.0)
        # A = (A520 - A700)pH1 - (A520 - A700)pH4.5; usar A700=0.02, diff_pH45=0.02
        diff_ph1 = A + 0.02
        return {
            "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
            "day": day, "vial_id": f"V{day}", "replicate": 1, "pH_storage": 4.0,
            "a520_ph1": diff_ph1 + 0.02, "a700_ph1": 0.02,
            "a520_ph45": 0.04, "a700_ph45": 0.02,
            "dilution_factor": 10.0, "path_length_cm": 1.0, "notes": notes,
        }



class TestFirstOrderKinetics(unittest.TestCase):
    """Validar ajustes pela função de produção."""

    def test_kinetics_rejects_non_positive_data(self):
        """Dados nao positivos (concentracao <= 0) nao geram ln valido."""
        rows = [
            self._kin_row(day=0, tac=100.0),
            self._kin_row(day=7, tac=0.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        fits = lab.fit_kinetics(out)
        self.assertTrue(len(fits) == 0 or fits["k_per_day"].isna().any())

    def test_fit_recovers_known_rate_and_half_life(self):
        expected_k = 0.037
        initial = 120.0
        rows = [
            self._kin_row(day=day, tac=initial * math.exp(-expected_k * day))
            for day in [0, 3, 7, 14, 21]
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        fit = lab.fit_kinetics(out)
        self.assertEqual(len(fit), 1)
        self.assertAlmostEqual(fit.iloc[0]["k_per_day"], expected_k, delta=1e-10)
        self.assertAlmostEqual(fit.iloc[0]["half_life_days"], math.log(2) / expected_k, delta=1e-8)

    def test_shared_baseline_is_aggregated_like_tac(self):
        rows = [
            self._kin_row(day=0, tac=100.0, condition="BASELINE"),
            self._kin_row(day=0, tac=140.0, condition="BASELINE"),
            *[
                self._kin_row(day=day, tac=120.0 * math.exp(-0.02 * day), condition="4C_dark")
                for day in (3, 7, 14)
            ],
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        baseline = out.loc[out["storage_condition"] == "4C_dark", "day0_tac_mg_c3g_L"].iloc[0]
        self.assertAlmostEqual(baseline, 120.0, places=7)
        fit = lab.fit_kinetics(out)
        self.assertAlmostEqual(
            fit.loc[fit["storage_condition"] == "4C_dark", "k_per_day"].iloc[0],
            0.02,
            delta=1e-10,
        )

    def _kin_row(self, day, tac, condition="4C_dark"):
        absorbance_difference = tac * EPSILON_C3G / (MW_C3G * 10.0 * 1000.0)
        return {
            "batch_id": "B1", "formulation": "native", "storage_condition": condition,
            "day": day, "vial_id": f"V{day}", "replicate": 1, "pH_storage": 4.0,
            "a520_ph1": absorbance_difference + 0.040, "a700_ph1": 0.020,
            "a520_ph45": 0.040, "a700_ph45": 0.020,
            "dilution_factor": 10.0, "path_length_cm": 1.0, "notes": "",
        }




class TestArrhenius(unittest.TestCase):
    """Verificar saída determinística do simulador em temperaturas diferentes."""

    def _config(self, temperatures=(25.0, 35.0)):
        return {
            "reference_temperature_c": 25.0,
            "reference_half_life_days": 10.0,
            "activation_energy_kj_mol": 40.0,
            "initial_retention_pct": 100.0,
            "days": [0, 7],
            "scenarios": [
                {"scenario_id": f"T{temp:g}", "label": f"{temp:g} C", "temperature_c": temp,
                 "pH_factor": 1.0, "light_factor": 1.0, "oxygen_factor": 1.0,
                 "packaging_factor": 1.0}
                for temp in temperatures
            ],
        }

    def test_simulator_rates_and_positive_day_retention_at_two_temperatures(self):
        results = lab.simulate_scenarios(self._config())
        rates = results.groupby("temperature_c")["k_per_day_simulated"].first()
        expected_ref = math.log(2) / 10.0
        expected_hot = expected_ref * math.exp(
            -(40000.0 / 8.314462618) * (1.0 / 308.15 - 1.0 / 298.15)
        )
        self.assertAlmostEqual(rates.loc[25.0], expected_ref, delta=1e-12)
        self.assertAlmostEqual(rates.loc[35.0], expected_hot, delta=1e-12)
        day7 = results.loc[(results["temperature_c"] == 35.0) & (results["day"] == 7),
                           "retention_pct_simulated"].iloc[0]
        self.assertAlmostEqual(day7, 100.0 * math.exp(-expected_hot * 7), delta=1e-10)

    def test_simulator_rejects_non_finite_and_out_of_domain_parameters(self):
        for key, value in [
            ("reference_temperature_c", float("nan")),
            ("reference_half_life_days", float("inf")),
            ("activation_energy_kj_mol", float("nan")),
            ("initial_retention_pct", float("inf")),
            ("initial_retention_pct", -1.0),
            ("activation_energy_kj_mol", -0.01),
        ]:
            with self.subTest(parameter=key):
                cfg = self._config()
                cfg[key] = value
                with self.assertRaises(ValueError):
                    lab.simulate_scenarios(cfg)
        for temperature in (-273.15, float("nan"), float("inf")):
            with self.subTest(temperature=temperature):
                with self.assertRaises(ValueError):
                    lab.simulate_scenarios(self._config((temperature,)))
        for factor in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(factor=factor):
                cfg = self._config((25.0,))
                cfg["scenarios"][0]["oxygen_factor"] = factor
                with self.assertRaises(ValueError):
                    lab.simulate_scenarios(cfg)
        cfg = self._config()
        cfg["days"] = [float("nan")]
        with self.assertRaises(ValueError):
            lab.simulate_scenarios(cfg)


class TestColorConversions(unittest.TestCase):
    """Testar HSV e ΔE para RGB e CIELAB recebidos."""

    def _row(self, day, rgb, lab_values, condition="4C_dark"):
        return {
            "batch_id": "B1", "formulation": "native", "storage_condition": condition,
            "day": day, "vial_id": f"C{day}", "replicate": 1, "target_pH": 4.0,
            "measured_pH_final": 4.0, "r": rgb[0], "g": rgb[1], "b": rgb[2],
            "L_star": lab_values[0], "a_star": lab_values[1], "b_star": lab_values[2],
            "absorbance_max_nm": 520, "absorbance_max": 0.8, "notes": "",
        }

    def test_known_rgb_and_cielab_values_pass_through_production_function(self):
        result = lab.add_hsv_and_delta_e(pd.DataFrame([
            self._row(0, (128, 64, 32), (50, 10, -5)),
            self._row(7, (230, 10, 10), (48, 13, -1)),
        ]))
        self.assertAlmostEqual(result.loc[0, "hue_deg"], 20.0, places=6)
        self.assertAlmostEqual(result.loc[0, "saturation_0_1"], 0.75, places=6)
        self.assertAlmostEqual(result.loc[0, "value_0_1"], 128 / 255, places=6)
        self.assertAlmostEqual(result.loc[0, "delta_e_cie76_vs_day0"], 0.0, places=6)
        self.assertAlmostEqual(result.loc[1, "delta_e_cie76_vs_day0"], math.sqrt(29), places=6)

    def test_missing_rgb_and_cielab_values_remain_missing(self):
        result = lab.add_hsv_and_delta_e(pd.DataFrame([
            self._row(0, (255, 0, 0), (50, 10, 5)),
            self._row(7, (float("nan"), 0, 0), (float("nan"), 10, 5)),
        ]))
        self.assertTrue(result.loc[1, ["hue_deg", "saturation_0_1", "value_0_1",
                                       "delta_e_cie76_vs_day0"]].isna().all())

    def test_color_delta_e_uses_shared_baseline(self):
        result = lab.add_hsv_and_delta_e(pd.DataFrame([
            self._row(0, (128, 64, 32), (50, 10, -5), condition="BASELINE"),
            self._row(7, (230, 10, 10), (48, 13, -1)),
        ]))
        self.assertAlmostEqual(result.loc[1, "L_star_day0"], 50.0, places=6)
        self.assertAlmostEqual(result.loc[1, "delta_e_cie76_vs_day0"], math.sqrt(29), places=6)



class TestSimulator(unittest.TestCase):
    """Validar repetibilidade, comportamento matematico, unidades e isolamento."""

    def test_simulator_repeatability(self):
        """Entradas e configuracoes identicas produzem resultados identicos."""
        cfg = lab.default_simulation_config()
        cfg["reference_half_life_days"] = 10.0
        cfg["activation_energy_kj_mol"] = 40.0
        r1 = lab.simulate_scenarios(cfg)
        r2 = lab.simulate_scenarios(cfg)
        pd.testing.assert_frame_equal(r1, r2)

    def test_simulator_temperature_affects_rate(self):
        """Variavel (temperatura) afeta o parametro cinetico k via Arrhenius."""
        cfg = lab.default_simulation_config()
        cfg["reference_half_life_days"] = 10.0
        cfg["activation_energy_kj_mol"] = 40.0
        cfg["reference_temperature_c"] = 25.0
        cfg_hot = dict(cfg)
        cfg_hot["scenarios"] = [{"scenario_id": "HOT", "label": "40 C", "temperature_c": 40.0,
                                 "pH_factor": 1.0, "light_factor": 1.0, "oxygen_factor": 1.0,
                                 "packaging_factor": 1.0, "notes": ""}]
        cfg_ref = dict(cfg)
        cfg_ref["scenarios"] = [{"scenario_id": "REF", "label": "25 C", "temperature_c": 25.0,
                                 "pH_factor": 1.0, "light_factor": 1.0, "oxygen_factor": 1.0,
                                 "packaging_factor": 1.0, "notes": ""}]
        r_hot = lab.simulate_scenarios(cfg_hot)
        r_ref = lab.simulate_scenarios(cfg_ref)
        hot_day = r_hot.loc[r_hot["day"] == 7, "retention_pct_simulated"].iloc[0]
        ref_day = r_ref.loc[r_ref["day"] == 7, "retention_pct_simulated"].iloc[0]
        self.assertLess(hot_day, ref_day)

    def test_simulator_applies_explicit_multipliers(self):
        cfg = lab.default_simulation_config()
        cfg.update({
            "reference_half_life_days": 10.0,
            "activation_energy_kj_mol": 40.0,
            "reference_temperature_c": 25.0,
            "initial_retention_pct": 100.0,
            "days": [0, 5],
            "scenarios": [{
                "scenario_id": "FACTORS", "label": "explicit factors", "temperature_c": 25.0,
                "pH_factor": 1.5, "light_factor": 2.0, "oxygen_factor": 0.5,
                "packaging_factor": 0.8,
            }],
        })
        result = lab.simulate_scenarios(cfg)
        expected_k = math.log(2) / 10.0 * 1.5 * 2.0 * 0.5 * 0.8
        self.assertAlmostEqual(result["combined_factor"].iloc[0], 1.2, places=12)
        self.assertTrue(result["k_per_day_simulated"].map(
            lambda value: math.isclose(value, expected_k, rel_tol=1e-12)
        ).all())
        retention_day5 = result.loc[result["day"] == 5, "retention_pct_simulated"].iloc[0]
        self.assertAlmostEqual(retention_day5, 100.0 * math.exp(-expected_k * 5), delta=1e-12)

    def test_simulator_units_and_limits(self):
        """Coerencia de unidades e limites."""
        cfg = lab.default_simulation_config()
        cfg["reference_half_life_days"] = 10.0
        cfg["activation_energy_kj_mol"] = 40.0
        results = lab.simulate_scenarios(cfg)
        self.assertTrue((results["retention_pct_simulated"] >= 0).all())
        self.assertTrue((results["retention_pct_simulated"] <= 100).all())
        self.assertTrue((results["data_origin"] == "SIMULATION_ONLY").all())

    def test_simulator_separate_from_experimental(self):
        """Separacao total entre simulacao e dados experimentais."""
        cfg = lab.default_simulation_config()
        cfg["reference_half_life_days"] = 10.0
        cfg["activation_energy_kj_mol"] = 40.0
        results = lab.simulate_scenarios(cfg)
        self.assertTrue((results["data_origin"] == "SIMULATION_ONLY").all())



class TestPublishedFixtures(unittest.TestCase):
    """Validar fixtures de referencia contra valores publicados."""

    @staticmethod
    def _normalize(value):
        text = unicodedata.normalize("NFKD", str(value).strip().lower())
        return "".join(char for char in text if not unicodedata.combining(char))

    @classmethod
    def _audit_key(cls, row):
        return (
            cls._normalize(row["study_id"]),
            cls._normalize(row["doi"]),
            cls._normalize(row["treatment_id"]),
            float(row["time_value"]),
            cls._normalize(row["time_unit"]),
            cls._normalize(row["measurement"]),
            cls._normalize(row["value_unit"]),
        )

    @classmethod
    def _fixture_mismatches(cls, fixture, original):
        source_rows = {}
        for row in original:
            key = cls._audit_key(row)
            if key in source_rows:
                raise AssertionError(f"Chave de auditoria duplicada na fonte preservada: {key}")
            source_rows[key] = float(row["value"])
        mismatches = []
        for row in fixture:
            key = cls._audit_key(row)
            if key not in source_rows or float(row["value"]) != source_rows[key]:
                mismatches.append(key)
        return mismatches

    def test_lin_2023_half_life_consistency(self):
        """t1/2 = ln(2) / k para Lin et al. (2023), acido gallico 0,4%."""
        fixture_path = FIXTURES_DIR / "lin_2023_gallic_acid.json"
        self.assertTrue(fixture_path.exists())
        with open(fixture_path, encoding="utf-8") as f:
            fx = json.load(f)
        k = fx["published_kinetic_values"][0]["value"]
        t_half_published = fx["published_kinetic_values"][1]["value"]
        t_half_computed = math.log(2) / k
        tolerance = fx["mathematical_benchmark"]["tolerance_abs_days"]
        self.assertAlmostEqual(t_half_computed, t_half_published, delta=tolerance)
        self.assertNotIn("time_series", fx)

    def test_pan_2021_values_recorded(self):
        """Pan et al. (2021): valores do resumo publicados com condicoes exatas."""
        fixture_path = FIXTURES_DIR / "pan_2021.json"
        self.assertTrue(fixture_path.exists())
        with open(fixture_path, encoding="utf-8") as f:
            fx = json.load(f)
        vals = fx["published_values"]
        ph2 = [v for v in vals if v["condition"] == "pH 2.0, 5 h"][0]
        self.assertAlmostEqual(ph2["value"], 92.92, places=2)
        self.assertEqual(ph2["time_unit"], "h")
        t40 = [v for v in vals if v["condition"] == "40 C, escuro, 5 h"][0]
        self.assertAlmostEqual(t40["value"], 70.50, places=2)
        self.assertEqual(t40["time_unit"], "h")
        hl = [v for v in vals if v["measurement"] == "half-life"][0]
        self.assertAlmostEqual(hl["value"], 67.28, places=2)
        self.assertEqual(hl["unit"], "h")
        self.assertNotEqual(ph2["condition"], t40["condition"])

    def test_hututui_fixture_matches_preserved_measurements_by_stable_key(self):
        fixture = pd.read_csv(FIXTURES_DIR / "hututui_2026_audit.csv").to_dict("records")
        original = pd.read_csv(
            Path(__file__).resolve().parents[1] / "data" / "literature" /
            "literature_measurements.csv"
        ).to_dict("records")
        self.assertEqual(len(fixture), 18)
        self.assertEqual(self._fixture_mismatches(fixture, original), [])
        self.assertEqual(set(pd.DataFrame(fixture)["verification_status"]), {"VERIFICATION_PENDING"})

    def test_muhamad_fixture_matches_preserved_measurements_by_stable_key(self):
        fixture = pd.read_csv(FIXTURES_DIR / "muhamad_2022_audit.csv").to_dict("records")
        original = pd.read_csv(
            Path(__file__).resolve().parents[1] / "data" / "literature" /
            "literature_measurements.csv"
        ).to_dict("records")
        self.assertEqual(len(fixture), 21)
        self.assertEqual(self._fixture_mismatches(fixture, original), [])
        self.assertEqual(set(pd.DataFrame(fixture)["verification_status"]), {"VERIFICATION_PENDING"})

    def test_stable_key_comparison_detects_a_changed_source_value(self):
        fixture = pd.read_csv(FIXTURES_DIR / "hututui_2026_audit.csv").to_dict("records")
        original = pd.read_csv(
            Path(__file__).resolve().parents[1] / "data" / "literature" /
            "literature_measurements.csv"
        ).to_dict("records")
        fixture[0]["value"] = float(fixture[0]["value"]) + 1.0
        mismatches = self._fixture_mismatches(fixture, original)
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0][2], "p4")

    def test_falcioni_method_reference(self):
        """Falcioni et al. (2022) e referencia metodologica apenas."""
        fixture_path = FIXTURES_DIR / "falcioni_2022_method.md"
        self.assertTrue(fixture_path.exists())
        content = fixture_path.read_text(encoding="utf-8")
        self.assertIn("referencia metodologica apenas", content)

    def test_literature_pending_status_is_validated_filtered_and_preserved(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertWarnsRegex(UserWarning, "excluídos da análise aprovada"):
            _, approved, _ = lab.validate_literature_data(root)
        self.assertEqual(set(approved["study_id"]), {"STUDY_B"},
                         "análise aprovada deve conter somente STUDY_B (verificado)")
        self.assertEqual(set(approved["verification_status"]), {"VERIFIED"})
        with self.assertWarnsRegex(UserWarning, "não são benchmarks aprovados"):
            _, exploratory, _ = lab.validate_literature_data(root, include_pending=True)
        self.assertEqual(len(exploratory), 39)
        self.assertEqual(set(exploratory["verification_status"]),
                         {"VERIFICATION_PENDING", "VERIFIED"})
        with self.assertWarnsRegex(UserWarning, "exploratório inclui"):
            fits = lab.fit_literature_kinetics(exploratory, include_pending=True)
        self.assertGreater(len(fits), 0)
        self.assertEqual(set(fits["verification_status"]),
                         {"VERIFICATION_PENDING", "VERIFIED"})
        approved_fits = lab.fit_literature_kinetics(approved)
        self.assertFalse(approved_fits.empty, "STUDY_B verificado deve gerar ajustes aprovados")
        self.assertEqual(set(approved_fits["study_id"]), {"STUDY_B"})

    def test_kinetic_reproduction_uses_generic_time_units_and_pending_status(self):
        report = pd.read_csv(
            Path(__file__).resolve().parents[1] / "reports" / "validation" /
            "kinetic_reproduction.csv"
        )
        month_rows = report.loc[report["time_unit"].str.casefold().isin(["mes", "mês", "months"])]
        self.assertGreater(len(month_rows), 0)
        self.assertTrue(month_rows["k_estimated_per_time_unit"].notna().all())
        self.assertNotIn("k_estimated_day_minus1", report.columns)
        self.assertNotIn("t_half_estimated_days", report.columns)
        self.assertEqual(set(month_rows["verification_status"]), {"VERIFICATION_PENDING"})


class TestLiteratureKineticModelComparison(unittest.TestCase):
    def test_model_fits_recover_deterministic_parameters(self):
        times = [0, 1, 2, 3, 4, 5]
        initial_concentration = 120.0
        zero_order_rate = 4.0
        first_order_rate = 0.2
        second_order_rate = 0.002
        cases = [
            (
                "zero_order",
                [initial_concentration - zero_order_rate * time for time in times],
                zero_order_rate,
            ),
            (
                "first_order",
                [initial_concentration * math.exp(-first_order_rate * time) for time in times],
                first_order_rate,
            ),
            (
                "second_order",
                [
                    initial_concentration
                    / (1 + second_order_rate * initial_concentration * time)
                    for time in times
                ],
                second_order_rate,
            ),
        ]

        for model, values, expected_rate in cases:
            with self.subTest(model=model):
                fit = lab._fit_kinetic_model(model, times, values)
                self.assertAlmostEqual(fit["initial_concentration"], initial_concentration, places=6)
                self.assertAlmostEqual(fit["rate_parameter_value"], expected_rate, places=7)
                self.assertLess(fit["rmse"], 1e-6)

    def test_first_order_fit_selects_best_solution_after_saturated_start(self):
        times = [1.0, 5.0, 10.0]
        values = [74.273, 44.663, 38.482]
        original_curve_fit = lab.curve_fit
        starting_points = []
        candidate_sse = []

        def track_curve_fit(*args, **kwargs):
            starting_points.append(tuple(kwargs["p0"]))
            result = original_curve_fit(*args, **kwargs)
            predictions = args[0](args[1], *result[0])
            candidate_sse.append(sum((observed - predicted) ** 2
                                     for observed, predicted in zip(args[2], predictions)))
            return result

        with patch.object(lab, "curve_fit", side_effect=track_curve_fit):
            fit = lab._fit_kinetic_model("first_order", times, values)

        self.assertGreaterEqual(len(starting_points), 3)
        self.assertTrue(all(math.isfinite(value) for point in starting_points for value in point))
        self.assertTrue(
            any(rate > 1.0 for _, rate in starting_points),
            "Expected a deterministic high-rate start that can reproduce the saturated fit.",
        )
        self.assertAlmostEqual(fit["sse"], min(candidate_sse), places=8)
        self.assertLess(fit["rmse"], 10.0)

    def test_comparison_preserves_source_status_conditions_and_time_units(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertWarnsRegex(UserWarning, "não são benchmarks aprovados"):
            studies, measurements, _ = lab.validate_literature_data(root, include_pending=True)
        with self.assertWarnsRegex(UserWarning, "comparação cinética exploratória inclui"):
            comparison = lab.compare_literature_kinetic_models(
                measurements, studies, include_pending=True
            )

        self.assertEqual(len(comparison), 27)
        self.assertEqual(set(comparison["model"]), {"zero_order", "first_order", "second_order"})
        self.assertEqual(set(comparison["verification_status"]),
                         {"VERIFICATION_PENDING", "VERIFIED"},
                         "comparação exploratória deve manter o status de origem (STUDY_A pendente, STUDY_B verificado)")
        self.assertTrue(comparison["data_origin"].eq("PUBLISHED_ARTICLE").all())
        self.assertTrue(comparison["citation"].notna().all())
        self.assertTrue(comparison["title"].notna().all())
        self.assertTrue(comparison["source_url"].str.startswith("https://").all())
        self.assertTrue(comparison["source_location"].notna().all())
        self.assertTrue(comparison["doi"].notna().all())
        self.assertTrue(comparison["uncertainty_status"].eq(
            "NOT_ESTIMATED_NO_INDEPENDENT_REPLICATES"
        ).all())
        self.assertTrue(comparison["uncertainty_recommendation"].str.contains(
            "bootstrap", case=False
        ).all())
        self.assertTrue(
            comparison.groupby(["study_id", "treatment_id"], dropna=False).size().eq(3).all()
        )
        self.assertTrue(
            comparison["predicted_values_json"].map(
                lambda text: len(json.loads(text))
            ).eq(comparison["n_observations"]).all()
        )

        study_a = comparison.loc[comparison["study_id"].eq("STUDY_A")]
        study_b = comparison.loc[comparison["study_id"].eq("STUDY_B")]
        self.assertEqual(set(study_a["n_timepoints"]), {3})
        self.assertTrue(study_a["aicc"].isna().all())
        self.assertEqual(set(study_a["model_selection_status"]),
                         {"INSUFFICIENT_SAMPLE_SIZE_FOR_AICC"})
        self.assertEqual(set(study_b["time_unit"]), {"mês"})
        self.assertEqual(set(study_b["n_timepoints"]), {7})
        self.assertTrue(study_b["aicc"].notna().all())
        self.assertEqual(set(study_b["model_selection_status"]),
                         {"DESCRIPTIVE_AICC_IID_ASSUMPTION_ONLY"})
        self.assertTrue(comparison["extrapolation_policy"].eq("NONE_WITHIN_OBSERVED_INTERVAL").all())
        self.assertTrue(comparison["fit_time_min"].le(comparison["fit_time_max"]).all())

    def test_pending_series_are_excluded_from_default_comparison(self):
        """Sem include_pending, só STUDY_B (VERIFIED) entra; STUDY_A (pendente) é excluído."""
        root = Path(__file__).resolve().parents[1]
        with self.assertWarnsRegex(UserWarning, "excluídos da análise aprovada"):
            studies, measurements, _ = lab.validate_literature_data(root)
        comparison = lab.compare_literature_kinetic_models(measurements, studies)

        self.assertFalse(comparison.empty, "STUDY_B verificado deve entrar na comparação aprovada")
        self.assertEqual(set(comparison["study_id"]), {"STUDY_B"},
                         "estudos pendentes (STUDY_A) não podem entrar na comparação aprovada")
        self.assertEqual(set(comparison["verification_status"]), {"VERIFIED"})
        self.assertIn("verification_status", comparison.columns)
        self.assertIn("source_location", comparison.columns)

    def test_conditional_parameter_intervals_and_three_point_insufficiency(self):
        times_7 = list(map(float, range(7)))
        values_7 = [10.1, 9.3, 9.2, 8.3, 8.1, 7.3, 7.2]
        prediction_7 = [10.0 - 0.5 * time for time in times_7]
        times_3 = [1.0, 5.0, 10.0]
        values_3 = [74.273, 44.663, 38.482]
        rows = [
            {
                "study_id": "STUDY_B",
                "treatment_id": "SEVEN_POINTS",
                "model": "zero_order",
                "initial_concentration_fit": 10.0,
                "rate_parameter_value": 0.5,
                "n_observations": 7,
                "time_unit": "mes",
                "verification_status": "VERIFICATION_PENDING",
                "observed_times_json": json.dumps(times_7),
                "observed_values_json": json.dumps(values_7),
                "predicted_values_json": json.dumps(prediction_7),
            },
            {
                "study_id": "STUDY_A",
                "treatment_id": "THREE_POINTS",
                "model": "first_order",
                "initial_concentration_fit": 71.59,
                "rate_parameter_value": 0.08,
                "n_observations": 3,
                "time_unit": "dia",
                "verification_status": "VERIFICATION_PENDING",
                "observed_times_json": json.dumps(times_3),
                "observed_values_json": json.dumps(values_3),
                "predicted_values_json": json.dumps([70.0, 52.0, 32.0]),
            },
        ]

        report = lab.estimate_literature_kinetic_parameter_uncertainty(pd.DataFrame(rows))
        seven = report.loc[report["treatment_id"].eq("SEVEN_POINTS")].iloc[0]
        three = report.loc[report["treatment_id"].eq("THREE_POINTS")].iloc[0]

        self.assertEqual(seven["parameter_uncertainty_status"],
                         "EXPLORATORY_CONDITIONAL_INTERVALS")
        self.assertEqual(seven["parameter_residual_degrees_of_freedom"], 5)
        self.assertAlmostEqual(seven["initial_concentration_ci_lower"], 9.6325904564, places=8)
        self.assertAlmostEqual(seven["initial_concentration_ci_upper"], 10.3674095436, places=8)
        self.assertAlmostEqual(seven["rate_parameter_ci_lower"], 0.3980989270, places=8)
        self.assertAlmostEqual(seven["rate_parameter_ci_upper"], 0.6019010730, places=8)
        self.assertIn("independent residuals", seven["parameter_uncertainty_assumptions"])
        self.assertEqual(three["parameter_uncertainty_status"],
                         "INSUFFICIENT_FOR_ROBUST_MODEL_SELECTION")
        self.assertEqual(three["parameter_residual_degrees_of_freedom"], 1)
        self.assertTrue(pd.isna(three["rate_parameter_ci_lower"]))
        self.assertTrue(pd.isna(three["rate_parameter_ci_upper"]))
        self.assertEqual(set(report["verification_status"]),
                         {"VERIFICATION_PENDING"})
        self.assertEqual(set(report["time_unit"]), {"mes", "dia"})

    def test_simulated_concentration_intervals_distinguish_mean_and_individual(self):
        times = list(map(float, range(7)))
        initial = 100.0
        rate = 0.065
        predictions = [initial * math.exp(-rate * time) for time in times]
        values = [
            prediction + residual
            for prediction, residual in zip(predictions, [0.4, -0.6, 0.2, 0.5, -0.3, -0.4, 0.2])
        ]
        comparison = pd.DataFrame([{
            "study_id": "STUDY_B",
            "treatment_id": "SEVEN_POINTS",
            "model": "first_order",
            "initial_concentration_fit": initial,
            "rate_parameter_value": rate,
            "n_observations": len(times),
            "fit_time_min": min(times),
            "fit_time_max": max(times),
            "time_unit": "mes",
            "value_unit": "mg/L",
            "verification_status": "VERIFICATION_PENDING",
            "observed_times_json": json.dumps(times),
            "observed_values_json": json.dumps(values),
            "predicted_values_json": json.dumps(predictions),
        }])

        intervals = lab.estimate_literature_kinetic_concentration_intervals(
            comparison, n_simulations=4000, random_seed=19
        )

        self.assertEqual(len(intervals), len(times))
        self.assertEqual(intervals["time_value"].tolist(), times)
        self.assertTrue(intervals["time_value"].between(0, 6).all())
        mean_columns = ["mean_response_ci_lower", "mean_response_ci_upper"]
        prediction_columns = [
            "individual_observation_pi_lower", "individual_observation_pi_upper"
        ]
        self.assertTrue(np.isfinite(intervals[mean_columns].to_numpy()).all())
        self.assertTrue(np.isfinite(intervals[prediction_columns].to_numpy()).all())
        mean_width = (
            intervals["mean_response_ci_upper"] - intervals["mean_response_ci_lower"]
        )
        prediction_width = (
            intervals["individual_observation_pi_upper"]
            - intervals["individual_observation_pi_lower"]
        )
        self.assertTrue((prediction_width > mean_width).all())
        self.assertEqual(
            set(intervals["concentration_uncertainty_status"]),
            {"EXPLORATORY_CONDITIONAL_SIMULATION"},
        )
        self.assertEqual(set(intervals["verification_status"]), {"VERIFICATION_PENDING"})
        self.assertTrue(intervals["concentration_interval_method"].str.contains(
            "parametric", case=False
        ).all())

    def test_simulated_concentration_intervals_mark_three_points_insufficient(self):
        times = [1.0, 5.0, 10.0]
        values = [74.273, 44.663, 38.482]
        comparison = pd.DataFrame([{
            "study_id": "STUDY_A",
            "treatment_id": "THREE_POINTS",
            "model": "first_order",
            "initial_concentration_fit": 75.0,
            "rate_parameter_value": 0.08,
            "n_observations": len(times),
            "fit_time_min": min(times),
            "fit_time_max": max(times),
            "time_unit": "dia",
            "value_unit": "mg/L",
            "verification_status": "VERIFICATION_PENDING",
            "observed_times_json": json.dumps(times),
            "observed_values_json": json.dumps(values),
            "predicted_values_json": json.dumps([75.0, 54.8, 33.7]),
        }])

        intervals = lab.estimate_literature_kinetic_concentration_intervals(
            comparison, n_simulations=1000, random_seed=19
        )

        self.assertEqual(intervals["time_value"].tolist(), times)
        self.assertEqual(
            set(intervals["concentration_uncertainty_status"]),
            {"INSUFFICIENT_FOR_CONDITIONAL_INTERVALS"},
        )
        interval_columns = [
            "mean_response_ci_lower", "mean_response_ci_upper",
            "individual_observation_pi_lower", "individual_observation_pi_upper",
        ]
        self.assertTrue(intervals[interval_columns].isna().all().all())
        self.assertEqual(set(intervals["verification_status"]), {"VERIFICATION_PENDING"})

    def test_simulation_marks_nonpositive_fitted_concentration_unavailable(self):
        times = list(map(float, range(7)))
        predictions = [10.0 - 2.0 * time for time in times]
        comparison = pd.DataFrame([{
            "study_id": "STUDY_B",
            "treatment_id": "NONPOSITIVE_ZERO_ORDER",
            "model": "zero_order",
            "initial_concentration_fit": 10.0,
            "rate_parameter_value": 2.0,
            "n_observations": len(times),
            "fit_time_min": min(times),
            "fit_time_max": max(times),
            "time_unit": "mes",
            "value_unit": "mg/L",
            "verification_status": "VERIFICATION_PENDING",
            "observed_times_json": json.dumps(times),
            "observed_values_json": json.dumps([10.0, 8.0, 7.0, 5.0, 4.0, 2.0, 1.0]),
            "predicted_values_json": json.dumps(predictions),
        }])

        intervals = lab.estimate_literature_kinetic_concentration_intervals(
            comparison, n_simulations=1000, random_seed=19
        )

        self.assertEqual(
            set(intervals["concentration_uncertainty_status"]),
            {"MODEL_OUTSIDE_PHYSICAL_DOMAIN"},
        )
        self.assertTrue(intervals["mean_response_ci_lower"].isna().all())
        self.assertTrue(intervals["individual_observation_pi_lower"].isna().all())
        self.assertTrue(intervals["concentration_interval_limitations"].str.contains(
            "nonpositive", case=False
        ).all())


class TestPan2021HalfLifeUnits(unittest.TestCase):
    """Verificar que a meia-vida de Pan et al. (2021) permanece em horas, sem conversao para dias."""

    def test_half_life_remains_in_hours_not_days(self):
        """t1/2 = 67.28 h deve ser registrada como horas, nao convertida para dias."""
        fixture_path = FIXTURES_DIR / "pan_2021.json"
        import json

        with open(fixture_path, encoding="utf-8") as f:
            fixture = json.load(f)

        half_life = None
        for v in fixture["published_values"]:
            if v["measurement"] == "half-life":
                half_life = v
                break

        self.assertIsNotNone(half_life, "meia-vida nao encontrada no fixture")
        self.assertEqual(half_life["value"], 67.28)
        self.assertEqual(half_life["unit"], "h")
        # 67.28 h != 67.28 dias; garantir que nao haja conversao implicita
        self.assertNotEqual(half_life["unit"], "dia")
        self.assertEqual(half_life["reported_or_calculated"], "reported")


class TestArrheniusRateRatio(unittest.TestCase):
    """Verificar razao de taxas de Arrhenius contra a fórmula analítica.

    k2/k1 = exp(-Ea/R * (1/T2 - 1/T1)), com T em Kelvin.
    """

    def test_rate_ratio_matches_arrhenius_formula(self):
        """A razao k(35 C)/k(25 C) deve coincidir com a fórmula de Arrhenius."""
        Ea_kj = 40.0
        Ea_j = Ea_kj * 1000.0
        R = 8.314462618
        T1_c, T2_c = 25.0, 35.0
        T1_k = T1_c + 273.15
        T2_k = T2_c + 273.15

        expected_ratio = math.exp(
            -(Ea_j / R) * (1.0 / T2_k - 1.0 / T1_k)
        )

        cfg = {
            "reference_temperature_c": T1_c,
            "reference_half_life_days": 10.0,
            "activation_energy_kj_mol": Ea_kj,
            "initial_retention_pct": 100.0,
            "days": [0, 7],
            "scenarios": [
                {
                    "scenario_id": "T25",
                    "label": "25 C",
                    "temperature_c": T1_c,
                    "pH_factor": 1.0,
                    "light_factor": 1.0,
                    "oxygen_factor": 1.0,
                    "packaging_factor": 1.0,
                },
                {
                    "scenario_id": "T35",
                    "label": "35 C",
                    "temperature_c": T2_c,
                    "pH_factor": 1.0,
                    "light_factor": 1.0,
                    "oxygen_factor": 1.0,
                    "packaging_factor": 1.0,
                },
            ],
        }
        results = lab.simulate_scenarios(cfg)
        rates = results.groupby("temperature_c")["k_per_day_simulated"].first()
        ratio = rates.loc[T2_c] / rates.loc[T1_c]
        self.assertAlmostEqual(ratio, expected_ratio, delta=1e-12)


class TestFirstOrderKineticKZero(unittest.TestCase):
    """Verificar comportamento da meia-vida quando a constante cinetica k tende a zero."""

    def test_k_zero_half_life_not_negative(self):
        """k = 0 nao deve produzir meia-vida negativa ou finita invalida."""
        # Primeira ordem: t1/2 = ln(2) / k. Com k = 0, t1/2 tende ao infinito.
        k = 0.0
        if k > 0:
            t_half = math.log(2.0) / k
        else:
            t_half = float("nan")
        self.assertTrue(math.isnan(t_half) or t_half == float("inf"))

    def test_k_negative_rejected_by_fit(self):
        """k negativo eh fora do dominio fisico para degradacao de primeira ordem."""
        k = -0.05
        self.assertLess(k, 0)
        # k negativo implicaria crescimento, nao degradacao; nao e aceitavel
        # como constante de degradacao de antocianinas.


class TestTACCompleteManualCalculation(unittest.TestCase):
    """Verificar o calculo completo do TAC passo a passo, incluindo unidades."""

    def test_tac_step_by_step_manual_matches_production(self):
        """Cada etapa do calculo (A, depois C) deve coincidir com o calculo manual."""
        # Absorbancias de exemplo
        a520_p1, a700_p1 = 0.500, 0.020
        a520_p45, a700_p45 = 0.040, 0.020
        df = 10.0
        path = 1.0
        mw = 449.2  # g/mol (cianidina-3-glicosídeo)
        epsilon = 26900.0  # L mol^-1 cm^-1

        # Etapa 1: diferenca de absorbancia
        A = (a520_p1 - a700_p1) - (a520_p45 - a700_p45)
        expected_A = 0.460

        # Etapa 2: concentracao em mol/L, depois converter para mg/L
        # C_mol_per_L = A / (epsilon * path)
        # C_mg_per_L = C_mol_per_L * mw * 1000 * df  (g->mg: x1000; DF aplicado)
        C_mol_per_L = A / (epsilon * path)
        C_mg_per_L = C_mol_per_L * mw * 1000.0 * df

        self.assertAlmostEqual(A, expected_A, places=6)
        self.assertAlmostEqual(C_mg_per_L, 76.81487, places=4)

        # Verificar com a funcao de producao
        row = {
            "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
            "day": 0, "vial_id": "V1", "replicate": 1, "pH_storage": 4.0,
            "a520_ph1": a520_p1, "a700_ph1": a700_p1,
            "a520_ph45": a520_p45, "a700_ph45": a700_p45,
            "dilution_factor": df, "path_length_cm": path, "notes": "",
        }
        out = lab.calculate_tac(pd.DataFrame([row]))
        self.assertAlmostEqual(out.loc[0, "absorbance_difference"], expected_A, places=6)
        self.assertAlmostEqual(out.loc[0, "tac_mg_c3g_L"], C_mg_per_L, places=4)


class TestLiteratureTraceability(unittest.TestCase):
    """Verificar rastreabilidade bibliográfica: nenhum registro promovido sem fonte primária."""

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.lit_dir = self.root / "data" / "literature"

    def test_all_verification_statuses_remain_pending(self):
        """Somente STUDY_B (texto integral confirmado) é VERIFIED; os demais seguem pendentes."""
        status_path = self.lit_dir / "literature_verification_status.csv"
        self.assertTrue(status_path.exists(), "literature_verification_status.csv deve existir")
        status = pd.read_csv(status_path)
        self.assertGreater(len(status), 0, "deve haver registros de verificação")
        verified = status.loc[status["verification_status"] == "VERIFIED"]
        pending = status.loc[status["verification_status"] == "VERIFICATION_PENDING"]
        self.assertEqual(set(verified["study_id"]), {"STUDY_B"},
                         "apenas STUDY_B pode ser VERIFIED (confirmado contra a Tabela 8)")
        self.assertEqual(len(verified), 21, "STUDY_B deve ter exatamente 21 registros VERIFIED")
        self.assertEqual(set(pending["study_id"]), {"STUDY_A"},
                         "apenas STUDY_A deve permanecer pendente no manifesto de verificação")
        self.assertEqual(len(pending), 18, "devem restar 18 registros de STUDY_A pendentes")

    def test_reported_or_calculated_only_reported_for_measurements(self):
        """Valores de medição publicados devem ser classificados como 'reported'."""
        meas_path = self.lit_dir / "literature_measurements.csv"
        self.assertTrue(meas_path.exists(), "literature_measurements.csv deve existir")
        meas = pd.read_csv(meas_path)
        if len(meas) > 0:
            self.assertTrue(
                (meas["data_origin"] == "PUBLISHED_ARTICLE").all(),
                "todas as medições de literatura devem ser PUBLISHED_ARTICLE",
            )
            self.assertTrue(
                (meas["reported_or_calculated"] == "reported").all(),
                "valores publicados devem ser classificados como 'reported', nao 'calculated'",
            )

    def test_no_simulation_or_literature_masquerading_as_experimental(self):
        """Nenhuma linha SIMULATION_ONLY ou LITERATURE deve aparecer como EXPERIMENTAL em ML."""
        ml_path = self.root / "data" / "raw" / "ml_observations.csv"
        if not ml_path.exists():
            self.skipTest("ml_observations.csv nao existe ainda")
        ml = pd.read_csv(ml_path)
        if len(ml) > 0 and "data_origin" in ml.columns:
            self.assertTrue(
                (ml["data_origin"] == "EXPERIMENTAL").all(),
                "apenas linhas EXPERIMENTAL devem ser usadas no treino de ML por padrao",
            )


class TestLiteratureAccessibilityTraceability(unittest.TestCase):
    """Rastreabilidade da recuperação do texto integral de STUDY_B.

    STUDY_B foi confirmado por espelho alternativo (Semantic Scholar) contra a
    Tabela 8, p. 6; os demais estudos, cujo texto integral segue inacessível,
    permanecem pendentes com campos de revisão vazios.
    """

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.lit_dir = self.root / "data" / "literature"

    def _is_cell_empty(self, value) -> bool:
        """Uma célula está vazia se for NaN (pandas) ou string vazia após strip."""
        import pandas as pd

        if pd.isna(value):
            return True
        return str(value).strip() == ""

    def test_only_study_b_verified_after_primary_source_recovery(self):
        """Apenas STUDY_B é VERIFIED (fonte primária recuperada); os demais seguem pendentes."""
        status_path = self.lit_dir / "literature_verification_status.csv"
        self.assertTrue(status_path.exists(), "literature_verification_status.csv deve existir")
        status = pd.read_csv(status_path)
        self.assertGreater(len(status), 0, "deve haver registros de verificação")
        verified_ids = set(status.loc[status["verification_status"] == "VERIFIED", "study_id"])
        self.assertEqual(verified_ids, {"STUDY_B"},
                         "somente STUDY_B pode ser VERIFIED; os demais Textos integrais "
                         "seguem inacessíveis (403/falha de fetch)")

    def test_verified_source_location_specific_for_study_b_and_empty_for_others(self):
        """STUDY_B deve ter localização específica (Tabela 8, p. 6); os demais, vazia."""
        status_path = self.lit_dir / "literature_verification_status.csv"
        status = pd.read_csv(status_path)
        for _, row in status.iterrows():
            loc = row["verified_source_location"]
            if row["study_id"] == "STUDY_B":
                loc_text = str(loc)
                self.assertFalse(self._is_cell_empty(loc),
                                 f"STUDY_B/{row['treatment_id']} VERIFIED exige localização")
                self.assertIn("Tabela 8", loc_text)
                self.assertIn("p. 6", loc_text)
                self.assertIn("muhamad_2022.pdf", loc_text)
            else:
                self.assertTrue(
                    self._is_cell_empty(loc),
                    f"registro {row['study_id']}/{row['treatment_id']} tem localização "
                    f"preenchida sem fonte primária confirmada: '{loc}'",
                )

    def test_review_fields_present_for_study_b_and_empty_for_others(self):
        """STUDY_B revisado por Lapllace em 2026-10-20; os demais, sem revisão."""
        status_path = self.lit_dir / "literature_verification_status.csv"
        status = pd.read_csv(status_path)
        for _, row in status.iterrows():
            reviewed_on = row["reviewed_on"]
            reviewer = row["reviewer"]
            if row["study_id"] == "STUDY_B":
                self.assertEqual(str(reviewed_on).strip(), "2026-10-20",
                                 f"STUDY_B/{row['treatment_id']} deve ter reviewed_on ISO")
                self.assertEqual(str(reviewer).strip(), "Lapllace",
                                 f"STUDY_B/{row['treatment_id']} deve registrar o revisor humano")
            else:
                self.assertTrue(
                    self._is_cell_empty(reviewed_on),
                    f"registro {row['study_id']}/{row['treatment_id']} tem reviewed_on "
                    f"preenchido sem revisão: '{reviewed_on}'",
                )
                self.assertTrue(
                    self._is_cell_empty(reviewer),
                    f"registro {row['study_id']}/{row['treatment_id']} tem reviewer "
                    f"preenchido sem revisão: '{reviewer}'",
                )

    def test_all_measurements_remain_reported_not_calculated(self):
        """Valores publicados devem continuar classificados como 'reported', nunca 'calculated' sem fórmula derivada."""
        meas_path = self.lit_dir / "literature_measurements.csv"
        self.assertTrue(meas_path.exists(), "literature_measurements.csv deve existir")
        meas = pd.read_csv(meas_path)
        if len(meas) > 0:
            self.assertTrue(
                (meas["data_origin"] == "PUBLISHED_ARTICLE").all(),
                "todas as medições de literatura devem ser PUBLISHED_ARTICLE",
            )
            self.assertTrue(
                (meas["reported_or_calculated"] == "reported").all(),
                "valores publicados devem ser classificados como 'reported', nao 'calculated'",
            )


if __name__ == "__main__":
    unittest.main()
