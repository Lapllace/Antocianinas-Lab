"""Testes da camada de persistência: validação, backup, duplicidade e isolamento."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import anthocyanin_lab as lab
import anthocyanin_persistence as persist

ROOT = Path(__file__).resolve().parents[1]


class TestFieldValidation(unittest.TestCase):
    def test_stab_rejects_pH_out_of_range(self):
        row = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "replicate": "1", "pH_storage": "15.0",
               "a520_ph1": "0.5", "a700_ph1": "0.02", "a520_ph45": "0.04", "a700_ph45": "0.02",
               "dilution_factor": "10", "path_length_cm": "1", "notes": ""}
        self.assertTrue(persist.validate_stab_descriptions(row))

    def test_stab_rejects_zero_dilution(self):
        row = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "replicate": "1", "pH_storage": "4.0",
               "a520_ph1": "0.5", "a700_ph1": "0.02", "a520_ph45": "0.04", "a700_ph45": "0.02",
               "dilution_factor": "0", "path_length_cm": "1", "notes": ""}
        self.assertTrue(persist.validate_stab_descriptions(row))

    def test_stab_rejects_negative_absorbance(self):
        row = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "replicate": "1", "pH_storage": "4.0",
               "a520_ph1": "-0.5", "a700_ph1": "0.02", "a520_ph45": "0.04", "a700_ph45": "0.02",
               "dilution_factor": "10", "path_length_cm": "1", "notes": ""}
        self.assertTrue(persist.validate_stab_descriptions(row))

    def test_color_rejects_rgb_out_of_range(self):
        row = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "replicate": "1", "target_pH": "4",
               "measured_pH_final": "4.0", "r": "300", "g": "10", "b": "10", "notes": ""}
        self.assertTrue(persist.validate_color_descriptions(row))

    def test_color_accepts_valid_rgb(self):
        row = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "replicate": "1", "target_pH": "4",
               "measured_pH_final": "4.0", "r": "255", "g": "0", "b": "0", "notes": ""}
        self.assertEqual(persist.validate_color_descriptions(row), [])

    def test_micro_accepts_blank_result(self):
        row = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "test_type": "count", "result_value": "",
               "result_unit": "CFU/g", "method": "", "notes": ""}
        self.assertEqual(persist.validate_micro_descriptions(row), [])

class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "stability_measurements.csv"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_empty(self):
        persist.write_empty_csv(self.path, list(persist.STABILITY_COLUMNS))

    def _row(self, **overrides):
        row = {
            "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
            "day": "0", "vial_id": "V1", "replicate": "1", "pH_storage": "4.0",
            "a520_ph1": "0.52", "a700_ph1": "0.02", "a520_ph45": "0.04", "a700_ph45": "0.02",
            "dilution_factor": "10", "path_length_cm": "1", "notes": "",
        }
        row.update(overrides)
        return row

    def test_append_non_duplicate(self):
        self._write_empty()
        result = persist.append_row_safely(
            self.path, pd.DataFrame([self._row()]), persist.STABILITY_KEY,
            persist.validate_stab_descriptions
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["appended_count"], 1)
        self.assertTrue((self.tmp / "backups").exists())
        self.assertTrue(self.path.exists() and self.path.stat().st_size > 0)

    def test_append_duplicate_prevented_without_overwrite(self):
        self._write_empty()
        first = self._row(vial_id="V1", replicate="1")
        persist.append_row_safely(self.path, pd.DataFrame([first]), persist.STABILITY_KEY,
                                  persist.validate_stab_descriptions)
        duplicate = self._row(vial_id="V1", replicate="1")
        result = persist.append_row_safely(self.path, pd.DataFrame([duplicate]), persist.STABILITY_KEY,
                                           persist.validate_stab_descriptions)
        self.assertEqual(result["status"], "error")
        self.assertIn("duplicado", result["message"])
        self.assertEqual(self.path.read_text(encoding="utf-8").count("B1,native"), 1)

    def test_backup_created_before_write(self):
        self._write_empty()
        persist.append_row_safely(self.path, pd.DataFrame([self._row()]), persist.STABILITY_KEY,
                                  persist.validate_stab_descriptions)
        backups = list((self.tmp / "backups").glob("*.csv"))
        self.assertTrue(backups)

    def test_validation_error_not_written(self):
        self._write_empty()
        bad = {"batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
               "day": "0", "vial_id": "V1", "replicate": "1", "pH_storage": "15.0",
               "a520_ph1": "0.5", "a700_ph1": "0.02", "a520_ph45": "0.04", "a700_ph45": "0.02",
               "dilution_factor": "10", "path_length_cm": "1", "notes": ""}
        result = persist.append_row_safely(self.path, pd.DataFrame([bad]),
                                           persist.STABILITY_KEY, persist.validate_stab_descriptions)
        self.assertEqual(result["status"], "error")
        # Nenhuma linha de dado foi gravada: o CSV permanece sem linhas.
        self.assertTrue(pd.read_csv(self.path).empty)


class TestDataIsolation(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        lab.make_templates(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_ml_observation(self, origin="EXPERIMENTAL", batch="B1", **kw):
        path = self.tmp / "data" / "raw" / "ml_observations.csv"
        rows = [
            {
                "record_id": "R1", "data_origin": origin, "batch_id": batch,
                "independent_batch": batch, "formulation": "native", "storage_condition": "4C_dark",
                "temperature_c": 4, "day": 0, "initial_pH": 3.5, "light_condition": "dark",
                "oxygen_condition": "sealed", "container_material": "amber_glass",
                "headspace_ratio_pct": 10, "preservative_or_additive": "none", "pH_day": 3.5,
                "study_id": "", "retention_pct": 100.0, "tac_mg_c3g_L": 1.0,
                "hue_deg": 0.0, "saturation_0_1": 1.0, "value_0_1": 1.0,
                "delta_e_cie76_vs_day0": 0.0, "assay_method": "", "instrument": "",
                "independent_batch": batch, "notes": "",
            }
        ]
        if origin == "LITERATURE":
            rows[0]["study_id"] = "STUDY_X"
        rows[0].update(kw)
        pd.DataFrame(rows).to_csv(path, index=False)

    def test_ml_refuses_literature_without_export(self):
        self._write_ml_observation(origin="LITERATURE")
        with self.assertRaisesRegex(ValueError, "Nenhuma linha EXPERIMENTAL"):
            lab.train_ml_model(self.tmp, target="retention_pct")

    def test_ml_uses_experimental_only(self):
        self._write_ml_observation()
        with self.assertRaisesRegex(ValueError, "Apenas 1 observações válidas"):
            lab.train_ml_model(self.tmp, target="retention_pct")

    def test_simulation_remains_simulated(self):
        cfg = lab.default_simulation_config()
        cfg["reference_half_life_days"] = 10.0
        cfg["activation_energy_kj_mol"] = 40.0
        results = lab.simulate_scenarios(cfg)
        self.assertTrue((results["data_origin"] == "SIMULATION_ONLY").all())

    def test_calculate_tac_ignores_literature_origin(self):
        stability = pd.DataFrame([{
            "batch_id": "B1", "formulation": "native", "storage_condition": "4C_dark",
            "day": 0, "vial_id": "V1", "replicate": 1, "pH_storage": 4.0,
            "a520_ph1": 0.52, "a700_ph1": 0.02, "a520_ph45": 0.04, "a700_ph45": 0.02,
            "dilution_factor": 10, "path_length_cm": 1, "notes": "",
        }])
        out = lab.calculate_tac(stability)
        self.assertIn("retention_pct", out.columns)
        self.assertEqual(out.loc[0, "retention_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()

