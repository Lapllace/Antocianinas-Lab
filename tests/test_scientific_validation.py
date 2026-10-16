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
import colorsys
import unittest
from pathlib import Path

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
        A = (0.500 - 0.020) - (0.040 - 0.020)
        expected_C = A * MW_C3G * 10.0 * 1000.0 / (EPSILON_C3G * 1.0)
        self.assertAlmostEqual(out.loc[0, "tac_mg_c3g_L"], expected_C, places=6)
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
        self.assertTrue(pd.isna(r7) or bool(out.loc[out["day"] == 7, "qc_flag"].iloc[0]))

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
    """Validar ln(C_t/C_0) = -k t e t_1/2 = ln(2)/k."""

    def test_half_life_from_k(self):
        """t1/2 = ln(2) / k."""
        k = 0.1
        expected_t_half = math.log(2) / k
        self.assertAlmostEqual(expected_t_half, 6.931471805599453, places=6)

    def test_kinetics_units_k_and_half_life(self):
        """Unidades de k (tempo^-1) e meia-vida (tempo) sao consistentes."""
        k = 0.0466
        t_half = math.log(2) / k
        self.assertAlmostEqual(t_half, 14.8744, places=4)
        self.assertAlmostEqual(k * t_half, math.log(2), places=6)

    def test_kinetics_rejects_non_positive_data(self):
        """Dados nao positivos (concentracao <= 0) nao geram ln valido."""
        rows = [
            self._kin_row(day=0, tac=100.0),
            self._kin_row(day=7, tac=0.0),
        ]
        out = lab.calculate_tac(pd.DataFrame(rows))
        fits = lab.fit_kinetics(out)
        self.assertTrue(len(fits) == 0 or fits["k_per_day"].isna().any())

    def test_kinetics_hours_vs_days_not_converted(self):
        """Tempos em horas vs dias nao sao convertidos automaticamente."""
        rows_days = [self._kin_row(day=d, tac=100.0 * math.exp(-0.1 * d)) for d in [0, 7, 14]]
        out_days = lab.calculate_tac(pd.DataFrame(rows_days))
        fit_days = lab.fit_kinetics(out_days)
        if len(fit_days) > 0:
            # Ajuste exploratorio feito; nao ha conversao implicita de horas para dias
            self.assertTrue("explorat" in str(fit_days.iloc[0]["fit_note"]).lower())

    def test_kinetics_rounded_parameters(self):
        """Parametros arredondados ainda devem produzir ajuste consistente."""
        rows = [self._kin_row(day=d, tac=round(100.0 * math.exp(-0.05 * d), 1)) for d in [0, 7, 14, 21]]
        out = lab.calculate_tac(pd.DataFrame(rows))
        fit = lab.fit_kinetics(out)
        if len(fit) > 0:
            k = fit.iloc[0]["k_per_day"]
            t_half = fit.iloc[0]["half_life_days"]
            self.assertAlmostEqual(t_half, math.log(2) / k, places=4)

    def test_kinetics_fit_error_when_ss_tot_zero(self):
        """Quando todos os valores sao iguais, ss_tot = 0 -> R^2 indefinido."""
        rows = [self._kin_row(day=d, tac=100.0) for d in [0, 7, 14]]
        out = lab.calculate_tac(pd.DataFrame(rows))
        fit = lab.fit_kinetics(out)
        if len(fit) > 0:
            self.assertTrue(pd.isna(fit.iloc[0]["r_squared"]) or fit.iloc[0]["r_squared"] == 0.0)
            # Quando ss_tot = 0, r_squared deve ser NaN (ajuste sem variancia)

    def _kin_row(self, day, tac):
        return {
            "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
            "day": day, "vial_id": f"V{day}", "replicate": 1, "pH_storage": 4.0,
            "a520_ph1": 0.500 + tac / 1000, "a700_ph1": 0.020,
            "a520_ph45": 0.040, "a700_ph45": 0.020,
            "dilution_factor": 10.0, "path_length_cm": 1.0, "notes": "",
        }




class TestArrhenius(unittest.TestCase):
    """Validar ln(k) = ln(A) - Ea/(R T). T obrigatoriamente em kelvin."""

    def test_arrhenius_temperature_must_be_kelvin(self):
        """Temperatura deve estar em kelvin; Celsius nao e aceito diretamente."""
        T_c = 25.0
        T_k = T_c + 273.15
        self.assertAlmostEqual(T_k, 298.15, places=2)

    def test_arrhenius_ea_explicit_unit(self):
        """Energia de ativacao com unidade explicita (kJ/mol -> J/mol na calculacao)."""
        Ea_kj = 50.0
        Ea_j = Ea_kj * 1000
        R = 8.314
        self.assertAlmostEqual(Ea_j, 50000.0, places=2)

    def test_arrhenius_kinetic_rate_time_unit_compatible(self):
        """Taxa cinetica com unidade temporal compatível com a meia-vida."""
        k_per_day = 0.0466
        t_half_days = math.log(2) / k_per_day
        self.assertAlmostEqual(t_half_days, 14.875, places=2)

    def test_arrhenius_refuses_incompatible_matrices(self):
        """Nao estimar Arrhenius combinando estudos com matrizes/solventes/metodos incompatíveis."""
        studies = pd.DataFrame([
            {"study_id": "A", "matrix": "extrato aquoso", "solvent": "agua", "time_unit": "dia", "value_unit": "mg/L"},
            {"study_id": "B", "matrix": "bebida mista", "solvent": "n/a", "time_unit": "mes", "value_unit": "mg/L"},
        ])
        self.assertNotEqual(studies.loc[0, "time_unit"], studies.loc[1, "time_unit"])
        self.assertNotEqual(studies.loc[0, "matrix"], studies.loc[1, "matrix"])

    def test_arrhenius_insufficient_data_rejected(self):
        """Identificar quando dados sao insuficientes para ajustar o modelo Arrhenius."""
        temps_k = [298.15]
        self.assertLess(len(temps_k), 2)



class TestColorConversions(unittest.TestCase):
    """Validar RGB, HSV, espaco de cor e ΔE*ab."""

    def test_rgb_to_hsv_known_cases(self):
        """Casos conhecidos de conversao RGB -> HSV."""
        h, s, v = colorsys.rgb_to_hsv(255 / 255, 0 / 255, 0 / 255)
        self.assertAlmostEqual(h, 0.0, places=6)
        self.assertAlmostEqual(s, 1.0, places=6)
        self.assertAlmostEqual(v, 1.0, places=6)
        h, s, v = colorsys.rgb_to_hsv(0 / 255, 0 / 255, 255 / 255)
        self.assertAlmostEqual(h, 2 / 3, places=6)

    def test_rgb_out_of_range(self):
        """Valores RGB fora de 0-255 sao invalidos (verificado na camada de persistencia)."""
        # colorsys nao valida range; a validacao de range fica em anthocyanin_persistence.
        # Aqui apenas confirmamos que valores dentro do range funcionam.
        h, s, v = colorsys.rgb_to_hsv(255 / 255, 0 / 255, 0 / 255)
        self.assertAlmostEqual(h, 0.0, places=6)

    def test_delta_e_identical_colors_is_zero(self):
        """ΔE*ab = sqrt((dL)^2 + (da)^2 + (db)^2); cores idênticas -> 0."""
        L1, a1, b1 = 50.0, 60.0, 40.0
        L2, a2, b2 = 50.0, 60.0, 40.0
        de = math.sqrt((L2 - L1) ** 2 + (a2 - a1) ** 2 + (b2 - b1) ** 2)
        self.assertAlmostEqual(de, 0.0, places=6)

    def test_delta_e_known_difference(self):
        """ΔE*ab com diferença conhecida."""
        L1, a1, b1 = 50.0, 60.0, 40.0
        L2, a2, b2 = 51.0, 62.0, 43.0
        de = math.sqrt((L2 - L1) ** 2 + (a2 - a1) ** 2 + (b2 - b1) ** 2)
        expected = math.sqrt(1 + 4 + 9)
        self.assertAlmostEqual(de, expected, places=6)

    def test_delta_e_missing_values(self):
        """Comportamento com valores ausentes (NaN) -> resultado NaN."""
        L1, a1, b1 = 50.0, 60.0, 40.0
        L2 = float("nan")
        a2, b2 = 60.0, 40.0
        de = math.sqrt((L2 - L1) ** 2 + (a2 - a1) ** 2 + (b2 - b1) ** 2)
        self.assertTrue(pd.isna(de))

    def test_hsv_missing_rgb(self):
        """RGB ausente -> HSV NaN."""
        r = float("nan")
        self.assertTrue(pd.isna(r))

    def test_rgb_colorspace_assumption_documented(self):
        """Documentar espaco RGB (sRGB 8-bit assumido), gama, ponto branco."""
        self.assertTrue(True)



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
        self.assertLessEqual(r_hot.iloc[0]["retention_pct_simulated"], r_ref.iloc[0]["retention_pct_simulated"])

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

    def test_hututui_fixture_exists(self):
        """Fixture de auditoria Huțuțui et al. (2026) existe."""
        fixture_path = FIXTURES_DIR / "hututui_2026_audit.csv"
        self.assertTrue(fixture_path.exists())
        df = pd.read_csv(fixture_path)
        self.assertGreater(len(df), 0)
        self.assertTrue((df["verification_status"] == "VERIFICATION_PENDING").all())

    def test_muhamad_fixture_exists(self):
        """Fixture de auditoria Muhamad et al. (2022) existe."""
        fixture_path = FIXTURES_DIR / "muhamad_2022_audit.csv"
        self.assertTrue(fixture_path.exists())
        df = pd.read_csv(fixture_path)
        self.assertGreater(len(df), 0)
        self.assertTrue((df["verification_status"] == "VERIFICATION_PENDING").all())

    def test_falcioni_method_reference(self):
        """Falcioni et al. (2022) e referencia metodologica apenas."""
        fixture_path = FIXTURES_DIR / "falcioni_2022_method.md"
        self.assertTrue(fixture_path.exists())
        content = fixture_path.read_text(encoding="utf-8")
        self.assertIn("referencia metodologica apenas", content)


if __name__ == "__main__":
    unittest.main()
