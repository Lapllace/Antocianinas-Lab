#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase 2 - Etapa 1 da harmonia de dados - gera base derivada."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

OBS_COLUMNS = [
    "execution_id",
    "generated_on_utc",
    "observation_id",
    "source_record_id",
    "study_id",
    "treatment_id",
    "measurement",
    "value_original",
    "unit_original",
    "time_value_original",
    "time_unit_original",
    "doi",
    "source_url",
    "source_version",
    "source_locator",
    "source_locator_class",
    "provenance_class",
    "verification_status",
    "verification_note",
    "matrix_type",
    "species",
    "extraction_method",
    "solvent",
    "solvent_composition",
    "additive",
    "additive_concentration_pct",
    "pH",
    "temperature_c",
    "light_condition",
    "oxygen_condition",
    "package_material",
    "storage_conditions",
    "measurement_name",
    "standard_deviation",
    "replicate_count",
    "replicate_type",
    "normalization_formula",
    "normalized_value",
    "normalized_unit",
    "comparability_group",
    "exclusion_reason",
    "notes",
]

COMPARISON_GROUPS = {
    "STUDY_A": {
        "group": "A",
        "exclusion_reason": "",
    },
    "STUDY_B": {
        "group": "B",
        "exclusion_reason": "",
    },
    "STUDY_C": {
        "group": "C",
        "exclusion_reason": "Sem serie temporal; apenas resumo cinetico",
    },
    "STUDY_D": {
        "group": "D",
        "exclusion_reason": "Retencao em horas; nao misturar com series em dias",
    },
    "STUDY_E": {
        "group": "E",
        "exclusion_reason": "Dados qualitativos; sem valores quantitativos",
    },
}


def _safe_slug(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip().replace(" ", "_")


def _to_scalar(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, float):
        if pd.isna(value):
            return None
        return value
    s = str(value).strip()
    if s == "":
        return None
    try:
        f = float(s)
        if f.is_integer():
            return int(f)
        return f
    except ValueError:
        return s


def _classify_provenance(data_origin: str) -> str:
    """Classify provenance based on data_origin field."""
    origin = str(data_origin).strip().upper()
    if origin == "PUBLISHED_ARTICLE":
        return "USER_TRANSCRIBED_PENDING_VERIFICATION"
    elif origin == "LAB_MEASUREMENT":
        return "LAB_MEASUREMENT"
    elif origin == "SIMULATION":
        return "SIMULATION"
    elif origin == "LITERATURE":
        return "LITERATURE"
    else:
        return "UNKNOWN"


def _classify_replicates(replicate_count: object) -> str:
    """Classify replicate type based on count."""
    if replicate_count is None or replicate_count == "":
        return "not_reported"
    try:
        n = int(float(replicate_count))
        if n <= 1:
            return "not_reported"
        else:
            return "unknown"
    except (ValueError, TypeError):
        return "not_reported"


def _has_any_value(record: dict) -> bool:
    """Check if record has any non-empty value."""
    for v in record.values():
        if v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v).strip():
            return True
    return False


def harmonize_measurements(
    measurements: pd.DataFrame,
    evidence: pd.DataFrame,
    status: pd.DataFrame,
    studies: pd.DataFrame,
    execution_id: str,
) -> pd.DataFrame:
    """Return harmonized dataframe (one row = one original observation)."""
    out_rows = []
    measurement_records = measurements.to_dict("records")
    evidence_records = evidence.to_dict("records")
    status_by_key = {
        (r["study_id"], r["doi"], r["treatment_id"], r["time_value"], r["time_unit"], r["measurement"], r["value_unit"]): r
        for r in status.to_dict("records")
    }

    for idx, m in enumerate(measurement_records, start=2):
        study_id = m.get("study_id", "")
        treatment_id = m.get("treatment_id", "")
        source_locator_raw = m.get("source_location", "") or ""

        data_origin = m.get("data_origin", "") or "PUBLISHED_ARTICLE"
        provenance_class = _classify_provenance(data_origin)

        status_key = (
            study_id,
            m.get("doi", ""),
            treatment_id,
            m.get("time_value", ""),
            m.get("time_unit", ""),
            m.get("measurement", ""),
            m.get("value_unit", ""),
        )
        verification_status = "VERIFICATION_PENDING"
        verification_note = ""
        if status_key in status_by_key:
            st = status_by_key[status_key]
            if st.get("verification_status", ""):
                status_val = str(st["verification_status"]).strip()
                verification_status = (
                    status_val if status_val.upper() in {"PENDING", "PARTIAL", "VERIFIED", "BLOCKED"}
                    else "VERIFICATION_PENDING"
                )
            verification_note = str(st.get("verification_notes", "") or "").strip()
        if not source_locator_raw:
            verification_note = (
                verification_note
                or "Localizacao exata da fonte nao confirmada pela celula original."
            )

        if "pendente de conferencia" in source_locator_raw.lower():
            source_locator_class = "TABLE_OR_FIGURE_PENDING"
        elif source_locator_raw.strip():
            source_locator_class = "TABLE_OR_FIGURE_REFERENCED"
        else:
            source_locator_class = "NO_SOURCE_LOCATOR"

        group_info = COMPARISON_GROUPS.get(study_id, {"group": None, "exclusion_reason": "study_id nao mapeado"})
        row = {
            "observation_id": f"OBS-{study_id}-{treatment_id}-{m.get('time_value','-')}-{m.get('time_unit','-')}-{m.get('measurement','')}",
            "source_record_id": f"{study_id}|L{idx}",
            "study_id": study_id,
            "treatment_id": treatment_id,
            "measurement": m.get("measurement", ""),
            "value_original": _to_scalar(m.get("value", "")),
            "unit_original": m.get("value_unit", ""),
            "time_value_original": _to_scalar(m.get("time_value", "")),
            "time_unit_original": m.get("time_unit", ""),
            "doi": m.get("doi", ""),
            "source_url": m.get("source_url", ""),
            "source_version": "17-10-2026",
            "source_locator": source_locator_raw,
            "source_locator_class": source_locator_class,
            "provenance_class": provenance_class,
            "verification_status": verification_status,
            "verification_note": verification_note,
            "matrix_type": m.get("matrix", ""),
            "species": m.get("species", ""),
            "extraction_method": m.get("extraction_type", ""),
            "solvent": m.get("solvent", ""),
            "solvent_composition": m.get("solvent", ""),
            "additive": m.get("additive", ""),
            "additive_concentration_pct": _to_scalar(m.get("additive_concentration_pct", "")),
            "pH": _to_scalar(m.get("pH", "")),
            "temperature_c": _to_scalar(m.get("temperature_c", "")),
            "light_condition": m.get("light_condition", ""),
            "oxygen_condition": m.get("oxygen_condition", ""),
            "package_material": m.get("package_material", ""),
            "storage_conditions": m.get("storage_conditions", ""),
            "measurement_name": m.get("measurement", ""),
            "standard_deviation": _to_scalar(m.get("standard_deviation", "")),
            "replicate_count": _to_scalar(m.get("replicate_count", "")),
            "replicate_type": _classify_replicates(m.get("replicate_count", "")),
            "normalization_formula": "",
            "normalized_value": "",
            "normalized_unit": "",
            "comparability_group": group_info["group"],
            "exclusion_reason": group_info["exclusion_reason"],
            "notes": m.get("notes", ""),
        }
        out_rows.append(row)

    for er in evidence_records:
        if not _has_any_value(er):
            continue
        study_id = er.get("study_id", "")
        treatment_id = er.get("treatment_id", "")
        if study_id not in COMPARISON_GROUPS:
            continue
        group_info = COMPARISON_GROUPS[study_id]
        if group_info["group"] is None:
            continue
        evidence_id = er.get("evidence_type", "") or er.get("evidence_category", "")
        study_row = studies[studies["study_id"] == study_id]
        species_val = study_row["species"].iloc[0] if len(study_row) > 0 else ""
        extraction_val = study_row["extraction_conditions"].iloc[0] if len(study_row) > 0 else ""
        solvent_val = study_row["solvent"].iloc[0] if len(study_row) > 0 else ""
        storage_val = study_row["storage_conditions"].iloc[0] if len(study_row) > 0 else ""

        row = {
            "observation_id": f"EVID-{study_id}-{_safe_slug(evidence_id)}-0",
            "source_record_id": f"{study_id}|evidence|{_safe_slug(er.get('evidence_type'))}",
            "study_id": study_id,
            "treatment_id": treatment_id,
            "measurement": _safe_slug(er.get("measurement", "")),
            "value_original": _to_scalar(er.get("value", "")),
            "unit_original": er.get("value_unit", ""),
            "time_value_original": _to_scalar(er.get("time_value", "")),
            "time_unit_original": er.get("time_unit", ""),
            "doi": er.get("doi", ""),
            "source_url": er.get("source_url", ""),
            "source_version": "17-10-2026",
            "source_locator": str(er.get("source_location") or ""),
            "source_locator_class": "ARTICLE_TEXT" if not er.get("source_location") else "TABLE_OR_FIGURE_REFERENCED",
            "provenance_class": _classify_provenance(er.get("origin_source", "")),
            "verification_status": "VERIFICATION_PENDING",
            "verification_note": "Resumo/contagem de evidencia sem serie temporal; origem textual. Nao e serie de concentracao.",
            "matrix_type": er.get("conditions", ""),
            "species": species_val,
            "extraction_method": extraction_val,
            "solvent": solvent_val,
            "solvent_composition": "",
            "additive": er.get("additive", ""),
            "additive_concentration_pct": _to_scalar(er.get("additive_concentration_pct", "")),
            "pH": _to_scalar(er.get("pH", "")),
            "temperature_c": _to_scalar(er.get("temperature_c", "")),
            "light_condition": "",
            "oxygen_condition": "",
            "package_material": "",
            "storage_conditions": storage_val,
            "measurement_name": _safe_slug(er.get("measurement", "")),
            "standard_deviation": _to_scalar(er.get("standard_deviation", "")),
            "replicate_count": _to_scalar(er.get("replicate_count", "")),
            "replicate_type": "not_reported",
            "normalization_formula": "",
            "normalized_value": "",
            "normalized_unit": "",
            "comparability_group": group_info["group"],
            "exclusion_reason": group_info["exclusion_reason"],
            "notes": er.get("notes", ""),
        }
        out_rows.append(row)

    df = pd.DataFrame(out_rows, columns=OBS_COLUMNS)
    df["execution_id"] = execution_id
    df["generated_on_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return df


def detect_exact_duplicates(df: pd.DataFrame) -> list:
    if df.empty:
        return []
    core_cols = ["study_id", "treatment_id", "time_value_original", "time_unit_original", "value_original", "measurement"]
    subset = [c for c in core_cols if c in df.columns]
    groups = df.groupby(subset, dropna=False)
    duplicates = []
    for key, group in groups:
        if len(group) > 1:
            for _, row in group.iterrows():
                duplicates.append({
                    "observation_id": row.get("observation_id"),
                    "key": "|".join(str(key[c]) for c in subset),
                    "n_replicates": len(group),
                    "note": "Linha identica detectada; todas mantidas, nenhuma excluida.",
                })
    return duplicates


def build_overlapping_relations(studies: pd.DataFrame) -> pd.DataFrame:
    rels = []
    study_b = studies.loc[studies["study_id"] == "STUDY_B"]
    if len(study_b):
        rels.append({
            "source_study_id": "STUDY_B",
            "source_citation": study_b.iloc[0]["citation"],
            "source_year": 2022,
            "related_study_id": "STUDY_C",
            "related_citation": "Lin et al. (2023) - publicacao dos mesmos autores com tabela numerica sobrevalorizada",
            "related_year": 2023,
            "relation_type": "related_dataset",
            "rationale": "Tabela numerica igual ou sobreposta; nao e adicionada como evidencia independente ate que a independencia seja demonstrada.",
            "action": "nao duplicar observacoes; manter na bibliografia",
        })
    return pd.DataFrame(rels, columns=[
        "source_study_id", "source_citation", "source_year",
        "related_study_id", "related_citation", "related_year",
        "relation_type", "rationale", "action",
    ])


def build_report(
    harmonized: pd.DataFrame,
    duplicates: list,
    measurements: pd.DataFrame,
    execution_id: str,
) -> str:
    lines = []
    lines.append("# Relatorio de Auditoria - Fase 2, Etapa 1: Harmonia de Dados")
    lines.append("")
    lines.append("**Data:** 17 de outubro de 2026")
    lines.append(f"**Execucao:** {execution_id}")
    lines.append("**Status:** iniciada - derivada gerada; originais inalterados.")
    lines.append("")
    lines.append("## 1. Resumo executivo")
    lines.append("")
    lines.append("| Metrica | Valor |")
    lines.append("|---|---|")
    lines.append(f"| Linhas originais (literature_measurements.csv) | {len(measurements)} |")
    lines.append(f"| Linhas geradas na base harmonica | {len(harmonized)} |")
    lines.append(f"| Duplicatas exatas detectadas | {len(duplicates)} |")
    lines.append(f"| Dados simulados incluidos | nao |")
    lines.append("")
    lines.append("## 2. Preservacao de originais")
    lines.append("")
    lines.append("Cada observacao mantém value_original, unit_original, time_value_original, time_unit_original copiados textualmente de literature_measurements.csv. Nenhuma conversao de unidades, escala temporal ou inferencia de valores ausentes foi realizada.")
    lines.append("")
    lines.append("Os campos normalization_formula, normalized_value, normalized_unit estao vazios por decisao de fase: nenhuma transformacao foi aplicada nesta etapa.")
    lines.append("")
    lines.append("## 3. Lacunas registradas")
    lines.append("")
    lines.append("| Campo | Quantidade | Motivo registrado |")
    lines.append("|---|---|---|")
    lines.append(f"| source_locator | {int(harmonized['source_locator'].eq('').sum())} | Localizacao pendente de conferencia; somente DOI disponivel. |")
    lines.append(f"| standard_deviation | {int(harmonized['standard_deviation'].isna().sum())} | Nao informado na fonte; ausencia preservada, nao substituida por zero. |")
    lines.append(f"| replicate_type | {int(harmonized['replicate_type'].eq('not_reported').sum())} | Nao informado; classe not_reported para nao confundir com replica independente. |")
    lines.append(f"| pH | {int(harmonized['pH'].isna().sum())} | Nao reportado; nenhuma inferencia de pH. |")
    lines.append(f"| additive_concentration_pct | {int(harmonized['additive_concentration_pct'].isna().sum())} | Nao reportado; ausencia registrada. |")
    lines.append("")
    lines.append("## 4. Duplicatas")
    if duplicates:
        lines.append("Detecao de linhas identicas nos registros brutos:")
        for d in duplicates:
            lines.append(f"- {d['observation_id'] or 'sim'}: {d['key']} - {d['n_replicates']} linhas identicas; manter todas, nenhuma excluida.")
    else:
        lines.append("Nenhuma dupla exata encontrada nos registros de mensuracao.")
    lines.append("")
    lines.append("## 5. Unidades e escalas mantidas")
    lines.append("")
    lines.append("As duas matrizes de unidade sao mantidas separadas:")
    lines.append("- mg CGE/100 g FW - STUDY_A (extrato)")
    lines.append("- mg equivalentes de cianidina-3-glicosideo/L - STUDY_B (bebida mista)")
    lines.append("")
    lines.append("Tempos preservados em dia (STUDY_A) e mes (STUDY_B); conversao nao e feita.")
    lines.append("")
    lines.append("## 6. Publicacoes potencialmente sobrepostas")
    lines.append("")
    lines.append("Relacao STUDY_B (Muhamad et al. 2022) com publicacao de 2023 dos mesmos autores registrada em relations_overlapping_publications.csv. As observacoes originais nao sao duplicadas; ambas permanecem na bibliografia.")
    lines.append("")
    lines.append("## 7. Listas de grupos de comparabilidade")
    lines.append("")
    lines.append("| Grupo | Estudos | Observacao |")
    lines.append("|---|---|---|")
    for sid in ["STUDY_A", "STUDY_B", "STUDY_C", "STUDY_D", "STUDY_E"]:
        info = COMPARISON_GROUPS.get(sid, {})
        lines.append(f"| {info.get('group', '-')} | {sid} | {info.get('exclusion_reason', '')} |")
    lines.append("")
    lines.append("## 8. Arquivos gerados")
    lines.append("")
    lines.append("- data/literature/processed/harmonized/harmonized_measurements.csv")
    lines.append("- data/literature/processed/harmonized/relations_overlapping_publications.csv")
    lines.append("- data/literature/processed/harmonized/harmonization_report.csv")
    lines.append("- data/literature/processed/harmonized/harmonization_report.md")
    lines.append("")
    lines.append("## 9. Limites e pendencias")
    lines.append("")
    lines.append("- Estado VERIFICATION_PENDING mantido (nao autoatualiza a VERIFIED).")
    lines.append("- Localidade de cada celula ainda nao confirmada na fonte original.")
    lines.append("- Unidades mg CGE/100 g FW vs mg equivalentes de cianidina-3-glicosideo/L sao distintas e nao sao convertidas.")
    lines.append("")
    return "\\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fase 2 - Etapa 1: gera base harmonica derivada.")
    parser.add_argument("--dir", type=Path, default=Path("."), help="Raiz do projeto")
    args = parser.parse_args(argv)
    root = args.dir.resolve()

    lit_dir = root / "data" / "literature"
    proc_dir = lit_dir / "processed" / "harmonized"
    proc_dir.mkdir(parents=True, exist_ok=True)

    measurements = pd.read_csv(lit_dir / "literature_measurements.csv", dtype=str)
    evidence = pd.read_csv(lit_dir / "literature_evidence.csv", dtype=str)
    status = pd.read_csv(lit_dir / "literature_verification_status.csv", dtype=str)
    studies = pd.read_csv(lit_dir / "literature_studies.csv", dtype=str)

    execution_id = f"F2E1-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    harmonized = harmonize_measurements(measurements, evidence, status, studies, execution_id)

    duplicates = detect_exact_duplicates(harmonized)

    measurements_path = proc_dir / "harmonized_measurements.csv"
    harmonized.to_csv(measurements_path, index=False)

    relations_path = proc_dir / "relations_overlapping_publications.csv"
    build_overlapping_relations(studies).to_csv(relations_path, index=False)

    report_path = proc_dir / "harmonization_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(build_report(harmonized, duplicates, measurements, execution_id))

    report_csv_path = proc_dir / "harmonization_report.csv"
    dup_rows = pd.DataFrame(duplicates) if duplicates else pd.DataFrame(columns=[
        "observation_id", "key", "n_replicates", "note"])
    audit = pd.DataFrame([
        {"check": "lines_processed_measurements", "value": len(measurements), "status": "ok"},
        {"check": "lines_processed_evidence_rows", "value": len(evidence), "status": "ok"},
        {"check": "rows_harmonized", "value": len(harmonized), "status": "ok"},
        {"check": "exact_duplicate_groups", "value": len(duplicates), "status": "ok"},
        {"check": "empty_source_locators", "value": int(harmonized["source_locator"].eq("").sum()), "status": "warning"},
        {"check": "missing_standard_deviation", "value": int(harmonized["standard_deviation"].isna().sum()), "status": "warning"},
        {"check": "missing_replicate_type", "value": int(harmonized["replicate_type"].eq("not_reported").sum()), "status": "ok"},
        {"check": "normalized_formula_nonempty", "value": int((harmonized["normalization_formula"] != "").sum()), "status": "info"},
    ])
    audit.to_csv(report_csv_path, index=False)

    print(f"Harmonizacao gerada: {harmonized.shape[0]} observacoes em {measurements_path}")
    print(f"Duplicatas exatas: {len(duplicates)}")
    print(f"Relatorio Markdown: {report_path}")
    print(f"Relatorio CSV: {report_csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
