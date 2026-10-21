"""Importação assistida de dados experimentais.

Camada de lógica (independente de Streamlit) que prepara a importação de
medições experimentais a partir de arquivos CSV/XLSX ou de tabelas coladas,
mapeia colunas de origem para os campos dos esquemas existentes e produz
uma prévia validada antes de qualquer gravação.

Reutiliza os validadores, as chaves de duplicidade e o mecanismo de
persistência de :mod:`anthocyanin_persistence`; não duplica a lógica de
gravação nem altera os cálculos científicos.

A interface é organizada em estágios — interpretar a origem, mapear
colunas, validar a prévia — para permitir, no futuro, uma camada de
interpretação em linguagem natural sobre a mesma fronteira, sem integrar
um modelo de linguagem nesta etapa (nenhuma dependência de IA é usada).

Regras de integridade:

* importa apenas medições experimentais nos esquemas atuais
  (estabilidade, cor, microbiologia);
* não insere referências bibliográficas nem resultados simulados;
* preserva valores e unidades de origem — nada é corrigido, convertido
  ou preenchido silenciosamente;
* nenhuma linha é gravada antes da confirmação explícita (a gravação
  fica a cargo de :func:`anthocyanin_persistence.append_row_safely`).
"""

from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

import pandas as pd

import anthocyanin_persistence as persist

# Tipos de registro suportados pela importação assistida (esquemas atuais).
RECORD_TYPES = ("stability", "color", "micro")

# Rótulos legíveis para a interface.
RECORD_LABELS = {
    "stability": "Estabilidade",
    "color": "Cor",
    "micro": "Microbiologia",
}

# Configuração de cada tipo, reutilizando os contratos de persistência.
_CONFIG = {
    "stability": {
        "columns": list(persist.STABILITY_COLUMNS),
        "key": list(persist.STABILITY_KEY),
        "validator": persist.validate_stab_descriptions,
        "numeric": list(persist.STABILITY_NUMERIC),
        "csv_name": "stability_measurements.csv",
    },
    "color": {
        "columns": list(persist.COLOR_COLUMNS),
        "key": list(persist.COLOR_KEY),
        "validator": persist.validate_color_descriptions,
        "numeric": list(persist.COLOR_NUMERIC),
        "csv_name": "color_measurements.csv",
    },
    "micro": {
        "columns": list(persist.MICRO_COLUMNS),
        "key": list(persist.MICRO_KEY),
        "validator": persist.validate_micro_descriptions,
        "numeric": list(persist.MICRO_NUMERIC),
        "csv_name": "microbiology_measurements.csv",
    },
}

# Campos obrigatórios (não podem ficar vazios). Inclui a chave composta de
# duplicidade de cada tipo e, para cor, os canais RGB exigidos pelo
# validador existente.
REQUIRED = {
    "stability": list(persist.STABILITY_KEY),
    "color": list(persist.COLOR_KEY) + ["r", "g", "b"],
    "micro": list(persist.MICRO_KEY),
}

# Sinônimos comuns (português/inglês) para sugerir mapeamento quando o
# nome da coluna de origem não coincide exatamente com o campo do esquema.
# Aplicados apenas quando a correspondência é inequívoca; casos ambíguos
# ficam sem sugestão e exigem seleção manual.
_ALIASES = {
    "batchid": "batch_id", "batch": "batch_id", "lote": "batch_id",
    "id_lote": "batch_id", "lote_id": "batch_id",
    "formulacao": "formulation", "formula": "formulation",
    "storagecondition": "storage_condition", "storage": "storage_condition",
    "condicao": "storage_condition", "cond": "storage_condition",
    "condicao_armazenamento": "storage_condition",
    "dia": "day", "dias": "day", "tempo": "day", "tempo_dias": "day",
    "time_days": "day", "time": "day", "tempo_armazenamento": "day",
    "vialid": "vial_id", "vial": "vial_id", "frasco": "vial_id",
    "amostra": "vial_id", "sample": "vial_id", "id_amostra": "vial_id",
    "replica": "replicate", "rep": "replicate", "repeticao": "replicate",
    "n_replica": "replicate",
    "notes": "notes", "note": "notes", "observacoes": "notes",
    "obs": "notes", "observacao": "notes",
    "phstorage": "pH_storage", "ph_armazenamento": "pH_storage",
    "a520ph1": "a520_ph1", "abs520ph1": "a520_ph1", "absorbancia520ph1": "a520_ph1",
    "a700ph1": "a700_ph1", "abs700ph1": "a700_ph1",
    "a520ph45": "a520_ph45", "a520ph4_5": "a520_ph45", "abs520ph45": "a520_ph45",
    "a700ph45": "a700_ph45", "a700ph4_5": "a700_ph45",
    "dilutionfactor": "dilution_factor", "fd": "dilution_factor",
    "fator_diluicao": "dilution_factor", "diluicao": "dilution_factor",
    "pathlength": "path_length_cm", "pathlengthcm": "path_length_cm",
    "caminho_optico": "path_length_cm", "caminho": "path_length_cm",
    "targetph": "target_pH", "ph_alvo": "target_pH", "ph_objetivo": "target_pH",
    "measuredph": "measured_pH_final", "ph_final": "measured_pH_final",
    "ph_medido": "measured_pH_final", "measuredphfinal": "measured_pH_final",
    "red": "r", "vermelho": "r",
    "green": "g", "verde": "g",
    "blue": "b", "azul": "b",
    "lstar": "L_star", "lab_l": "L_star", "l_lab": "L_star",
    "astar": "a_star", "lab_a": "a_star", "a_lab": "a_star",
    "bstar": "b_star", "lab_b": "b_star", "b_lab": "b_star",
    "lambda": "absorbance_max_nm", "lambda_nm": "absorbance_max_nm",
    "pico_nm": "absorbance_max_nm", "absorbancemaxnm": "absorbance_max_nm",
    "abs_max": "absorbance_max", "absorbancemax": "absorbance_max",
    "absorbancia_pico": "absorbance_max",
    "testtype": "test_type", "tipo_teste": "test_type", "teste": "test_type",
    "assay": "test_type", "ensaio": "test_type",
    "resultvalue": "result_value", "resultado": "result_value",
    "valor": "result_value", "valor_resultado": "result_value",
    "resultunit": "result_unit", "unidade": "result_unit",
    "unidade_resultado": "result_unit",
    "metodo": "method",
}


# ---------------------------------------------------------------------------
# Configuração por tipo de registro
# ---------------------------------------------------------------------------

def columns_for(record_type: str) -> list[str]:
    """Colunas canônicas do esquema de destino."""
    return list(_CONFIG[record_type]["columns"])


def key_for(record_type: str) -> list[str]:
    """Chave composta usada na detecção de duplicidade."""
    return list(_CONFIG[record_type]["key"])


def validator_for(record_type: str):
    """Validador existente do tipo de registro (função pura)."""
    return _CONFIG[record_type]["validator"]


def numeric_fields_for(record_type: str) -> list[str]:
    return list(_CONFIG[record_type]["numeric"])


def csv_name_for(record_type: str) -> str:
    return _CONFIG[record_type]["csv_name"]


def required_fields(record_type: str) -> list[str]:
    """Campos que não podem ficar vazios na importação."""
    return list(REQUIRED[record_type])


def combined_validator(record_type: str):
    """Combina o validador existente com obrigatoriedade de chave e unidade.

    Retorna uma função ``row -> list[str]`` utilizada tanto na prévia quanto
    como argumento ``validate`` de :func:`anthocyanin_persistence.append_row_safely`,
    de modo que o portão de gravação aplique as mesmas regras da prévia.
    """
    base = _CONFIG[record_type]["validator"]
    req = list(REQUIRED[record_type])

    def _validate(row: dict) -> list[str]:
        errors: list[str] = list(base(row))
        for field in req:
            if str(row.get(field, "")).strip() == "":
                errors.append(f"{field} é obrigatório e está ausente.")
        if record_type == "micro":
            value = str(row.get("result_value", "")).strip()
            unit = str(row.get("result_unit", "")).strip()
            if value != "" and unit == "":
                errors.append("result_unit ausente para um result_value preenchido.")
        return errors

    return _validate


# ---------------------------------------------------------------------------
# Normalização de nomes (para sugerir mapeamento)
# ---------------------------------------------------------------------------

def _normalize(name: str) -> str:
    """Minusculiza, remove acentos e padroniza separadores."""
    text = str(name).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _compact(name: str) -> str:
    """Forma compacta (sem separadores) para comparação tolerante."""
    return _normalize(name).replace("_", "")


# Aliases reindexados pela forma compacta (sem separadores) para casar com
# nomes de coluna que trazem espaços ou pontuação (ex.: "Abs 520 pH 1").
_ALIASES_COMPACT = {_compact(k): v for k, v in _ALIASES.items()}


def suggest_mapping(source_columns, target_fields) -> dict:
    """Sugere mapeamento ``target_field -> source_column`` (ou ``None``).

    A sugestão só atribui quando a correspondência é inequívoca: nomes
    exatamente iguais (após normalização), depois compactos, e por fim
    sinônimos conhecidos. Casos ambíguos ficam como ``None`` e exigem
    seleção manual na interface.
    """
    norm_sources = {c: _normalize(c) for c in source_columns}
    compact_sources = {c: _compact(c) for c in source_columns}
    mapping = {f: None for f in target_fields}
    used = set()

    # Passo 1: igualdade exata após normalização.
    for f in target_fields:
        nf = _normalize(f)
        matches = [c for c in source_columns if norm_sources[c] == nf and c not in used]
        if len(matches) == 1:
            mapping[f] = matches[0]
            used.add(matches[0])

    # Passo 2: igualdade na forma compacta (tolera separadores).
    for f in target_fields:
        if mapping[f] is not None:
            continue
        cf = _compact(f)
        matches = [c for c in source_columns if compact_sources[c] == cf and c not in used]
        if len(matches) == 1:
            mapping[f] = matches[0]
            used.add(matches[0])

    # Passo 3: sinônimos conhecidos (apenas se inequívoco).
    for f in target_fields:
        if mapping[f] is not None:
            continue
        candidates = [
            c for c in source_columns
            if c not in used and _ALIASES_COMPACT.get(compact_sources[c]) == f
        ]
        if len(candidates) == 1:
            mapping[f] = candidates[0]
            used.add(candidates[0])

    return mapping


# ---------------------------------------------------------------------------
# Interpretação da origem (CSV, XLSX, tabela colada)
# ---------------------------------------------------------------------------

def parse_source(path=None, pasted=None) -> pd.DataFrame:
    """Interpreta a origem dos dados.

    Esta função é a fronteira de "interpretação da origem": hoje lê
    arquivos/tabelas estruturadas; uma futura camada de linguagem natural
    poderá produzir o mesmo DataFrame a partir de descrições em texto.
    """
    if path is not None:
        return _read_file(Path(path))
    if pasted is not None and str(pasted).strip():
        return _read_pasted(pasted)
    raise ValueError("Nenhuma origem informada: envie um arquivo ou cole uma tabela.")


def _read_file(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    if ext == ".csv":
        return _read_csv_file(path)
    if ext in (".xlsx", ".xlsm"):
        return _read_xlsx_file(path)
    if ext == ".xls":
        raise ValueError(
            "Formato .xls legado não suportado. Exporte como .xlsx ou .csv."
        )
    raise ValueError(f"Formato de arquivo não suportado: {ext}")


def _read_csv_file(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Não foi possível ler o CSV {path.name}: {exc}") from exc


def _read_xlsx_file(path: Path) -> pd.DataFrame:
    try:
        import openpyxl  # noqa: F401  — engine exigido pelo pandas
    except ImportError as exc:  # pragma: no cover
        raise ValueError(
            "Leitura de XLSX exige a dependência 'openpyxl'. "
            "Instale com: pip install openpyxl"
        ) from exc
    try:
        return pd.read_excel(path, sheet_name=0, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Não foi possível ler a planilha {path.name}: {exc}") from exc


def _read_pasted(text: str) -> pd.DataFrame:
    raw = str(text)
    if not raw.strip():
        return pd.DataFrame()
    try:
        return pd.read_csv(
            io.StringIO(raw), sep=None, engine="python", skipinitialspace=True
        )
    except Exception:  # noqa: BLE001
        for sep in (",", ";", "\t"):
            try:
                return pd.read_csv(io.StringIO(raw), sep=sep)
            except Exception:  # noqa: BLE001
                continue
        raise ValueError(
            "Não foi possível interpretar a tabela colada. "
            "Use colunas separadas por tabulação, vírgula ou ponto-e-vírgula."
        )


# ---------------------------------------------------------------------------
# Mapeamento e montagem da prévia
# ---------------------------------------------------------------------------

def apply_mapping(df: pd.DataFrame, mapping: dict, target_fields) -> pd.DataFrame:
    """Reordena/renomeia colunas de origem para o esquema de destino.

    Colunas não mapeadas são descartadas; campos de destino sem origem
    ficam vazios. Valores são tratados como texto (preservando a origem),
    com NaN normalizado para "" e espaços removidos — nenhuma conversão
    de valor científico é aplicada silenciosamente.
    """
    out = pd.DataFrame(index=range(len(df)))
    for field in target_fields:
        source = mapping.get(field)
        if source and source in df.columns:
            col = df[source]
            col = col.where(col.notna(), "")
            out[field] = col.astype(str).str.strip()
        else:
            out[field] = ""
    return out[list(target_fields)]


def _row_key(row: dict, key_cols: list[str]) -> str:
    return "|".join(str(row.get(c, "")).strip() for c in key_cols)


def _existing_keys(existing: pd.DataFrame, key_cols: list[str]) -> set[str]:
    if existing is None or existing.empty:
        return set()
    keys = set()
    for i in range(len(existing)):
        row = {c: existing.iloc[i][c] for c in key_cols if c in existing.columns}
        keys.add("|".join(str(row.get(c, "")).strip() for c in key_cols))
    return keys


def _unit_warnings(record_type: str, row: dict) -> list[str]:
    """Avisos (não impeditivos) sobre unidades — extensão futura."""
    # Reservado: tipos sem coluna de unidade explícita não geram aviso hoje.
    return []


def build_preview(mapped_df: pd.DataFrame, record_type: str,
                  existing_df: pd.DataFrame | None = None) -> dict:
    """Constrói a prévia validada (em memória; não grava nada).

    Cada linha recebe:

    * ``erros``: problemas que impedem a gravação (validador, obrigatórios,
      unidade ausente, duplicidade contra o existente ou dentro do lote);
    * ``avisos``: observações não impeditivas;
    * ``valida``: ``True`` quando não há erros impeditivos;
    * ``duplicata``: ``True`` quando colide com registro existente ou
      com outra linha do próprio lote de importação.

    Retorna ``{"rows": [...], "summary": {...}}``.
    """
    cfg = _CONFIG[record_type]
    validator = combined_validator(record_type)
    key_cols = list(cfg["key"])

    existing = _existing_keys(existing_df, key_cols)
    seen_in_batch: dict[str, int] = {}
    rows: list[dict] = []

    for pos in range(len(mapped_df)):
        row = {c: mapped_df.iloc[pos][c] for c in mapped_df.columns}
        errors = list(validator(row))

        k = _row_key(row, key_cols)
        dup_existing = k in existing
        dup_batch = k in seen_in_batch
        seen_in_batch[k] = seen_in_batch.get(k, 0) + 1

        if dup_existing:
            errors.append("Duplicata de registro já gravado (chave composta).")
        if dup_batch:
            errors.append("Duplicata de outra linha deste lote de importação.")

        avisos: list[str] = list(_unit_warnings(record_type, row))

        record = {
            "linha": pos + 1,
            "erros": "; ".join(errors),
            "avisos": "; ".join(avisos),
            "valida": len(errors) == 0,
            "duplicata": bool(dup_existing or dup_batch),
        }
        for c in mapped_df.columns:
            record[c] = row[c]
        rows.append(record)

    validas = sum(1 for r in rows if r["valida"])
    invalidas = len(rows) - validas
    duplicatas = sum(1 for r in rows if r["duplicata"])

    obrig_ausentes = sorted({
        err.split(" ")[0] for r in rows for err in r["erros"].split("; ")
        if "obrigatório e está ausente" in err
    })
    fora_limite = sorted({
        err for r in rows for err in r["erros"].split("; ")
        if ("deve estar entre" in err or "não pode ser negativo" in err
            or "deve ser numérico" in err or "deve ser um inteiro" in err
            or "deve ser maior que zero" in err)
    })
    unidades = sorted({
        err for r in rows for err in r["erros"].split("; ")
        if "unidade" in err.lower() or "result_unit" in err
    })

    summary = {
        "total": len(rows),
        "validas": validas,
        "invalidas": invalidas,
        "duplicatas": duplicatas,
        "campos_obrigatorios_ausentes": obrig_ausentes,
        "valores_fora_limite_ou_invalidos": fora_limite,
        "unidades_ausentes": unidades,
    }
    return {"rows": rows, "summary": summary}


def preview_rows_to_frame(rows: list[dict], target_fields) -> pd.DataFrame:
    """Monta um DataFrame editável para a interface, com coluna de exclusão."""
    display_cols = ["linha"] + list(target_fields) + ["erros", "avisos", "_excluir"]
    frame = pd.DataFrame(columns=display_cols)
    for r in rows:
        frame.loc[len(frame)] = {
            "linha": r["linha"],
            **{c: r.get(c, "") for c in target_fields},
            "erros": r["erros"],
            "avisos": r["avisos"],
            "_excluir": False,
        }
    return frame


def finalize_from_edited(edited: pd.DataFrame, target_fields) -> pd.DataFrame:
    """Extrai as linhas não excluídas do DataFrame editado, no esquema de destino."""
    if edited is None or edited.empty:
        return pd.DataFrame(columns=list(target_fields))
    if "_excluir" in edited.columns:
        keep = edited[edited["_excluir"].astype(str).str.lower().isin(["true", "1", "sim"])]
        kept = edited[~edited.index.isin(keep.index)]
    else:
        kept = edited
    out = pd.DataFrame(columns=list(target_fields))
    for c in target_fields:
        out[c] = kept[c].astype(str).str.strip() if c in kept.columns else ""
    return out.reset_index(drop=True)
