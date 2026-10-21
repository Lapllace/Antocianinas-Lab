"""Camada de persistência e validação para a interface Streamlit.

Esta camada é independente de Streamlit: pode ser importada e testada
diretamente. Ela reutiliza a contrato de colunas do módulo científico
(`anthocyanin_lab.py`) e concentra as regras de segurança de gravação:

* validação de campos vocacionais (pH, diluição, caminho óptico, RGB);
* detecção de registros duplicados;
* backup timestampado antes de qualquer gravação;
* escrita atômica (arquivo temporário + rename) para não corromper o CSV;
* reporte explícito de sucesso ou falha.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

# Contratos de coluna exatos, sincronizados com anthocyanin_lab.py.
STABILITY_COLUMNS = [
    "batch_id", "formulation", "storage_condition", "day", "vial_id", "replicate",
    "pH_storage", "a520_ph1", "a700_ph1", "a520_ph45", "a700_ph45",
    "dilution_factor", "path_length_cm", "notes",
]

COLOR_COLUMNS = [
    "batch_id", "formulation", "storage_condition", "day", "vial_id", "replicate",
    "target_pH", "measured_pH_final", "r", "g", "b",
    "L_star", "a_star", "b_star", "absorbance_max_nm", "absorbance_max", "notes",
]

MICRO_COLUMNS = [
    "batch_id", "formulation", "storage_condition", "day", "vial_id",
    "test_type", "result_value", "result_unit", "method", "notes",
]

# Chave composta usada para detectar duplicidade (não sobrescrever).
STABILITY_KEY = ["batch_id", "formulation", "storage_condition", "day", "vial_id", "replicate"]
COLOR_KEY = ["batch_id", "formulation", "storage_condition", "day", "vial_id", "replicate"]
MICRO_KEY = ["batch_id", "formulation", "storage_condition", "day", "vial_id", "test_type"]

# Campos numéricos normalizados antes de validar/escrever.
STABILITY_NUMERIC = ["day", "replicate", "pH_storage", "a520_ph1", "a700_ph1",
                     "a520_ph45", "a700_ph45", "dilution_factor", "path_length_cm"]
COLOR_NUMERIC = ["day", "replicate", "target_pH", "measured_pH_final", "r", "g", "b",
                 "L_star", "a_star", "b_star", "absorbance_max_nm", "absorbance_max"]
MICRO_NUMERIC = ["day", "result_value"]


def load_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    """Carrega um CSV mantendo o esquema esperado; cabeçalho vazio se arquivo vazio/ausente."""
    p = Path(path)
    if not p.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(p)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Não foi possível ler {p}: {exc}") from exc
    if df.empty:
        return pd.DataFrame(columns=columns)
    return df


def _to_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _join_key(frame: pd.DataFrame, key_cols: list[str]) -> pd.Series:
    """Compõe a chave única como string para comparação robusta."""
    return pd.Series(
        ["|".join(str(frame.loc[i, col]) for col in key_cols) for i in range(len(frame))],
        index=frame.index,
        dtype=object,
    )


def validate_stab_descriptions(row: dict[str, str]) -> list[str]:
    """Validação cruzada para estabilidade (numérico, pH, diluição, caminho óptico, não negativo)."""
    errors: list[str] = []
    for field in STABILITY_NUMERIC:
        value = str(row.get(field, "")).strip()
        if value == "":
            continue
        try:
            number = float(value)
        except ValueError:
            errors.append(f"{field} deve ser numérico.")
            continue
        if field == "day":
            continue
        if field == "replicate" and number <= 0:
            errors.append("replicate deve ser maior que zero.")
        elif field == "pH_storage" and not (0.0 <= number <= 14.0):
            errors.append("pH_storage deve estar entre 0 e 14.")
        elif number < 0:
            errors.append(f"{field} não pode ser negativo.")
        if field == "dilution_factor" and number <= 0:
            errors.append("dilution_factor deve ser maior que zero.")
        if field == "path_length_cm" and number <= 0:
            errors.append("path_length_cm deve ser maior que zero.")
    return errors

def validate_color_descriptions(row: dict[str, str]) -> list[str]:
    """Validação cruzada para cor: RGB obrigatório e no intervalo 0-255; pH não-negativo."""
    errors: list[str] = []
    for field in ("r", "g", "b"):
        value = str(row.get(field, "")).strip()
        if value == "":
            errors.append(f"{field} é obrigatório (0-255).")
            continue
        try:
            number = int(value)
        except ValueError:
            errors.append(f"{field} deve ser um inteiro.")
            continue
        if not (0 <= number <= 255):
            errors.append(f"{field} deve estar entre 0 e 255.")
    for field in COLOR_NUMERIC:
        if field in ("r", "g", "b"):
            continue
        value = str(row.get(field, "")).strip()
        if value == "":
            continue
        try:
            number = float(value)
        except ValueError:
            errors.append(f"{field} deve ser numérico.")
            continue
        if field in ("target_pH", "measured_pH_final"):
            if not (0.0 <= number <= 14.0):
                errors.append(f"{field} deve estar entre 0 e 14.")
        elif number < 0:
            errors.append(f"{field} não pode ser negativo.")
    return errors


def validate_micro_descriptions(row: dict[str, str]) -> list[str]:
    """Validação básica para microbiologia: valores não negativos quando informados."""
    errors: list[str] = []
    for field in MICRO_NUMERIC:
        value = str(row.get(field, "")).strip()
        if value == "":
            continue
        try:
            number = float(value)
        except ValueError:
            errors.append(f"{field} deve ser numérico.")
            continue
        if number < 0:
            errors.append(f"{field} não pode ser negativo.")
    return errors


def write_empty_csv(path: Path, columns: list[str]) -> None:
    """Garante o cabeçalho sem sobrescrever dados já existentes."""
    p = Path(path)
    if p.exists() and p.stat().st_size > 0:
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=columns).to_csv(p, index=False)


def find_duplicates(existing: pd.DataFrame, new_rows: pd.DataFrame, key_cols: list[str]) -> list[str]:
    """Retorna colisões de chave (vazio = sem duplicidade)."""
    if existing.empty or new_rows.empty:
        return []
    existing_keys = _join_key(existing, key_cols)
    new_keys = _join_key(new_rows, key_cols)
    existing_set = set(existing_keys.tolist())
    return [key for key in new_keys.tolist() if key in existing_set]


def backup_csv(source: Path, backup_dir: Path) -> Path:
    """Gravando uma cópia timestampada de um CSV imediatamente antes da alteração."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = backup_dir / f"{source.name}.{timestamp}.csv"
    counter = 0
    while destination.exists():
        counter += 1
        destination = backup_dir / f"{source.stem}_{timestamp}_{counter}.csv"
    shutil.copy2(source, destination)
    return destination


def append_row_safely(
    csv_path: Path,
    new_rows: pd.DataFrame,
    key_cols: list[str],
    validate: callable,
    *,
    backup_parent: Path = None,
) -> dict:
    """Adiciona registros a um CSV com backup, validação e prevenção de duplicidade.

    Retorna um dicionário com status, mensagem, backup_path (em sucesso) e
    appended_count (em sucesso).
    """
    errors: list[str] = []
    for _, row in new_rows.iterrows():
        row_dict = {col: row[col] for col in new_rows.columns if col in row.index}
        errors.extend(validate(row_dict))

    if errors:
        return {
            "status": "error",
            "message": "Validação recusou a gravação: " + "; ".join(errors),
            "backup_path": None,
            "appended_count": 0,
        }

    csv_path = Path(csv_path)
    write_empty_csv(csv_path, list(new_rows.columns))
    existing = load_csv(csv_path, list(new_rows.columns))

    # Apenas colunas numéricas são normalizadas; as do tipo String ficam
    # integrais (são parte da chave de duplicidade).
    numeric_key_cols = [
        c for c in key_cols if c in existing.columns and pd.api.types.is_numeric_dtype(existing[c])
    ]
    _to_numeric(existing, numeric_key_cols)

    duplicates = find_duplicates(existing, new_rows, key_cols)
    if duplicates:
        return {
            "status": "error",
            "message": (
                "Registro(s) duplicado(s) detectado(s); nada foi alterado: "
                + "; ".join(sorted(set(duplicates)))
            ),
            "backup_path": None,
            "appended_count": 0,
        }

    # Compõe o conteúdo final concatenando os registros existentes aos
    # novos (até aqui o arquivo não foi alterado). A reindexação preserva a
    # ordem canônica de colunas do esquema de destino.
    base = pd.concat([existing, new_rows], ignore_index=True, sort=False)
    base = base.reindex(columns=list(new_rows.columns))


    target = Path(backup_parent or csv_path.parent) / "backups"
    backup_path = backup_csv(csv_path, target)

    # Escrita atômica: arquivo temporário gerado e renomeado para o destino,
    # de modo que uma gravação em curso nunca deixa o CSV corrompido.
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(csv_path.parent), prefix=".tmp_", suffix=".csv"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                base.to_csv(handle, index=False)
            os.replace(tmp_name, csv_path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"Falha ao gravar {csv_path}: {exc}",
            "backup_path": str(backup_path) if backup_path.exists() else None,
            "appended_count": 0,
        }

    return {
        "status": "success",
        "message": f"Gravação concluída: {len(new_rows)} novo(s) registro(s) em {csv_path.name}.",
        "backup_path": str(backup_path),
        "appended_count": int(len(new_rows)),
    }

