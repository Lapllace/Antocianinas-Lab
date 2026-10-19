#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes focados da harmonizacao de dados (Fase 2, Etapa 1)."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "tools" / "harmonize_literature.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("harmonize_literature", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_script():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dir", str(ROOT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"Script falhou: {result.stderr}"
    return ROOT / "data" / "literature" / "processed" / "harmonized" / "harmonized_measurements.csv"


def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def test_traces_each_observation_to_source_record():
    """Cada observacao tem observation_id e source_record_id rastreaveis."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")

    measurement_obs = df[df["observation_id"].str.startswith("OBS-", na=False)]
    assert len(measurement_obs) == len(measurements)

    for _, obs in measurement_obs.iterrows():
        src = obs["source_record_id"]
        study_id = obs["study_id"]
        line_num = int(src.split("L")[1])
        original_row = measurements.iloc[line_num - 2]
        assert original_row["study_id"] == study_id
        assert original_row["treatment_id"] == obs["treatment_id"]
        assert original_row["measurement"] == obs["measurement"]


def test_preserves_original_values_and_units():
    """value_original e unit_original sao copiados exatamente do CSV bruto."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")

    measurement_obs = df[df["observation_id"].str.startswith("OBS-", na=False)]
    for _, obs in measurement_obs.iterrows():
        line_num = int(obs["source_record_id"].split("L")[1])
        orig = measurements.iloc[line_num - 2]
        if str(obs["value_original"]).replace(".", "", 1).isdigit():
            assert float(obs["value_original"]) == float(orig["value"])
        assert obs["unit_original"] == orig["value_unit"]
        assert str(obs["time_value_original"]) == orig["time_value"]
        assert obs["time_unit_original"] == orig["time_unit"]


def test_units_not_converted():
    """mg CGE/100 g FW (STUDY_A) e mg equivalentes/L (STUDY_B) permanecem distintas."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")

    a_units = set(df.loc[df["study_id"] == "STUDY_A", "unit_original"].dropna())
    b_units = set(df.loc[df["study_id"] == "STUDY_B", "unit_original"].dropna())

    assert "mg CGE/100 g FW" in a_units
    assert "mg equivalentes de cianidina-3-glicosídeo/L" in b_units
    assert a_units.isdisjoint(b_units)

def test_time_units_not_converted():
    """dias (STUDY_A) e meses (STUDY_B) permanecem distintos."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")

    a_times = set(df.loc[df["study_id"] == "STUDY_A", "time_unit_original"].dropna())
    b_times = set(df.loc[df["study_id"] == "STUDY_B", "time_unit_original"].dropna())

    assert "dia" in a_times
    assert "mês" in b_times
    assert a_times.isdisjoint(b_times)


def test_missing_values_preserved_without_imputation():
    """Ausencias sao representadas como nulo, nunca como zero."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")

    measurement_obs = df[df["observation_id"].str.startswith("OBS-", na=False)]
    assert measurement_obs["standard_deviation"].isna().all()
    assert (measurement_obs["replicate_type"] == "not_reported").all()
    assert (measurement_obs["value_original"].notna()).all()


def test_verification_status_not_auto_upgraded():
    """Nenhum status e atualizado automaticamente para VERIFIED."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")

    assert (df["verification_status"] == "VERIFICATION_PENDING").all()


def test_deterministic_execution():
    """Duas execucoes com mesmo input geram output identico."""
    path1 = _run_script()
    path2 = _run_script()
    assert _checksum(path1) == _checksum(path2), "Saida nao e deterministica"


def test_no_duplicate_observation_ids():
    """Nenhum observation_id duplicado na saida."""
    path = _run_script()
    df = pd.read_csv(path)
    assert df["observation_id"].is_unique


def test_all_studies_mapped():
    """Todos os study_id estao mapeados para STUDY_A a STUDY_E."""
    path = _run_script()
    df = pd.read_csv(path)
    studies = set(df["study_id"].dropna().unique())
    assert studies <= {"STUDY_A", "STUDY_B", "STUDY_C", "STUDY_D", "STUDY_E"}


def test_no_normalization_applied():
    """Campos de normalizacao estao vazios (nenhuma conversao aplicada)."""
    path = _run_script()
    df = pd.read_csv(path)
    assert (df["normalization_formula"].isna() | (df["normalization_formula"] == "")).all()
    assert (df["normalized_value"].isna() | (df["normalized_value"] == "")).all()
    assert (df["normalized_unit"].isna() | (df["normalized_unit"] == "")).all()


# ---------------------------------------------------------------------------
# Regressoes da revisao pos-implementacao
# ---------------------------------------------------------------------------


def test_study_f_registered_with_correct_doi():
    """STUDY_F (Muhamad et al. 2023) existe no catalogo com o DOI correto."""
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)
    row = studies.loc[studies["study_id"] == "STUDY_F"]
    assert len(row) == 1, "STUDY_F deve existir exatamente uma vez no catalogo"
    assert row.iloc[0]["doi"] == "10.26656/fr.2017.6(S2).030"


def test_study_b_not_related_to_study_c():
    """STUDY_B nao pode ser relacionado a STUDY_C como publicacao sobreposta."""
    path = ROOT / "data" / "literature" / "processed" / "harmonized" / "relations_overlapping_publications.csv"
    df = pd.read_csv(path, dtype=str)
    assert not ((df["source_study_id"] == "STUDY_B") & (df["related_study_id"] == "STUDY_C")).any()
    assert not ((df["source_study_id"] == "STUDY_C") & (df["related_study_id"] == "STUDY_B")).any()


def test_overlapping_relation_is_study_b_to_study_f():
    """A unica relacao de sobreposicao e STUDY_B -> STUDY_F, como related_dataset."""
    path = ROOT / "data" / "literature" / "processed" / "harmonized" / "relations_overlapping_publications.csv"
    df = pd.read_csv(path, dtype=str)
    pair = df.loc[
        (df["source_study_id"] == "STUDY_B") & (df["related_study_id"] == "STUDY_F")
    ]
    assert len(pair) == 1
    assert pair.iloc[0]["relation_type"] == "related_dataset"
    # A relacao e declarada como pendente de confirmacao documental.
    assert "confirma" in pair.iloc[0]["rationale"].lower()


def test_qualitative_evidence_not_flagged_as_duplicate():
    """Evidencias qualitativas STUDY_E (linhas 14 e 15) nao sao duplicatas:
    compartilham tempo/categoria mas descrevem ingredientes distintos."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    df = mod.harmonize_measurements(measurements, evidence, status, studies, "TEST-001")
    duplicates = mod.detect_exact_duplicates(df)
    study_e_dups = [d for d in duplicates if "STUDY_E" in str(d.get("observation_id", ""))]
    assert study_e_dups == [], (
        "Evidencias STUDY_E de ingredientes distintos nao devem ser tratadas como duplicatas"
    )


def test_markdown_report_has_real_newlines():
    """O relatorio Markdown usa quebras de linha reais, nao o literal \\n."""
    _run_script()
    path = ROOT / "data" / "literature" / "processed" / "harmonized" / "harmonization_report.md"
    content = path.read_text(encoding="utf-8")
    assert chr(10) in content, "Markdown deve conter quebras de linha reais"
    assert "\\n" not in content, "Markdown nao deve conter a sequencia literal \\n"


def test_execution_id_is_content_derived():
    """execution_id deriva do conteudo de entrada, nao de relogio."""
    mod = _load_module()
    measurements = pd.read_csv(ROOT / "data" / "literature" / "literature_measurements.csv", dtype=str)
    status = pd.read_csv(ROOT / "data" / "literature" / "literature_verification_status.csv", dtype=str)
    evidence = pd.read_csv(ROOT / "data" / "literature" / "literature_evidence.csv", dtype=str)
    studies = pd.read_csv(ROOT / "data" / "literature" / "literature_studies.csv", dtype=str)

    id1 = mod._compute_execution_id(measurements, evidence, status, studies)
    id2 = mod._compute_execution_id(measurements, evidence, status, studies)
    assert id1 == id2, "execution_id deve ser estavel para o mesmo input"
    assert id1.startswith("F2E1-")



def test_source_locator_class_cedilla_pending() -> None:
    '''Pendencia de conferencia com cedilha (conferência) -> TABLE_OR_FIGURE_PENDING.
    A classificaçao nao deve depender de ausencia de acento.
    '''
    mod = _load_module()
    measurements = pd.DataFrame(
        [
            {'study_id': 'TEST-CEDILLA', 'treatment_id': 'T1', 'source_location': 'Localização exata da tabela no artigo pendente de conferência', 'data_origin': 'PUBLISHED_ARTICLE', 'doi': '', 'value': '1.0', 'value_unit': 'mg/L', 'time_value': '1', 'time_unit': 'd', 'measurement': 'retencao', 'matrix': 'teste'}
        ]
    )
    evidence = pd.DataFrame()
    status = pd.DataFrame()
    studies = pd.DataFrame()
    df = mod.harmonize_measurements(measurements, evidence, status, studies, 'TEST-001')
    assert len(df) == 1
    assert df.iloc[0]['source_locator_class'] == 'TABLE_OR_FIGURE_PENDING'


def test_source_locator_class_specific_reference() -> None:
    '''Localizador explicito (ex.: tabl. 3, col. 2) -> TABLE_OR_FIGURE_REFERENCED.
    Uma referencia especifica nao e considerada pendente de conferencia.
    '''
    mod = _load_module()
    measurements = pd.DataFrame(
        [
            {'study_id': 'TEST-REF', 'treatment_id': 'T1', 'source_location': 'tabl. 3, col. 2', 'data_origin': 'PUBLISHED_ARTICLE', 'doi': '', 'value': '1.0', 'value_unit': 'mg/L', 'time_value': '1', 'time_unit': 'h', 'measurement': 'retencao', 'matrix': 'teste'}
        ]
    )
    evidence = pd.DataFrame()
    status = pd.DataFrame()
    studies = pd.DataFrame()
    df = mod.harmonize_measurements(measurements, evidence, status, studies, 'TEST-001')
    assert len(df) == 1
    assert df.iloc[0]['source_locator_class'] == 'TABLE_OR_FIGURE_REFERENCED'


def test_source_locator_class_totals_on_current_base() -> None:
    '''Base atual: 39 pendentes (medicoes) + 15 referenciados (evidencias) = 54 linhas.'''
    mod = _load_module()
    measurements = pd.read_csv(ROOT / 'data' / 'literature' / 'literature_measurements.csv', dtype=str)
    status = pd.read_csv(ROOT / 'data' / 'literature' / 'literature_verification_status.csv', dtype=str)
    evidence = pd.read_csv(ROOT / 'data' / 'literature' / 'literature_evidence.csv', dtype=str)
    studies = pd.read_csv(ROOT / 'data' / 'literature' / 'literature_studies.csv', dtype=str)
    df = mod.harmonize_measurements(measurements, evidence, status, studies, 'TEST-001')
    pending = int((df['source_locator_class'] == 'TABLE_OR_FIGURE_PENDING').sum())
    referenced = int((df['source_locator_class'] == 'TABLE_OR_FIGURE_REFERENCED').sum())
    no_locator = int((df['source_locator_class'] == 'NO_SOURCE_LOCATOR').sum())
    assert pending == 39, 'Esperado 39 pendentes, obteve ' + str(pending)
    assert referenced == 15, 'Esperado 15 referenciados, obteve ' + str(referenced)
    assert no_locator == 0

if __name__ == "__main__":
    import unittest
    unittest.main()

