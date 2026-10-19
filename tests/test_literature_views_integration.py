#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integracao Fase 3: base harmonizada como fonte, com tres visoes separadas."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import pandas as pd
import pytest

import anthocyanin_lab as lab

ROOT = Path(__file__).resolve().parents[1]
RAW_NAMES = (
    "literature_measurements.csv",
    "literature_evidence.csv",
    "literature_verification_status.csv",
    "literature_studies.csv",
)
VOLATILE_COLUMNS = ("execution_id", "generated_on_utc")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_csv_hash(path: Path, id_column: str) -> str:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    kept = [c for c in frame.columns if c not in VOLATILE_COLUMNS]
    frame = frame[kept].sort_values(by=[id_column] + kept).reset_index(drop=True)
    text = frame.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def workdir():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        lit = root / "data" / "literature"
        (lit / "processed" / "harmonized").mkdir(parents=True)
        for name in RAW_NAMES:
            shutil.copyfile(ROOT / "data" / "literature" / name, lit / name)
        before = {name: _sha256(lit / name) for name in RAW_NAMES}
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "harmonize_literature.py"), "--dir", str(root)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0, result.stderr
        yield {"root": root, "before": before}


def test_raw_files_preserved(workdir):
    lit = workdir["root"] / "data" / "literature"
    for name, digest in workdir["before"].items():
        assert _sha256(lit / name) == digest


def test_no_published_measure_lost(workdir):
    root = workdir["root"]
    catalog = lab.load_harmonized_catalog(root)
    raw_m = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv",
                        dtype=str, keep_default_na=False)
    assert len(raw_m) == 39
    by_source = {row["source_record_id"]: row for _, row in catalog.iterrows()}
    for line, (_, raw) in enumerate(raw_m.iterrows(), start=2):
        row = by_source[f"{raw['study_id']}|L{line}"]
        assert row["treatment_id"] == raw["treatment_id"]
        assert row["measurement"] == raw["measurement"]
        assert float(row["value_original"]) == float(raw["value"])
        assert row["unit_original"] == raw["value_unit"]
        assert float(row["time_value_original"]) == float(raw["time_value"])
        assert row["time_unit_original"] == raw["time_unit"]
    assert len(catalog) == 54
    assert (catalog["evidence_class"] == "QUANTITATIVE_MEASUREMENT").sum() == 43
    assert (catalog["evidence_class"] == "PUBLISHED_KINETIC_PARAMETER").sum() == 8
    assert (catalog["evidence_class"] == "QUALITATIVE_NARRATIVE").sum() == 3


def test_evidence_classes_never_enter_fits(workdir):
    catalog = lab.load_harmonized_catalog(workdir["root"])
    with pytest.raises(ValueError, match="QUANTITATIVE_MEASUREMENT"):
        lab.adapt_measurements_for_analysis(
            catalog[catalog["evidence_class"] == "PUBLISHED_KINETIC_PARAMETER"]
        )
    with pytest.raises(ValueError, match="QUANTITATIVE_MEASUREMENT"):
        lab.adapt_measurements_for_analysis(
            catalog[catalog["evidence_class"] == "QUALITATIVE_NARRATIVE"]
        )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lab.analyze_literature(workdir["root"], view="pending")
    kinetics = pd.read_csv(
        workdir["root"] / "data" / "literature" / "processed" / "views"
        / "pending_exploratory" / "literature_kinetics.csv", dtype=str)
    assert len(kinetics) == 9
    published = pd.read_csv(
        workdir["root"] / "data" / "literature" / "processed" / "views"
        / "pending_exploratory" / "published_kinetic_parameters.csv", dtype=str)
    assert len(published) == 8
    assert set(published["reported_or_calculated"]) == {"reported"}
    assert set(kinetics["reported_or_calculated"]) == {"calculated_from_published_series"}
    narratives = pd.read_csv(
        workdir["root"] / "data" / "literature" / "processed" / "views"
        / "pending_exploratory" / "qualitative_narrative_evidence.csv", dtype=str)
    assert len(narratives) == 3


def test_views_filter_status_without_promotion(workdir):
    catalog = lab.load_harmonized_catalog(workdir["root"])
    views = lab.split_literature_views(catalog)
    assert len(views["verified"]) == 0
    assert len(views["pending"]) == 54
    assert len(views["rejected"]) == 0
    assert len(views["combined"]) == 54
    tampered = catalog.copy()
    tampered.loc[tampered.index[0], "verification_status"] = "VERIFIED"
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        lit = root / "data" / "literature"
        (lit / "processed" / "harmonized").mkdir(parents=True)
        for name in RAW_NAMES:
            shutil.copyfile(ROOT / "data" / "literature" / name, lit / name)
        tampered.to_csv(lit / "processed" / "harmonized" / "harmonized_measurements.csv", index=False)
        with pytest.raises(ValueError, match="localizacao primaria"):
            lab.load_harmonized_catalog(root)


def test_verified_default_excludes_pending(workdir):
    root = workdir["root"]
    with pytest.warns(UserWarning, match="excluidos da analise aprovada"):
        lab.analyze_literature(root)
    kinetics = pd.read_csv(root / "data" / "literature" / "processed"
                           / "views" / "verified" / "literature_kinetics.csv", dtype=str)
    assert len(kinetics) == 0
    assert list(kinetics.columns) == lab.LITERATURE_FIT_COLUMNS
    html = (root / "data" / "literature" / "processed"
            / "views" / "verified" / "literature_report.html").read_text(encoding="utf-8")
    assert "Nenhuma serie elegivel" in html


def test_exploratory_only_when_explicit(workdir):
    root = workdir["root"]
    with pytest.warns(UserWarning, match="exploratoria"):
        lab.analyze_literature(root, view="pending")
    html = (root / "data" / "literature" / "processed" / "views"
            / "pending_exploratory" / "literature_report.html").read_text(encoding="utf-8")
    assert "EXPLORATORIA" in html.upper()
    comp = pd.read_csv(root / "data" / "literature" / "processed" / "views"
                       / "pending_exploratory" / "literature_kinetic_model_comparison.csv",
                       dtype=str)
    assert set(comp["analysis_view"]) == {"pending"}
    assert set(comp["verification_status"]) == {"VERIFICATION_PENDING"}
    with pytest.raises(ValueError, match="combined"):
        lab.analyze_literature(root, include_pending=True, view="verified")


def test_no_mixed_units_or_matrices_in_fits(workdir):
    root = workdir["root"]
    catalog = lab.load_harmonized_catalog(root)
    assert (catalog["normalized_value"] == "").all()
    assert (catalog["normalized_unit"] == "").all()
    assert (catalog["normalization_formula"] == "").all()
    comp = pd.read_csv(root / "data" / "literature" / "processed" / "views"
                       / "pending_exploratory" / "literature_kinetic_model_comparison.csv",
                       dtype=str)
    assert len(comp) > 0
    summary = pd.read_csv(root / "data" / "literature" / "processed" / "views"
                          / "pending_exploratory" / "inclusion_exclusion_summary.csv",
                          dtype=str)
    assert "CROSS_STUDY_POOLING_BLOCKED" in set(summary["reason"])


def test_reproducible_without_volatile_metadata(workdir):
    root = workdir["root"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lab.analyze_literature(root, view="pending")
    first = _canonical_csv_hash(
        root / "data" / "literature" / "processed" / "views"
        / "pending_exploratory" / "literature_kinetics.csv", "treatment_id")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lab.analyze_literature(root, view="pending")
    second = _canonical_csv_hash(
        root / "data" / "literature" / "processed" / "views"
        / "pending_exploratory" / "literature_kinetics.csv", "treatment_id")
    assert first == second
    catalog = lab.load_harmonized_catalog(root)
    assert catalog["observation_id"].is_unique
    assert catalog["source_record_id"].is_unique


def test_ml_not_validated_preserved():
    import json
    status = json.loads((ROOT / "reports" / "validation" / "ml_validation_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "ML_NOT_VALIDATED"
