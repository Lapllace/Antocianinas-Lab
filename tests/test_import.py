"""Testes do módulo de importação assistida (anthocyanin_import).

Todos os dados aqui são SINTÉTICOS, criados apenas para os testes, e nunca
são misturados aos dados cientificos reais do projeto. Nenhum arquivo de
data/raw, data/literature ou data/simulation é modificado por estes testes.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import anthocyanin_import as ai
import anthocyanin_persistence as persist
import anthocyanin_ui as ui


def stab_row(**over):
    """Linha sintetica valida para estabilidade (nao e dado de laboratorio)."""
    r = {
        "batch_id": "SYN-B1", "formulation": "native", "storage_condition": "C4_DARK",
        "day": "0", "vial_id": "SYN-V1", "replicate": "1", "pH_storage": "4.0",
        "a520_ph1": "0.52", "a700_ph1": "0.02", "a520_ph45": "0.04", "a700_ph45": "0.02",
        "dilution_factor": "10", "path_length_cm": "1", "notes": "",
    }
    r.update(over)
    return r


def color_row(**over):
    """Linha sintetica valida para cor."""
    r = {
        "batch_id": "SYN-B1", "formulation": "native", "storage_condition": "C4_DARK",
        "day": "0", "vial_id": "SYN-V1", "replicate": "1", "target_pH": "3.0",
        "measured_pH_final": "3.1", "r": "120", "g": "40", "b": "90",
        "L_star": "", "a_star": "", "b_star": "", "absorbance_max_nm": "",
        "absorbance_max": "", "notes": "",
    }
    r.update(over)
    return r


def micro_row(**over):
    """Linha sintetica valida para microbiologia."""
    r = {
        "batch_id": "SYN-B1", "formulation": "native", "storage_condition": "C4_DARK",
        "day": "7", "vial_id": "SYN-V1", "test_type": "count", "result_value": "2.3",
        "result_unit": "CFU/g", "method": "", "notes": "",
    }
    r.update(over)
    return r


class TestParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_parse_csv(self):
        p = self.tmp / "s.csv"
        pd.DataFrame([stab_row(), stab_row(vial_id="SYN-V2", replicate="2")]).to_csv(p, index=False)
        df = ai.parse_source(path=p)
        self.assertEqual(len(df), 2)
        self.assertIn("batch_id", df.columns)

    def test_parse_xlsx(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl indisponivel")
        p = self.tmp / "s.xlsx"
        pd.DataFrame([stab_row()]).to_excel(p, index=False, engine="openpyxl")
        df = ai.parse_source(path=p)
        self.assertEqual(len(df), 1)

    def test_parse_xlsx_missing_openpyxl_message(self):
        p = self.tmp / "s.xlsx"
        pd.DataFrame([stab_row()]).to_excel(p, index=False, engine="openpyxl")
        # Simula ausencia do openpyxl reescrevendo _read_xlsx_file.
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "openpyxl":
                raise ImportError("simulado")
            return real_import(name, *a, **k)
        builtins.__import__ = fake_import
        try:
            with self.assertRaises(ValueError) as ctx:
                ai.parse_source(path=p)
            self.assertIn("openpyxl", str(ctx.exception))
        finally:
            builtins.__import__ = real_import

    def test_parse_pasted_tab(self):
        text = "batch_id\tday\nSYN-B1\t0\nSYN-B2\t3\n"
        df = ai.parse_source(pasted=text)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ["batch_id", "day"])

    def test_parse_pasted_comma(self):
        text = "batch_id,day\nSYN-B1,0\n"
        df = ai.parse_source(pasted=text)
        self.assertEqual(len(df), 1)

    def test_parse_unsupported_format(self):
        with self.assertRaises(ValueError):
            ai.parse_source(path=self.tmp / "a.pdf")

    def test_parse_empty_source_raises(self):
        with self.assertRaises(ValueError):
            ai.parse_source()


class TestMapping(unittest.TestCase):
    def test_exact_normalized_match(self):
        m = ai.suggest_mapping(["Batch ID", "DAY", "PH_STORAGE"], ai.columns_for("stability"))
        self.assertEqual(m["batch_id"], "Batch ID")
        self.assertEqual(m["day"], "DAY")
        self.assertEqual(m["pH_storage"], "PH_STORAGE")

    def test_compact_match_tolerates_separators(self):
        m = ai.suggest_mapping(["A 520 pH 1"], ai.columns_for("stability"))
        self.assertEqual(m["a520_ph1"], "A 520 pH 1")

    def test_alias_synonym(self):
        m = ai.suggest_mapping(["Lote", "Dias"], ai.columns_for("stability"))
        self.assertEqual(m["batch_id"], "Lote")
        self.assertEqual(m["day"], "Dias")

    def test_ambiguous_leaves_none(self):
        # Duas colunas casam com batch_id -> ambiguo, fica sem sugestao.
        m = ai.suggest_mapping(["batch_id", "Batch ID"], ai.columns_for("stability"))
        self.assertIsNone(m["batch_id"])

    def test_unmatched_field_is_none(self):
        m = ai.suggest_mapping(["qualquer_coisa"], ai.columns_for("stability"))
        self.assertIsNone(m["batch_id"])

    def test_apply_mapping_preserves_values_and_order(self):
        src = pd.DataFrame([{"Lote": "SYN-B1", "Dias": "0", "lixo": "zzz"}])
        mapping = ai.suggest_mapping(list(src.columns), ai.columns_for("stability"))
        mapping["replicate"] = None
        out = ai.apply_mapping(src, mapping, ai.columns_for("stability"))
        self.assertEqual(list(out.columns), ai.columns_for("stability"))
        self.assertEqual(out.loc[0, "batch_id"], "SYN-B1")
        self.assertEqual(out.loc[0, "day"], "0")
        self.assertEqual(out.loc[0, "replicate"], "")
        self.assertNotIn("lixo", out.columns)

    def test_apply_mapping_keeps_source_not_converted(self):
        # Valor com virgula decimal e mantido como texto (nao convertido).
        src = pd.DataFrame([{"ph_storage": "4,0"}])
        mapping = ai.suggest_mapping(list(src.columns), ai.columns_for("stability"))
        out = ai.apply_mapping(src, mapping, ai.columns_for("stability"))
        self.assertEqual(out.loc[0, "pH_storage"], "4,0")


class TestValidationPreview(unittest.TestCase):
    def test_missing_required_flagged(self):
        mapped = pd.DataFrame([stab_row(formulation="", vial_id="", replicate="")])
        pv = ai.build_preview(mapped, "stability")
        self.assertEqual(pv["summary"]["invalidas"], 1)
        self.assertIn("formulation", pv["summary"]["campos_obrigatorios_ausentes"])
        self.assertIn("vial_id", pv["summary"]["campos_obrigatorios_ausentes"])

    def test_out_of_range_flagged(self):
        mapped = pd.DataFrame([stab_row(pH_storage="15.0")])
        pv = ai.build_preview(mapped, "stability")
        self.assertFalse(pv["rows"][0]["valida"])
        self.assertTrue(pv["summary"]["valores_fora_limite_ou_invalidos"])

    def test_non_numeric_flagged(self):
        mapped = pd.DataFrame([stab_row(dilution_factor="dez")])
        pv = ai.build_preview(mapped, "stability")
        self.assertFalse(pv["rows"][0]["valida"])

    def test_color_rgb_required(self):
        mapped = pd.DataFrame([color_row(r="")])
        pv = ai.build_preview(mapped, "color")
        self.assertEqual(pv["summary"]["invalidas"], 1)

    def test_valid_row_passes(self):
        mapped = pd.DataFrame([stab_row()])
        pv = ai.build_preview(mapped, "stability")
        self.assertEqual(pv["summary"]["validas"], 1)


class TestDuplicates(unittest.TestCase):
    def test_duplicate_vs_existing(self):
        existing = pd.DataFrame([stab_row()])
        mapped = pd.DataFrame([stab_row()])
        pv = ai.build_preview(mapped, "stability", existing_df=existing)
        self.assertTrue(pv["rows"][0]["duplicata"])
        self.assertFalse(pv["rows"][0]["valida"])
        self.assertEqual(pv["summary"]["duplicatas"], 1)

    def test_duplicate_within_batch(self):
        mapped = pd.DataFrame([stab_row(), stab_row()])
        pv = ai.build_preview(mapped, "stability", existing_df=pd.DataFrame(columns=ai.columns_for("stability")))
        self.assertEqual(pv["summary"]["duplicatas"], 1)  # segunda linha duplica a primeira
        self.assertTrue(pv["rows"][1]["duplicata"])

    def test_no_duplicate_when_different(self):
        mapped = pd.DataFrame([stab_row(), stab_row(vial_id="SYN-V2", replicate="2")])
        pv = ai.build_preview(mapped, "stability", existing_df=pd.DataFrame(columns=ai.columns_for("stability")))
        self.assertEqual(pv["summary"]["duplicatas"], 0)


class TestUnits(unittest.TestCase):
    def test_micro_unit_missing_blocks(self):
        mapped = pd.DataFrame([micro_row(result_unit="")])
        pv = ai.build_preview(mapped, "micro")
        self.assertFalse(pv["rows"][0]["valida"])
        self.assertTrue(any("result_unit" in m for m in pv["summary"]["unidades_ausentes"]))

    def test_micro_unit_present_passes(self):
        mapped = pd.DataFrame([micro_row()])
        pv = ai.build_preview(mapped, "micro")
        self.assertEqual(pv["summary"]["validas"], 1)

    def test_micro_blank_result_no_unit_required(self):
        mapped = pd.DataFrame([micro_row(result_value="", result_unit="")])
        pv = ai.build_preview(mapped, "micro")
        self.assertTrue(pv["rows"][0]["valida"])


class TestPreviewEditing(unittest.TestCase):
    def test_finalize_drops_excluded_rows(self):
        rows = ai.build_preview(pd.DataFrame([stab_row(), stab_row(vial_id="SYN-V2", replicate="2")]), "stability")["rows"]
        frame = ai.preview_rows_to_frame(rows, ai.columns_for("stability"))
        frame.loc[0, "_excluir"] = True
        final = ai.finalize_from_edited(frame, ai.columns_for("stability"))
        self.assertEqual(len(final), 1)
        self.assertEqual(final.loc[0, "vial_id"], "SYN-V2")

    def test_finalize_edited_value_used(self):
        rows = ai.build_preview(pd.DataFrame([stab_row()]), "stability")["rows"]
        frame = ai.preview_rows_to_frame(rows, ai.columns_for("stability"))
        frame.loc[0, "vial_id"] = "SYN-EDITED"
        final = ai.finalize_from_edited(frame, ai.columns_for("stability"))
        self.assertEqual(final.loc[0, "vial_id"], "SYN-EDITED")


class TestNoWriteBeforeConfirm(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "stability_measurements.csv"
        persist.write_empty_csv(self.path, ai.columns_for("stability"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_preview_does_not_write(self):
        before = self.path.read_text(encoding="utf-8")
        mapped = pd.DataFrame([stab_row()])
        ai.build_preview(mapped, "stability", existing_df=persist.load_csv(self.path, ai.columns_for("stability")))
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_write_only_on_explicit_append(self):
        final = pd.DataFrame([stab_row()])
        result = persist.append_row_safely(self.path, final, ai.key_for("stability"), ai.combined_validator("stability"))
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(persist.load_csv(self.path, ai.columns_for("stability"))), 1)


class TestPreserveExistingOnFailure(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "stability_measurements.csv"
        persist.write_empty_csv(self.path, ai.columns_for("stability"))
        persist.append_row_safely(self.path, pd.DataFrame([stab_row()]),
                                  ai.key_for("stability"), ai.combined_validator("stability"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_duplicate_at_write_preserves_existing(self):
        rows_before = len(persist.load_csv(self.path, ai.columns_for("stability")))
        dup = pd.DataFrame([stab_row()])
        result = persist.append_row_safely(self.path, dup, ai.key_for("stability"), ai.combined_validator("stability"))
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(persist.load_csv(self.path, ai.columns_for("stability"))), rows_before)

    def test_validation_error_at_write_preserves_existing(self):
        rows_before = len(persist.load_csv(self.path, ai.columns_for("stability")))
        bad = pd.DataFrame([stab_row(pH_storage="15.0")])
        result = persist.append_row_safely(self.path, bad, ai.key_for("stability"), ai.combined_validator("stability"))
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(persist.load_csv(self.path, ai.columns_for("stability"))), rows_before)


class TestAppendFixRegression(unittest.TestCase):
    """Garante que append_row_safely realmente acrescenta a um CSV nao-vazio
    (regressao do bug que descartava as linhas novas)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "stability_measurements.csv"
        persist.write_empty_csv(self.path, ai.columns_for("stability"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_two_distinct_rows_both_persist(self):
        persist.append_row_safely(self.path, pd.DataFrame([stab_row()]),
                                  ai.key_for("stability"), ai.combined_validator("stability"))
        second = pd.DataFrame([stab_row(vial_id="SYN-V2", replicate="2")])
        r = persist.append_row_safely(self.path, second, ai.key_for("stability"), ai.combined_validator("stability"))
        self.assertEqual(r["status"], "success")
        self.assertEqual(len(persist.load_csv(self.path, ai.columns_for("stability"))), 2)

    def test_multi_row_append_at_once(self):
        rows = pd.DataFrame([stab_row(), stab_row(vial_id="SYN-V2", replicate="2"),
                            stab_row(vial_id="SYN-V3", replicate="3")])
        r = persist.append_row_safely(self.path, rows, ai.key_for("stability"), ai.combined_validator("stability"))
        self.assertEqual(r["status"], "success")
        self.assertEqual(len(persist.load_csv(self.path, ai.columns_for("stability"))), 3)


class TestFullImportFlow(unittest.TestCase):
    """Fluxo ponta a ponta: parse -> mapear -> prever -> confirmar -> gravar."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "stability_measurements.csv"
        persist.write_empty_csv(self.path, ai.columns_for("stability"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_csv_import_flow_writes(self):
        csv_path = self.tmp / "entrada.csv"
        pd.DataFrame([
            stab_row(),
            stab_row(vial_id="SYN-V2", replicate="2"),
        ]).to_csv(csv_path, index=False)
        src = ai.parse_source(path=csv_path)
        mapping = ai.suggest_mapping(list(src.columns), ai.columns_for("stability"))
        mapped = ai.apply_mapping(src, mapping, ai.columns_for("stability"))
        preview = ai.build_preview(mapped, "stability", existing_df=persist.load_csv(self.path, ai.columns_for("stability")))
        self.assertEqual(preview["summary"]["validas"], 2)
        final = ai.finalize_from_edited(ai.preview_rows_to_frame(preview["rows"], ai.columns_for("stability")),
                                       ai.columns_for("stability"))
        r = persist.append_row_safely(self.path, final, ai.key_for("stability"), ai.combined_validator("stability"))
        self.assertEqual(r["status"], "success")
        self.assertEqual(len(persist.load_csv(self.path, ai.columns_for("stability"))), 2)


class TestUploadedSourceState(unittest.TestCase):
    def test_same_uploaded_source_keeps_preview_across_reruns(self):
        source = pd.DataFrame([{"batch_id": "SYN-B1", "day": "0"}])
        state = {
            "imp_source_df": source.copy(),
            "imp_source_name": "entrada.csv",
            "imp_preview_built": True,
        }

        ui._imp_update_source(state, source.copy(), "entrada.csv")

        self.assertTrue(state["imp_preview_built"])

    def test_changed_uploaded_source_invalidates_preview(self):
        state = {
            "imp_source_df": pd.DataFrame([{"batch_id": "SYN-B1", "day": "0"}]),
            "imp_source_name": "entrada.csv",
            "imp_preview_built": True,
        }
        changed_source = pd.DataFrame([{"batch_id": "SYN-B2", "day": "0"}])

        ui._imp_update_source(state, changed_source, "entrada.csv")

        self.assertFalse(state["imp_preview_built"])
        self.assertEqual(state["imp_source_df"].iloc[0]["batch_id"], "SYN-B2")


if __name__ == "__main__":
    unittest.main()
