import importlib.util
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "anthocyanin_lab.py"
spec = importlib.util.spec_from_file_location("anthocyanin_lab", MODULE_PATH)
lab = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(lab)


class TestAnalysis(unittest.TestCase):
    def test_tac_and_retention(self):
        rows = []
        for day, a in [(0, 0.50), (7, 0.40), (14, 0.32)]:
            rows.append({
                "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
                "day": day, "vial_id": f"V{day}", "replicate": 1, "pH_storage": 4.0,
                "a520_ph1": a + 0.02, "a700_ph1": 0.02,
                "a520_ph45": 0.04, "a700_ph45": 0.02,
                "dilution_factor": 10, "path_length_cm": 1, "notes": ""
            })
        out = lab.calculate_tac(pd.DataFrame(rows))
        self.assertGreater(out.loc[0, "tac_mg_c3g_L"], 0)
        self.assertAlmostEqual(out.loc[0, "retention_pct"], 100.0, places=5)
        self.assertLess(out.loc[1, "retention_pct"], 100.0)

    def test_shared_baseline_without_extra_storage_vials(self):
        rows = []
        for formulation, offset in [("native", 0.0), ("pH3", 0.1)]:
            # A single measured day-0 sample per batch/formulation, before
            # allocation to storage conditions.
            rows.append({
                "batch_id": "B1", "formulation": formulation, "storage_condition": "BASELINE",
                "day": 0, "vial_id": f"BASE-{formulation}", "replicate": 1, "pH_storage": 4.0,
                "a520_ph1": 0.52 + offset, "a700_ph1": 0.02,
                "a520_ph45": 0.04, "a700_ph45": 0.02,
                "dilution_factor": 10, "path_length_cm": 1, "notes": "baseline compartilhado"
            })
            for condition, values in [("4C_dark", [(3, 0.45), (7, 0.40), (14, 0.30)]),
                                      ("25C_dark", [(3, 0.42), (7, 0.35), (14, 0.25)])]:
                for day, a in values:
                    rows.append({
                        "batch_id": "B1", "formulation": formulation, "storage_condition": condition,
                        "day": day, "vial_id": f"{formulation}-{condition}-{day}", "replicate": 1,
                        "pH_storage": 4.0, "a520_ph1": a + offset, "a700_ph1": 0.02,
                        "a520_ph45": 0.04, "a700_ph45": 0.02,
                        "dilution_factor": 10, "path_length_cm": 1, "notes": ""
                    })
        out = lab.calculate_tac(pd.DataFrame(rows))
        stored = out.loc[out["day"] > 0]
        self.assertTrue(stored["day0_tac_mg_c3g_L"].notna().all())
        self.assertTrue(stored["retention_pct"].notna().all())
        fits = lab.fit_kinetics(out)
        self.assertTrue((fits.loc[fits["storage_condition"].isin(["4C_dark", "25C_dark"]), "n_timepoints"] >= 4).all())

    def test_hsv_conversion_and_delta_e(self):
        rows = []
        for day, rgb, lab_values in [
            (0, (255, 0, 0), (50, 60, 40)),
            (7, (230, 10, 10), (48, 55, 38)),
        ]:
            rows.append({
                "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
                "day": day, "vial_id": f"C{day}", "replicate": 1, "target_pH": 4,
                "measured_pH_final": 4.0, "r": rgb[0], "g": rgb[1], "b": rgb[2],
                "L_star": lab_values[0], "a_star": lab_values[1], "b_star": lab_values[2],
                "absorbance_max_nm": 520, "absorbance_max": 0.8, "notes": ""
            })
        out = lab.add_hsv_and_delta_e(pd.DataFrame(rows))
        self.assertAlmostEqual(out.loc[0, "hue_deg"], 0.0, places=5)
        self.assertAlmostEqual(out.loc[0, "saturation_0_1"], 1.0, places=5)
        self.assertAlmostEqual(out.loc[0, "delta_e_cie76_vs_day0"], 0.0, places=5)
        self.assertGreater(out.loc[1, "delta_e_cie76_vs_day0"], 0.0)

    def test_srgb_to_cielab_reference_values(self):
        # Branco sRGB: L* = 100, a* ~ 0, b* ~ 0 sob D65.
        l_white, a_white, b_white = lab.srgb_to_cielab(255, 255, 255)
        self.assertAlmostEqual(l_white, 100.0, places=3)
        self.assertAlmostEqual(a_white, 0.0, delta=0.05)
        self.assertAlmostEqual(b_white, 0.0, delta=0.05)

        # Preto sRGB: origem do espaco CIELAB.
        l_black, a_black, b_black = lab.srgb_to_cielab(0, 0, 0)
        self.assertAlmostEqual(l_black, 0.0, places=6)
        self.assertAlmostEqual(a_black, 0.0, places=6)
        self.assertAlmostEqual(b_black, 0.0, places=6)

        # Vermelho sRGB puro sob D65: valores de referencia CIE (aprox.).
        l_red, a_red, b_red = lab.srgb_to_cielab(255, 0, 0)
        self.assertAlmostEqual(l_red, 53.2408, delta=0.05)
        self.assertAlmostEqual(a_red, 80.0925, delta=0.1)
        self.assertAlmostEqual(b_red, 67.2032, delta=0.1)

        # Entradas fora de faixa retornam nulo em vez de estimar.
        for invalid in [(256, 0, 0), (-1, 0, 0), (None, 0, 0)]:
            l_val, a_val, b_val = lab.srgb_to_cielab(*invalid)
            self.assertTrue(math.isnan(l_val) and math.isnan(a_val) and math.isnan(b_val))

    def test_simulation_is_separate_and_temperature_changes_rate(self):
        cfg = {
            "reference_temperature_c": 25.0,
            "reference_half_life_days": 10.0,
            "activation_energy_kj_mol": 40.0,
            "initial_retention_pct": 100.0,
            "days": [0, 10],
            "scenarios": [
                {"scenario_id": "C25", "label": "25 C", "temperature_c": 25.0},
                {"scenario_id": "C4", "label": "4 C", "temperature_c": 4.0},
            ],
        }
        results = lab.simulate_scenarios(cfg)
        c25 = results.loc[results["scenario_id"] == "C25"].sort_values("day")
        c4 = results.loc[results["scenario_id"] == "C4"].sort_values("day")
        self.assertTrue((results["data_origin"] == "SIMULATION_ONLY").all())
        self.assertAlmostEqual(c25.iloc[0]["retention_pct_simulated"], 100.0)
        self.assertAlmostEqual(c25.iloc[1]["retention_pct_simulated"], 50.0, places=5)
        self.assertGreater(c4.iloc[1]["retention_pct_simulated"], c25.iloc[1]["retention_pct_simulated"])

    def test_simulation_requires_explicit_parameters(self):
        cfg = lab.default_simulation_config()
        with self.assertRaisesRegex(ValueError, "Configuração de simulação incompleta"):
            lab.simulate_scenarios(cfg)

    def test_ml_refuses_empty_dataset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lab.make_templates(root)
            with self.assertRaisesRegex(ValueError, "está vazio"):
                lab.train_ml_model(root, target="retention_pct")

    def test_ml_uses_experimental_data_and_grouped_batches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lab.make_templates(root)
            rows = []
            for batch in ["B1", "B2", "B3"]:
                for day in [0, 3, 7, 14]:
                    rows.append({
                        "record_id": f"{batch}-{day}", "data_origin": "EXPERIMENTAL",
                        "batch_id": batch, "independent_batch": batch,
                        "study_id": "",
                        "formulation": "native", "storage_condition": "4C_dark",
                        "temperature_c": 4, "day": day, "initial_pH": 3.5,
                        "light_condition": "dark", "oxygen_condition": "sealed",
                        "container_material": "amber_glass", "headspace_ratio_pct": 10,
                        "preservative_or_additive": "none", "pH_day": 3.5,
                        "retention_pct": max(20, 100 - day * 3 - (int(batch[-1]) - 1) * 2),
                    })
            # A simulated row with an extreme target must be ignored.
            rows.append({**rows[0], "record_id": "SIM-1", "data_origin": "SIMULATION_ONLY",
                         "batch_id": "SIM", "independent_batch": "SIM", "retention_pct": 9999})
            rows.append({**rows[0], "record_id": "LIT-1", "data_origin": "LITERATURE",
                         "batch_id": "LIT", "independent_batch": "LIT", "study_id": "S0",
                         "retention_pct": 9999})
            pd.DataFrame(rows).to_csv(root / "data" / "raw" / "ml_observations.csv", index=False)
            lab.train_ml_model(root, target="retention_pct")
            output = pd.read_csv(root / "data" / "ml" / "cross_validated_predictions.csv")
            self.assertEqual(len(output), 12)
            self.assertTrue((output["data_origin"] == "EXPERIMENTAL").all())
            self.assertTrue((root / "data" / "ml" / "ml_report.html").exists())

            with self.assertRaisesRegex(ValueError, "pelo menos 5"):
                lab.train_ml_model(root, target="retention_pct", include_literature=True)

            rows.extend([
                {**rows[0], "record_id": f"LIT-{study}", "data_origin": "LITERATURE",
                 "study_id": f"S{study}", "batch_id": "", "independent_batch": "",
                 "retention_pct": 70.0 + study}
                for study in range(1, 5)
            ])
            pd.DataFrame(rows).to_csv(root / "data" / "raw" / "ml_observations.csv", index=False)
            lab.train_ml_model(root, target="retention_pct", include_literature=True)
            included = pd.read_csv(root / "data" / "ml" / "cross_validated_predictions.csv")
            self.assertEqual(len(included), 17)
            self.assertEqual(included["data_origin"].value_counts().to_dict(),
                             {"EXPERIMENTAL": 12, "LITERATURE": 5})
            self.assertEqual(included.loc[included["data_origin"] == "LITERATURE",
                                          "cv_group"].nunique(), 5)
            report = json.loads((root / "data" / "ml" / "ml_metrics.json").read_text(encoding="utf-8"))
            self.assertIn("Domain shift", report["domain_shift_warning"])

    def test_init_creates_templates_and_config_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lab.make_templates(root)
            config = root / "data" / "config" / "simulation_parameters.json"
            template = root / "data" / "templates" / "ml_observation_template.csv"
            self.assertTrue(config.exists())
            self.assertTrue(template.exists())
            before = config.read_text(encoding="utf-8")
            lab.make_templates(root)
            self.assertEqual(config.read_text(encoding="utf-8"), before)

    def test_literature_data_separate_from_raw_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lab.make_templates(root)
            
            # Add literature data
            lit_dir = root / "data" / "literature"
            lit_dir.mkdir(parents=True, exist_ok=True)
            
            studies = pd.DataFrame([{
                "study_id": "TEST_STUDY",
                "citation": "Test 2024",
                "title": "Test study title",
                "doi": "10.1234/test",
                "url": "https://doi.org/10.1234/test",
                "species": "Brassica",
                "matrix": "Extrato",
                "solvent": "Agua",
                "extraction_conditions": "1:10",
                "method": "pH-differential",
                "pH": "3.0",
                "packaging": "Vidro",
                "storage_conditions": "4C escuro",
                "analysis_unit": "mg/L",
                "limitations": "Test only",
                "notes": "Test study"
            }])
            studies.to_csv(lit_dir / "literature_studies.csv", index=False)
            
            measurements = pd.DataFrame([{
                "study_id": "TEST_STUDY",
                "treatment_id": "T1",
                "source_url": "https://doi.org/10.1234/test",
                "doi": "10.1234/test",
                "source_location": "Table 1",
                "extraction_type": "Aquosa",
                "species": "Brassica",
                "matrix": "Extrato",
                "solvent": "Agua",
                "pH": "3.0",
                "additive": "",
                "additive_concentration_pct": "",
                "temperature_c": 4,
                "light_condition": "Escuro",
                "oxygen_condition": "Aerobico",
                "package_material": "Vidro",
                "time_value": 0,
                "time_unit": "dia",
                "measurement": "Anthocyanin",
                "value": 100.0,
                "standard_deviation": "",
                "value_unit": "mg/L",
                "replicate_count": "",
                "data_origin": "PUBLISHED_ARTICLE",
                "reported_or_calculated": "reported",
                "notes": "Test measurement"
            }])
            measurements.to_csv(lit_dir / "literature_measurements.csv", index=False)
            pd.DataFrame([{
                "study_id": "TEST_STUDY", "doi": "10.1234/test", "treatment_id": "T1",
                "time_value": 0, "time_unit": "dia", "measurement": "Anthocyanin",
                "value_unit": "mg/L", "verification_status": "VERIFICATION_PENDING",
                "verified_source_location": "", "reviewed_on": "", "reviewer": "",
                "verification_notes": "Local fixture sem revisão primária.",
            }], columns=lab.LITERATURE_STATUS_COLUMNS).to_csv(
                lit_dir / "literature_verification_status.csv", index=False
            )
            
            evidence = pd.DataFrame([{
                "study_id": "TEST_STUDY",
                "evidence_type": "kinetic_summary",
                "evidence_category": "first_order",
                "evidence_text": "Test kinetic",
                "origin_source": "Article",
                "source_url": "https://doi.org/10.1234/test",
                "doi": "10.1234/test",
                "source_location": "Table 1",
                "conditions": "4 C dark",
                "treatment_id": "T1",
                "additive": "",
                "additive_concentration_pct": "",
                "k_value": 0.01,
                "half_life": 69.3,
                "half_life_unit": "dia",
                "temperature_c": 4,
                "pH": "",
                "time_value": "",
                "time_unit": "",
                "measurement": "",
                "value": "",
                "standard_deviation": "",
                "value_unit": "",
                "k_unit": "dia^-1",
                "formula": "",
                "notes": "Test evidence"
            }])
            evidence.to_csv(lit_dir / "literature_evidence.csv", index=False)
            
            # Verify literature data loads correctly
            with self.assertWarnsRegex(UserWarning, "não são benchmarks aprovados"):
                studies_df, measurements_df, evidence_df = lab.validate_literature_data(
                    root, include_pending=True
                )
            self.assertEqual(len(studies_df), 1)
            self.assertEqual(len(measurements_df), 1)
            self.assertEqual(len(evidence_df), 1)
            self.assertEqual(measurements_df.iloc[0]["verification_status"], "VERIFICATION_PENDING")
            
            # Verify literature data is in separate directory
            self.assertTrue((root / "data" / "literature").exists())
            self.assertFalse((root / "data" / "raw" / "literature_studies.csv").exists())

    def test_literature_retention_calculation_marks_origin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lab.make_templates(root)
            
            lit_dir = root / "data" / "literature"
            lit_dir.mkdir(parents=True, exist_ok=True)
            
            measurements = pd.DataFrame([
                {
                    "study_id": "TEST", "treatment_id": "T1", "source_url": "url", "doi": "10.1234",
                    "source_location": "Table", "extraction_type": "Aqua", "species": "Brassica",
                    "matrix": "Extract", "solvent": "Water", "pH": "3.0", "additive": "",
                    "additive_concentration_pct": "", "temperature_c": 4, "light_condition": "Dark",
                    "oxygen_condition": "Aerobic", "package_material": "Glass", "time_value": 0,
                    "time_unit": "day", "measurement": "Anthocyanin", "value": 100.0,
                    "standard_deviation": "", "value_unit": "mg/L", "replicate_count": "",
                    "data_origin": "PUBLISHED_ARTICLE", "reported_or_calculated": "reported", "notes": ""
                },
                {
                    "study_id": "TEST", "treatment_id": "T1", "source_url": "url", "doi": "10.1234",
                    "source_location": "Table", "extraction_type": "Aqua", "species": "Brassica",
                    "matrix": "Extract", "solvent": "Water", "pH": "3.0", "additive": "",
                    "additive_concentration_pct": "", "temperature_c": 4, "light_condition": "Dark",
                    "oxygen_condition": "Aerobic", "package_material": "Glass", "time_value": 5,
                    "time_unit": "day", "measurement": "Anthocyanin", "value": 80.0,
                    "standard_deviation": "", "value_unit": "mg/L", "replicate_count": "",
                    "data_origin": "PUBLISHED_ARTICLE", "reported_or_calculated": "reported", "notes": ""
                }
            ])
            measurements.to_csv(lit_dir / "literature_measurements.csv", index=False)
            
            studies = pd.DataFrame([{
                "study_id": "TEST", "citation": "Test", "title": "Test study", "doi": "10.1234", "url": "url",
                "species": "Brassica", "matrix": "Extract", "solvent": "Water", "method": "pH",
                "extraction_conditions": "1:10",
                "pH": "3.0", "packaging": "Glass", "storage_conditions": "4C dark",
                "analysis_unit": "mg/L", "limitations": "", "notes": ""
            }])
            studies.to_csv(lit_dir / "literature_studies.csv", index=False)
            
            evidence = pd.DataFrame([{
                "study_id": "TEST", "evidence_type": "kinetic", "evidence_category": "first",
                "evidence_text": "Test", "origin_source": "Article", "k_value": "", "half_life": "",
                "half_life_unit": "", "temperature_c": "", "conditions": "", "notes": ""
            }])
            evidence.to_csv(lit_dir / "literature_evidence.csv", index=False)
            
            measurements_with_retention = lab.calculate_literature_retention(measurements)
            
            # Check that retention is calculated and origin is marked
            self.assertIn("retention_pct", measurements_with_retention.columns)
            self.assertIn("retention_origin", measurements_with_retention.columns)
            self.assertIn("retention_formula", measurements_with_retention.columns)
            
            # Initial value should be marked as 100%
            initial_row = measurements_with_retention[measurements_with_retention["time_value"] == 0].iloc[0]
            self.assertEqual(initial_row["retention_pct"], 100.0)
            self.assertEqual(initial_row["retention_origin"], "calculated")
            self.assertEqual(initial_row["retention_reference_time_value"], 0)
            
            # Later value should be calculated
            later_row = measurements_with_retention[measurements_with_retention["time_value"] == 5].iloc[0]
            self.assertAlmostEqual(later_row["retention_pct"], 80.0, places=5)
            self.assertEqual(later_row["retention_origin"], "calculated")
            self.assertEqual(later_row["retention_formula"],
                             "100 * value / measured_value_at_earliest_time")

            zero_baseline = measurements.copy()
            zero_baseline["value"] = [0.0, 10.0]
            zero_retention = lab.calculate_literature_retention(zero_baseline)
            self.assertTrue(zero_retention["retention_pct"].isna().all())

    def test_project_literature_sources_are_complete_and_preserve_reported_values(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertWarnsRegex(UserWarning, "não são benchmarks aprovados"):
            studies, measurements, evidence = lab.validate_literature_data(root, include_pending=True)

        self.assertEqual(len(studies), 6)
        self.assertEqual(len(measurements), 39)
        self.assertEqual(
            set(studies["study_id"]),
            {"STUDY_A", "STUDY_B", "STUDY_C", "STUDY_D", "STUDY_E", "STUDY_F"},
        )
        # STUDY_F (Muhamad et al. 2023) e registro bibliografico separado,
        # relacionado a STUDY_B como possivel sobreposicao; nao leva observacoes.
        study_f = studies.loc[studies["study_id"] == "STUDY_F"]
        self.assertEqual(len(study_f), 1)
        self.assertEqual(study_f.iloc[0]["doi"], "10.26656/fr.2017.6(S2).030")
        self.assertTrue(measurements["source_url"].str.startswith("https://").all())
        self.assertTrue(measurements["source_location"].str.strip().ne("").all())
        self.assertTrue(measurements["data_origin"].eq("PUBLISHED_ARTICLE").all())
        self.assertTrue(measurements["reported_or_calculated"].eq("reported").all())
        # Status de verificação: STUDY_B verificado (texto integral); os demais, pendentes.
        verified_mask = measurements["verification_status"].eq("VERIFIED")
        self.assertTrue(measurements.loc[verified_mask, "study_id"].eq("STUDY_B").all())
        self.assertEqual(int(verified_mask.sum()), 21)
        self.assertTrue(measurements.loc[~verified_mask, "verification_status"]
                        .eq("VERIFICATION_PENDING").all())
        # Desvios-padrão: preenchidos apenas para STUDY_B (transcritos da Tabela 8).
        sd_mask = measurements["standard_deviation"].notna()
        self.assertTrue(measurements.loc[sd_mask, "study_id"].eq("STUDY_B").all())
        self.assertEqual(int(sd_mask.sum()), 21)
        self.assertTrue(measurements.loc[measurements["study_id"] != "STUDY_B",
                                         "standard_deviation"].isna().all())

        study_a = measurements.loc[measurements["study_id"] == "STUDY_A"]
        self.assertEqual(len(study_a), 18)
        self.assertEqual(set(study_a["treatment_id"]), {"P2", "P4", "P8", "P9", "P13", "P14"})
        self.assertTrue(study_a.groupby("treatment_id")["time_value"].apply(
            lambda times: set(times) == {1, 5, 10}
        ).all())
        self.assertNotIn(0, set(study_a["time_value"]))
        expected_a = {
            "P4": [116.859, 110.353, 107.653],
            "P2": [115.470, 107.321, 104.161],
            "P8": [116.462, 97.179, 91.940],
            "P9": [72.678, 59.587, 49.249],
            "P13": [74.273, 44.663, 38.482],
            "P14": [74.798, 58.212, 49.402],
        }
        for treatment, expected_values in expected_a.items():
            observed = study_a.loc[study_a["treatment_id"] == treatment].sort_values("time_value")["value"].tolist()
            self.assertEqual(observed, expected_values)

        study_b = measurements.loc[measurements["study_id"] == "STUDY_B"]
        self.assertEqual(len(study_b), 21)
        self.assertTrue(study_b["matrix"].str.contains("rosela").all())
        self.assertEqual(set(study_b["package_material"]), {"Vidro", "Lata metálica", "Polipropileno"})
        expected_b = {
            "Vidro": [263.40, 132.10, 87.75, 74.38, 55.60, 48.29, 34.36],
            "Lata metálica": [262.66, 113.20, 94.54, 71.80, 49.27, 39.85, 30.50],
            "Polipropileno": [262.17, 96.88, 88.21, 40.42, 21.09, 14.38, 10.44],
        }
        for package, expected_values in expected_b.items():
            observed = study_b.loc[study_b["package_material"] == package].sort_values("time_value")["value"].tolist()
            self.assertEqual(observed, expected_values)

        # Validação determinística dos 21 pares (média, desvio-padrão) pela combinação
        # de embalagem x mês, transcritos da Tabela 8 (p. 6) do texto integral de
        # Muhamad et al. (2022) — dados do artigo, não artificiais.
        table8_b = {
            ("Vidro", 0): (263.40, 1.67), ("Vidro", 1): (132.10, 3.60), ("Vidro", 2): (87.75, 16.60),
            ("Vidro", 3): (74.38, 2.21), ("Vidro", 4): (55.60, 0.87), ("Vidro", 5): (48.29, 0.96),
            ("Vidro", 6): (34.36, 1.83),
            ("Lata metálica", 0): (262.66, 0.87), ("Lata metálica", 1): (113.20, 3.96),
            ("Lata metálica", 2): (94.54, 23.17), ("Lata metálica", 3): (71.80, 7.35),
            ("Lata metálica", 4): (49.27, 1.93), ("Lata metálica", 5): (39.85, 0.85),
            ("Lata metálica", 6): (30.50, 0.17),
            ("Polipropileno", 0): (262.17, 1.04), ("Polipropileno", 1): (96.88, 0.71),
            ("Polipropileno", 2): (88.21, 18.55), ("Polipropileno", 3): (40.42, 0.49),
            ("Polipropileno", 4): (21.09, 1.31), ("Polipropileno", 5): (14.38, 0.17),
            ("Polipropileno", 6): (10.44, 1.42),
        }
        actual_b = {
            (row["package_material"], int(row["time_value"])): (
                float(row["value"]), float(row["standard_deviation"]))
            for _, row in study_b.iterrows()
        }
        self.assertEqual(len(actual_b), 21)
        self.assertEqual(set(actual_b.keys()), set(table8_b.keys()))
        for key in sorted(table8_b.keys()):
            self.assertEqual(actual_b[key], table8_b[key],
                             f"divergência de média/DP em {key[0]} x mês {key[1]}")

        self.assertEqual(len(evidence.loc[evidence["study_id"] == "STUDY_D"]), 3)
        reported_a = evidence.loc[evidence["study_id"] == "STUDY_A"].set_index("treatment_id")
        self.assertEqual(reported_a.loc["P4", "k_value"], 0.009)
        self.assertEqual(reported_a.loc["P4", "half_life"], 76.0)
        pan = evidence.loc[evidence["study_id"] == "STUDY_D"]
        self.assertEqual(set(pan.loc[pan["time_unit"].notna(), "time_unit"]), {"h"})
        retention_at_ph = pan.loc[pan["evidence_category"] == "retention_at_pH"].iloc[0]
        self.assertEqual(retention_at_ph["pH"], 2.0)
        self.assertEqual(retention_at_ph["value"], 92.92)
        self.assertEqual(retention_at_ph["standard_deviation"], 0.69)
        half_life = pan.loc[pan["evidence_category"] == "first_order_degradation"].iloc[0]
        self.assertEqual(half_life["temperature_c"], 50)
        self.assertEqual(half_life["pH"], 2.0)
        self.assertEqual(half_life["half_life"], 67.28)
        self.assertEqual(half_life["half_life_unit"], "h")

        lin = evidence.loc[evidence["study_id"] == "STUDY_C"]
        absorbance = lin.loc[lin["measurement"] == "absorbance increase"].iloc[0]
        color = lin.loc[lin["measurement"] == "total color variation decrease"].iloc[0]
        self.assertTrue(lin.loc[lin["evidence_category"] == "reported_response",
                                "evidence_type"].eq("quantitative_summary").all())
        self.assertEqual(absorbance["value"], 247.70)
        self.assertEqual(absorbance["value_unit"], "%")
        self.assertEqual(color["value"], 70.34)
        self.assertEqual(color["value_unit"], "%")
        patras = evidence.loc[evidence["study_id"] == "STUDY_E"]
        self.assertEqual(set(patras["time_value"]), {20})
        self.assertEqual(set(patras["time_unit"]), {"weeks"})
        self.assertEqual(set(patras["pH"]), {6.31})
        self.assertEqual(set(patras["additive_concentration_pct"]), {0.2})

    def test_literature_validation_rejects_invalid_unit_origin_and_untraceable_rows(self):
        source = Path(__file__).resolve().parents[1] / "data" / "literature"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lit_dir = root / "data" / "literature"
            lit_dir.mkdir(parents=True)
            for filename in ("literature_studies.csv", "literature_measurements.csv",
                             "literature_evidence.csv", "literature_verification_status.csv"):
                shutil.copyfile(source / filename, lit_dir / filename)

            measurements_path = lit_dir / "literature_measurements.csv"
            measurements = pd.read_csv(measurements_path)
            measurements.loc[0, "value_unit"] = "unverified-unit"
            measurements.to_csv(measurements_path, index=False)
            with self.assertRaisesRegex(ValueError, "Unidade incompatível"):
                lab.validate_literature_data(root)

            measurements.loc[0, "value_unit"] = "mg CGE/100 g FW"
            measurements.loc[0, "data_origin"] = "SIMULATION_ONLY"
            measurements.to_csv(measurements_path, index=False)
            with self.assertRaisesRegex(ValueError, "PUBLISHED_ARTICLE"):
                lab.validate_literature_data(root)

            measurements.loc[0, "data_origin"] = "PUBLISHED_ARTICLE"
            measurements.loc[0, "source_location"] = ""
            measurements.to_csv(measurements_path, index=False)
            with self.assertRaisesRegex(ValueError, "source_location"):
                lab.validate_literature_data(root)

    def test_literature_kinetics_fit_each_treatment_without_mixing_units(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertWarnsRegex(UserWarning, "não são benchmarks aprovados"):
            _, measurements, _ = lab.validate_literature_data(root, include_pending=True)
        with self.assertWarnsRegex(UserWarning, "exploratório inclui"):
            kinetics = lab.fit_literature_kinetics(measurements, include_pending=True)

        self.assertEqual(len(kinetics), 9)
        self.assertEqual(set(kinetics["treatment_id"]), {"P2", "P4", "P8", "P9", "P13", "P14",
                                                         "GLASS", "METAL_CAN", "POLYPROPYLENE"})
        self.assertTrue(kinetics["residual_rmse_log"].notna().all())
        self.assertTrue(kinetics["residual_rmse_value"].notna().all())
        self.assertTrue(kinetics["data_origin"].eq("PUBLISHED_ARTICLE").all())
        self.assertTrue(kinetics["reported_or_calculated"].eq("calculated_from_published_series").all())
        self.assertTrue(kinetics["source_url"].str.startswith("https://").all())
        # Ajustes exploratórios mantêm o status de origem: STUDY_A pendente, STUDY_B verificado.
        self.assertEqual(set(kinetics["verification_status"]),
                         {"VERIFICATION_PENDING", "VERIFIED"})

    def test_experimental_plan_equalizes_initial_ph_and_separates_outcomes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lab.make_templates(root)
            lab.generate_experimental_plan(root, concentrations=[0.2, 0.8])
            plan = pd.read_csv(root / "data" / "literature" / "processed" /
                               "experimental_plan_stabilization.csv")

            self.assertEqual(set(plan["target_pH"]), {3.0})
            self.assertEqual(set(plan["storage_condition"]), {"4C_DARK"})
            self.assertEqual(set(plan["additive_concentration_pct"]), {0, 0.2, 0.4, 0.8})
            self.assertTrue(plan["pH_discrimination_outcome"].str.contains("separabilidade").all())
            self.assertTrue(plan["color_outcome"].ne(plan["pH_outcome"]).all())
            reference = plan.loc[plan["additive_concentration_pct"] == 0.4].iloc[0]
            self.assertIn("bebida simulada", reference["literature_reference"])
            self.assertTrue(plan["alert_rule"].str.contains("estatisticamente significativa").all())


if __name__ == "__main__":
    unittest.main()
