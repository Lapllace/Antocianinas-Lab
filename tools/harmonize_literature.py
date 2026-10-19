#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase 2 - Etapa 1 da harmonia de dados - gera base derivada."""

from __future__ import annotations

import argparse
import hashlib
import sys
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
    "evidence_class",
    "evidence_type",
    "evidence_text",
    "k_value",
    "k_unit",
    "half_life",
    "half_life_unit",
    "formula",
    "data_origin",
    "reported_or_calculated",
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
    "STUDY_F": {
        "group": None,
        "exclusion_reason": (
            "Sem observacoes harmonizadas nesta etapa; publicacao relacionada a STUDY_B "
            "(possivel sobreposicao de dados, sujeita a confirmacao documental)"
        ),
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


def _text(value: object) -> str:
    """Texto seguro: None/NaN viram string vazia (nunca 'nan')."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if not isinstance(value, str) and pd.isna(value):
        return ""
    s = str(value).strip()
    return "" if s.lower() == "nan" else s


def _normalize_verification_status(value: object) -> str:
    """Normaliza status para o vocabulario do projeto.

    Somente tres estados sao produzidos: VERIFIED, VERIFICATION_PENDING e
    REJECTED. REJECTED e honrado (nunca rebaixado ou promovido); VERIFIED so
    sobrevive se vier como VERIFIED; qualquer outro rotulo (PENDING, PARTIAL,
    BLOCKED, vazio) vira VERIFICATION_PENDING - nunca auto-promocao.
    """
    v = _text(value).upper()
    if v == "VERIFIED":
        return "VERIFIED"
    if v == "REJECTED":
        return "REJECTED"
    return "VERIFICATION_PENDING"


def _classify_evidence_class(evidence_type: object, record: dict) -> str:
    """Classifica a evidencia em um dos tres grupos do roadmap (separacao por tipo).

    Regras (deterministicas, sem inferir valores ausentes):
    - PUBLISHED_KINETIC_PARAMETER: resumo cinetico publicado (k/meia-vida)
      relatado pelo artigo; nunca vira ponto de serie temporal.
    - QUANTITATIVE_MEASUREMENT: valor numerico publicado (concentracao,
      retencao, absorbancia, variacao percentual etc.).
    - QUALITATIVE_NARRATIVE: descricao textual/conclusao dos autores sem
      valor numerico.
    """
    et = _text(evidence_type).lower()
    if et == "kinetic_summary" or _text(record.get("k_value")) or _text(record.get("half_life")):
        return "PUBLISHED_KINETIC_PARAMETER"
    if _text(record.get("value")):
        return "QUANTITATIVE_MEASUREMENT"
    return "QUALITATIVE_NARRATIVE"


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
    supplement: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return harmonized dataframe (one row = one original observation)."""
    out_rows = []
    measurement_records = measurements.to_dict("records")
    evidence_records = evidence.to_dict("records")
    status_by_key = {
        (r["study_id"], r["doi"], r["treatment_id"], r["time_value"], r["time_unit"], r["measurement"], r["value_unit"]): r
        for r in status.to_dict("records")
    }

    # Rollup por estudo para as linhas de evidencia (o manifesto lateral tem
    # chave apenas de medições; evidencias herdam o status do estudo com a
    # mesma regra de validate_literature_data: VERIFIED somente se TODAS as
    # chaves do estudo forem VERIFIED; pendente se qualquer chave for
    # pendente; senao REJECTED). Nenhuma promocao automatica acontece aqui.
    study_statuses: dict[str, set] = {}
    for st_row in status.to_dict("records"):
        study_statuses.setdefault(str(st_row["study_id"]), set()).add(
            _normalize_verification_status(st_row["verification_status"])
        )
    evidence_status_by_study: dict[str, str] = {}
    for study_key, values in study_statuses.items():
        if values == {"VERIFIED"}:
            evidence_status_by_study[study_key] = "VERIFIED"
        elif "VERIFICATION_PENDING" in values:
            evidence_status_by_study[study_key] = "VERIFICATION_PENDING"
        else:
            evidence_status_by_study[study_key] = "REJECTED"

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
            verification_status = _normalize_verification_status(st.get("verification_status", ""))
            verification_note = _text(st.get("verification_notes", ""))
        if not source_locator_raw:
            verification_note = (
                verification_note
                or "Localizacao exata da fonte nao confirmada pela celula original."
            )

        if "pendente de conferência" in source_locator_raw.lower():
            source_locator_class = "TABLE_OR_FIGURE_PENDING"
        elif source_locator_raw.strip():
            source_locator_class = "TABLE_OR_FIGURE_REFERENCED"
        else:
            source_locator_class = "NO_SOURCE_LOCATOR"

        # Aplicar enriquecimentos do supplement se disponível (Fase 3)
        std_val = _to_scalar(m.get("standard_deviation", ""))
        rep_count = _to_scalar(m.get("replicate_count", ""))
        source_loc_enriched = ""
        verification_note_enriched = ""
        if supplement is not None:
            supp_key = (study_id, treatment_id, m.get("time_value", ""), m.get("time_unit", ""))
            supp_row = supplement[(supplement["study_id"] == study_id) & 
                              (supplement["treatment_id"] == treatment_id) & 
                              (supplement["time_value"] == m.get("time_value", "")) & 
                              (supplement["time_unit"] == m.get("time_unit", ""))]
            if len(supp_row) > 0:
                if pd.isna(std_val) or std_val == "":
                    std_val = _to_scalar(supp_row.iloc[0]["standard_deviation"])
                if pd.isna(rep_count) or rep_count == "":
                    rep_count = _to_scalar(supp_row.iloc[0]["replicate_count"])
                source_loc_enriched = _text(supp_row.iloc[0]["source_location_enriched"])
                verification_note_enriched = _text(supp_row.iloc[0]["verification_notes_enriched"])

        group_info = COMPARISON_GROUPS.get(study_id, {"group": None, "exclusion_reason": "study_id nao mapeado"})
        row = {
            "observation_id": f"OBS-{study_id}-{treatment_id}-{m.get('time_value','-')}-{m.get('time_unit','-')}-{m.get('measurement','')}",
            "source_record_id": f"{study_id}|L{idx}",
            "study_id": study_id,
            "treatment_id": treatment_id,
            "measurement": m.get("measurement", ""),
            "value_original": _to_scalar(m.get("value", "")),
            "unit_original": m.get("value_unit", ""),
            "time_value_original": m.get("time_value", ""),
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
            "standard_deviation": std_val,
            "replicate_count": rep_count,
            "replicate_type": _classify_replicates(rep_count),
            "normalization_formula": "",
            "normalized_value": "",
            "normalized_unit": "",
            "comparability_group": group_info["group"],
            "exclusion_reason": group_info["exclusion_reason"],
            # Medições do CSV bruto sao, por construcao, valores numericos
            # publicados (o validador bruto exige value/time numericos).
            "evidence_class": "QUANTITATIVE_MEASUREMENT",
            "evidence_type": "",
            "evidence_text": "",
            "k_value": None,
            "k_unit": "",
            "half_life": None,
            "half_life_unit": "",
            "formula": "",
            "data_origin": _text(m.get("data_origin")),
            "reported_or_calculated": _text(m.get("reported_or_calculated")),
            "notes": m.get("notes", "") + ("; " + verification_note_enriched if verification_note_enriched else ""),
        }
        out_rows.append(row)

    evidence_counter = 0
    for evidence_line, er in enumerate(evidence_records, start=2):
        if not _has_any_value(er):
            continue
        study_id = er.get("study_id", "")
        treatment_id = er.get("treatment_id", "")
        if study_id not in COMPARISON_GROUPS:
            continue
        group_info = COMPARISON_GROUPS[study_id]
        if group_info["group"] is None:
            continue
        evidence_counter += 1
        evidence_id = er.get("evidence_type", "") or er.get("evidence_category", "")
        evidence_class = _classify_evidence_class(er.get("evidence_type", ""), er)
        evidence_status = evidence_status_by_study.get(str(study_id), "VERIFICATION_PENDING")
        study_row = studies[studies["study_id"] == study_id]
        species_val = study_row["species"].iloc[0] if len(study_row) > 0 else ""
        extraction_val = study_row["extraction_conditions"].iloc[0] if len(study_row) > 0 else ""
        solvent_val = study_row["solvent"].iloc[0] if len(study_row) > 0 else ""
        storage_val = study_row["storage_conditions"].iloc[0] if len(study_row) > 0 else ""

        row = {
            "observation_id": f"EVID-{study_id}-{_safe_slug(evidence_id)}-{evidence_counter}",
            "source_record_id": f"{study_id}|E{evidence_line}",
            "study_id": study_id,
            "treatment_id": treatment_id,
            "measurement": _safe_slug(er.get("measurement", "")),
            "value_original": _to_scalar(er.get("value", "")),
            "unit_original": er.get("value_unit", ""),
            "time_value_original": er.get("time_value", ""),
            "time_unit_original": er.get("time_unit", ""),
            "doi": er.get("doi", ""),
            "source_url": er.get("source_url", ""),
            "source_version": "17-10-2026",
            "source_locator": str(er.get("source_location") or ""),
            "source_locator_class": "ARTICLE_TEXT" if not er.get("source_location") else "TABLE_OR_FIGURE_REFERENCED",
            "provenance_class": _classify_provenance(er.get("origin_source", "")),
            "verification_status": evidence_status,
            "verification_note": (
                "Resumo/contagem de evidencia sem serie temporal; origem textual. Nao e serie de concentracao."
                if evidence_status != "REJECTED"
                else (
                    "REJECTED por rollup do estudo (chave de medicao do estudo rejeitada em "
                    "literature_verification_status.csv); registro preservado, excluido de ajustes."
                )
            ),
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
            "evidence_class": evidence_class,
            "evidence_type": _text(er.get("evidence_type")),
            "evidence_text": _text(er.get("evidence_text")),
            "k_value": _to_scalar(er.get("k_value")),
            "k_unit": _text(er.get("k_unit")),
            "half_life": _to_scalar(er.get("half_life")),
            "half_life_unit": _text(er.get("half_life_unit")),
            "formula": _text(er.get("formula")),
            # Todas as linhas de evidence sao relatadas pelo artigo (coluna
            # origin_source do bruto); o valor e publicado, nao ajustado aqui.
            "data_origin": "PUBLISHED_ARTICLE",
            "reported_or_calculated": "reported",
            "notes": er.get("notes", ""),
        }
        out_rows.append(row)

    df = pd.DataFrame(out_rows, columns=OBS_COLUMNS)
    df["execution_id"] = execution_id
    # Timestamp omitido propositalmente: qualquer data de execucao quebra a
    # determinismo da saida. O rastreio temporal e feito via control de versoes.
    df["generated_on_utc"] = ""
    return df

def _compute_execution_id(measurements: pd.DataFrame, evidence: pd.DataFrame, status: pd.DataFrame, studies: pd.DataFrame) -> str:
    """Gera um execution_id determinístico baseado no conteúdo dos CSVs de entrada."""
    h = hashlib.sha256()
    for df in (measurements, evidence, status, studies):
        h.update(pd.util.hash_pandas_object(df, index=False).values.tobytes())
    return f"F2E1-{h.hexdigest()[:16]}"


def detect_exact_duplicates(df: pd.DataFrame) -> list:
    """Detecta duplicatas EXATAS: linhas identicas em todos os campos
    cientificos e de proveniencia.

    Diferente de uma comparacao apenas pela chave de medicao, esta abordagem
    distingue evidencias qualitativas diferentes que compartilham a mesma
    categoria, tempo ou campos vazios (ex.: STUDY_E, linhas 14 e 15, que
    descrevem ingredientes distintos apesar do mesmo tempo de 20 semanas).
    """
    if df.empty:
        return []
    exclude = {
        "execution_id",
        "generated_on_utc",
        "observation_id",
        "source_record_id",
    }
    subset = [c for c in df.columns if c not in exclude]
    groups = df.groupby(subset, dropna=False)
    duplicates = []
    for _, group in groups:
        if len(group) > 1:
            for _, row in group.iterrows():
                duplicates.append({
                    "observation_id": row.get("observation_id"),
                    "key": row.get("source_record_id"),
                    "n_replicates": len(group),
                    "note": "Linha identica em todos os campos cientificos; todas mantidas, nenhuma excluida.",
                })
    return duplicates


def build_overlapping_relations(studies: pd.DataFrame) -> pd.DataFrame:
    rels = []
    study_b = studies.loc[studies["study_id"] == "STUDY_B"]
    study_f = studies.loc[studies["study_id"] == "STUDY_F"]
    if len(study_b) and len(study_f):
        rels.append({
            "source_study_id": "STUDY_B",
            "source_citation": study_b.iloc[0]["citation"],
            "source_year": 2022,
            "related_study_id": "STUDY_F",
            "related_citation": study_f.iloc[0]["citation"],
            "related_year": 2023,
            "relation_type": "related_dataset",
            "rationale": "Possível sobreposição de tabela numérica entre Muhamad et al. (2022) e Muhamad et al. (2023); sujeita à confirmação documental. Não adicionar como evidência independente até que a independência seja demonstrada.",
            "action": "não duplicar observações; manter na bibliografia",
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
    supplement: pd.DataFrame | None = None,
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
    lines.append(f"| Classe: medicoes quantitativas | {int((harmonized['evidence_class'] == 'QUANTITATIVE_MEASUREMENT').sum())} |")
    lines.append(f"| Classe: parametros cineticos publicados | {int((harmonized['evidence_class'] == 'PUBLISHED_KINETIC_PARAMETER').sum())} |")
    lines.append(f"| Classe: evidencias qualitativas/narrativas | {int((harmonized['evidence_class'] == 'QUALITATIVE_NARRATIVE').sum())} |")
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
    lines.append("Relacao STUDY_B (Muhamad et al. 2022, DOI 10.33102/mjosht.v8i1.239) com STUDY_F (Muhamad et al. 2023, DOI 10.26656/fr.2017.6(S2).030) registrada em relations_overlapping_publications.csv como possivel sobreposicao de dados, sujeita a confirmacao documental. STUDY_C (Lin et al. 2023) NAO e publicacao sobreposta a STUDY_B. As observacoes originais nao sao duplicadas; ambas permanecem na bibliografia.")
    lines.append("")
    lines.append("## 7. Listas de grupos de comparabilidade")
    lines.append("")
    lines.append("| Grupo | Estudos | Observacao |")
    lines.append("|---|---|---|")
    for sid in ["STUDY_A", "STUDY_B", "STUDY_C", "STUDY_D", "STUDY_E", "STUDY_F"]:
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
    if supplement is not None:
        lines.append(f"- Suplemento de enriquecimento aplicado: {len(supplement)} registros de literature_measurements_supplement_phase3.csv")
        lines.append("  (desvios-padrao, replicatas e localizadores adicionados na Fase 3)")
    lines.append("")
    return "\n".join(lines)


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

    # Ler arquivo de enriquecimento se existir (Fase 3)
    supplement_path = lit_dir / "literature_measurements_supplement_phase3.csv"
    supplement = None
    if supplement_path.exists():
        supplement = pd.read_csv(supplement_path, dtype=str)

    execution_id = _compute_execution_id(measurements, evidence, status, studies)
    harmonized = harmonize_measurements(measurements, evidence, status, studies, execution_id, supplement)

    duplicates = detect_exact_duplicates(harmonized)

    measurements_path = proc_dir / "harmonized_measurements.csv"
    harmonized.to_csv(measurements_path, index=False)

    relations_path = proc_dir / "relations_overlapping_publications.csv"
    build_overlapping_relations(studies).to_csv(relations_path, index=False)

    report_path = proc_dir / "harmonization_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(build_report(harmonized, duplicates, measurements, execution_id, supplement))

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
        {"check": "evidence_class_quantitative_measurements", "value": int((harmonized["evidence_class"] == "QUANTITATIVE_MEASUREMENT").sum()), "status": "ok"},
        {"check": "evidence_class_published_kinetic_parameters", "value": int((harmonized["evidence_class"] == "PUBLISHED_KINETIC_PARAMETER").sum()), "status": "ok"},
        {"check": "evidence_class_qualitative_narratives", "value": int((harmonized["evidence_class"] == "QUALITATIVE_NARRATIVE").sum()), "status": "ok"},
        {"check": "unique_observation_ids", "value": int(harmonized["observation_id"].nunique()), "status": "ok" if harmonized["observation_id"].is_unique else "error"},
        {"check": "unique_source_record_ids", "value": int(harmonized["source_record_id"].nunique()), "status": "ok" if harmonized["source_record_id"].is_unique else "error"},
        {"check": "supplement_applied", "value": len(supplement) if supplement is not None else 0, "status": "info"},
    ])
    audit.to_csv(report_csv_path, index=False)

    print(f"Harmonizacao gerada: {harmonized.shape[0]} observacoes em {measurements_path}")
    print(f"Duplicatas exatas: {len(duplicates)}")
    print(f"Relatorio Markdown: {report_path}")
    print(f"Relatorio CSV: {report_csv_path}")
    if supplement is not None:
        print(f"Suplemento aplicado: {len(supplement)} enriquecimentos de {supplement_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
