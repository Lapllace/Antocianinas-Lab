#!/usr/bin/env python3
"""Analysis and scenario-simulation pipeline for liquid red-cabbage anthocyanin stability.

Commands:
  python anthocyanin_lab.py init --dir .
  python anthocyanin_lab.py analyze --dir .
  python anthocyanin_lab.py simulate --dir . --demo
  python anthocyanin_lab.py ml --dir . --target retention_pct
  python anthocyanin_lab.py literature --dir .
  python anthocyanin_lab.py plan --dir .

The script calculates total monomeric anthocyanin concentration as cyanidin-3-glucoside
(C3G) equivalents using the pH-differential spectrophotometric method; retention relative
to day 0; exponential degradation kinetics; and smartphone HSV / CIE76 colour drift.
It does not replace instrument calibration, validated laboratory SOPs, or statistical review.
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import html
import json
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

MW_C3G_G_MOL = 449.2
EPSILON_C3G_L_MOL_CM = 26900.0

STABILITY_COLUMNS = [
    "batch_id", "formulation", "storage_condition", "day", "vial_id", "replicate",
    "pH_storage", "a520_ph1", "a700_ph1", "a520_ph45", "a700_ph45",
    "dilution_factor", "path_length_cm", "notes",
]
COLOR_COLUMNS = [
    "batch_id", "formulation", "storage_condition", "day", "vial_id", "replicate",
    "target_pH", "measured_pH_final", "r", "g", "b", "L_star", "a_star", "b_star",
    "absorbance_max_nm", "absorbance_max", "notes",
]
MICRO_COLUMNS = [
    "batch_id", "formulation", "storage_condition", "day", "vial_id",
    "test_type", "result_value", "result_unit", "method", "notes",
]
LITERATURE_COLUMNS = [
    "study_id", "treatment_id", "source_url", "doi", "source_location",
    "extraction_type", "species", "matrix", "solvent", "pH", "additive",
    "additive_concentration_pct", "temperature_c", "light_condition",
    "oxygen_condition", "package_material", "time_value", "time_unit",
    "measurement", "value", "standard_deviation", "value_unit",
    "replicate_count", "data_origin", "reported_or_calculated", "notes",
]

LITERATURE_STUDY_COLUMNS = [
    "study_id", "citation", "title", "doi", "url", "species", "matrix",
    "solvent", "extraction_conditions", "method", "pH", "packaging",
    "storage_conditions", "analysis_unit", "limitations", "notes",
]
LITERATURE_EVIDENCE_COLUMNS = [
    "study_id", "evidence_type", "evidence_category", "evidence_text",
    "origin_source", "source_url", "doi", "source_location", "conditions",
    "treatment_id", "additive", "additive_concentration_pct",
    "temperature_c", "pH", "time_value", "time_unit", "measurement", "value",
    "standard_deviation", "value_unit", "k_value", "k_unit",
    "half_life", "half_life_unit", "formula", "notes",
]


def safe_slug(value: object) -> str:
    return str(value).strip().replace(" ", "_")



def default_simulation_config() -> dict:
    """Template for a transparent, uncalibrated first-order scenario model."""
    return {
        "model": "first_order_arrhenius_scenario",
        "purpose": "Exploração de hipóteses; não é uma previsão validada nem dado experimental.",
        "reference_temperature_c": 25.0,
        "reference_half_life_days": None,
        "activation_energy_kj_mol": None,
        "initial_retention_pct": 100.0,
        "days": [0, 3, 7, 10, 14, 28],
        "scenarios": [
            {
                "scenario_id": "C4_DARK",
                "label": "4 °C, escuro",
                "temperature_c": 4.0,
                "pH_factor": 1.0,
                "light_factor": 1.0,
                "oxygen_factor": 1.0,
                "packaging_factor": 1.0,
                "notes": "Fatores de influência em 1,0 até calibração; temperatura modelada por Arrhenius."
            },
            {
                "scenario_id": "C25_DARK",
                "label": "25 °C, escuro",
                "temperature_c": 25.0,
                "pH_factor": 1.0,
                "light_factor": 1.0,
                "oxygen_factor": 1.0,
                "packaging_factor": 1.0,
                "notes": "Cenário de referência; fatores de influência em 1,0."
            }
        ]
    }


def ml_template_columns() -> list[str]:
    """Column contract for future ML-ready observations; never auto-filled."""
    return [
        "record_id", "data_origin", "batch_id", "formulation", "storage_condition",
        "temperature_c", "light_condition", "oxygen_condition", "container_material",
        "headspace_ratio_pct", "preservative_or_additive", "initial_pH", "pH_day",
        "study_id", "day", "tac_mg_c3g_L", "retention_pct", "hue_deg", "saturation_0_1",
        "value_0_1", "delta_e_cie76_vs_day0", "assay_method", "instrument",
        "independent_batch", "notes"
    ]


def write_json_if_missing(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"Mantido (não sobrescrito): {path}")
    else:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Criado: {path}")

def make_templates(root: Path) -> None:
    raw = root / "data" / "raw"
    processed = root / "data" / "processed"
    templates = root / "data" / "templates"
    config = root / "data" / "config"
    literature = root / "data" / "literature"
    raw.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    templates.mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)
    literature.mkdir(parents=True, exist_ok=True)
    files = {
        "stability_measurements.csv": STABILITY_COLUMNS,
        "color_measurements.csv": COLOR_COLUMNS,
        "microbiology_measurements.csv": MICRO_COLUMNS,
    }
    for filename, columns in files.items():
        path = raw / filename
        if path.exists():
            print(f"Mantido (não sobrescrito): {path}")
        else:
            pd.DataFrame(columns=columns).to_csv(path, index=False)
            print(f"Criado: {path}")
    write_json_if_missing(config / "simulation_parameters.json", default_simulation_config())
    ml_path = templates / "ml_observation_template.csv"
    if ml_path.exists():
        print(f"Mantido (não sobrescrito): {ml_path}")
    else:
        pd.DataFrame(columns=ml_template_columns()).to_csv(ml_path, index=False)
        print(f"Criado: {ml_path}")
    ml_data_path = raw / "ml_observations.csv"
    if ml_data_path.exists():
        print(f"Mantido (não sobrescrito): {ml_data_path}")
    else:
        pd.DataFrame(columns=ml_template_columns()).to_csv(ml_data_path, index=False)
        print(f"Criado: {ml_data_path}")
    
    lit_files = {
        "literature_studies.csv": LITERATURE_STUDY_COLUMNS,
        "literature_measurements.csv": LITERATURE_COLUMNS,
        "literature_evidence.csv": LITERATURE_EVIDENCE_COLUMNS,
    }
    for filename, columns in lit_files.items():
        path = literature / filename
        if path.exists():
            print(f"Mantido (não sobrescrito): {path}")
        else:
            pd.DataFrame(columns=columns).to_csv(path, index=False)
            print(f"Criado: {path}")


def numeric_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")


def calculate_tac(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate mg C3G-equivalents/L of original extract (with dilution correction)."""
    required = set(STABILITY_COLUMNS) - {"notes"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Colunas ausentes em stability_measurements.csv: " + ", ".join(sorted(missing)))

    df = frame.copy()
    numeric_columns(df, ["day", "pH_storage", "a520_ph1", "a700_ph1", "a520_ph45",
                         "a700_ph45", "dilution_factor", "path_length_cm", "replicate"])
    df["absorbance_difference"] = (
        (df["a520_ph1"] - df["a700_ph1"])
        - (df["a520_ph45"] - df["a700_ph45"])
    )
    denominator = EPSILON_C3G_L_MOL_CM * df["path_length_cm"]
    # A * MW(g/mol) * 1000(mg/g) / epsilon gives mg/L; apply dilution factor.
    df["tac_mg_c3g_L"] = (
        df["absorbance_difference"] * MW_C3G_G_MOL * 1000.0
        * df["dilution_factor"] / denominator
    )
    invalid = (df["path_length_cm"] <= 0) | (df["dilution_factor"] <= 0)
    df.loc[invalid, "tac_mg_c3g_L"] = np.nan

    keys = ["batch_id", "formulation", "storage_condition"]
    shared_keys = ["batch_id", "formulation"]
    valid_baseline = df.loc[(df["day"] == 0) & df["tac_mg_c3g_L"].notna()]

    # Prefer a baseline for the exact storage group. If the day-0 value was
    # measured once before splitting a batch into storage conditions, fall
    # back to the shared batch/formulation baseline; this does not require
    # extra physical vials.
    baseline_specific = valid_baseline.groupby(keys)["tac_mg_c3g_L"].mean().rename("_baseline_specific")
    baseline_shared = valid_baseline.groupby(shared_keys)["tac_mg_c3g_L"].mean().rename("_baseline_shared")
    df = df.join(baseline_specific, on=keys)
    df = df.join(baseline_shared, on=shared_keys)
    df["day0_tac_mg_c3g_L"] = df["_baseline_specific"].combine_first(df["_baseline_shared"])
    df = df.drop(columns=["_baseline_specific", "_baseline_shared"])
    df["retention_pct"] = 100.0 * df["tac_mg_c3g_L"] / df["day0_tac_mg_c3g_L"]
    df["qc_flag"] = ""
    df.loc[df["absorbance_difference"] < 0, "qc_flag"] = "A diferencial negativa: verificar branco, diluição e leitura"
    df.loc[df["day0_tac_mg_c3g_L"].isna(), "qc_flag"] = "Sem baseline válida no dia 0 para este grupo"
    df.loc[df["retention_pct"] > 120, "qc_flag"] = (
        df.loc[df["retention_pct"] > 120, "qc_flag"].astype(str)
        .apply(lambda s: (s + "; " if s else "") + "retenção >120%: verificar variabilidade analítica")
    )
    return df


def fit_kinetics(stability: pd.DataFrame) -> pd.DataFrame:
    """Fit ln(TAC) = intercept + slope*time; t1/2 is reported only when k=-slope > 0."""
    records: list[dict] = []
    keys = ["batch_id", "formulation", "storage_condition"]
    for group_key, group in stability.groupby(keys, dropna=False):
        valid = group.loc[(group["tac_mg_c3g_L"] > 0) & group["day"].notna()].copy()
        # A shared day-0 aliquot may be labeled BASELINE. Add its mean as the
        # common time-zero observation for this kinetic curve (not a new vial).
        if not (valid["day"] == 0).any() and isinstance(group_key, tuple) and len(group_key) == 3:
            batch_val, formulation_val, condition_val = group_key
            baseline_pool = stability.loc[
                (stability["batch_id"] == batch_val)
                & (stability["formulation"] == formulation_val)
                & (stability["day"] == 0)
                & (stability["tac_mg_c3g_L"] > 0)
            ]
            condition_baseline = baseline_pool.loc[baseline_pool["storage_condition"] == condition_val]
            use_base = condition_baseline if not condition_baseline.empty else baseline_pool
            if not use_base.empty:
                base_row = use_base.iloc[[0]].copy()
                base_row["day"] = 0
                valid = pd.concat([valid, base_row], ignore_index=True)
        daily = valid.groupby("day", as_index=False)["tac_mg_c3g_L"].mean().sort_values("day")
        row = dict(zip(keys, group_key if isinstance(group_key, tuple) else (group_key,)))
        row.update({"n_timepoints": int(daily["day"].nunique()), "k_per_day": np.nan,
                    "half_life_days": np.nan, "r_squared": np.nan,
                    "fit_note": "Necessários pelo menos 3 tempos distintos com TAC > 0"})
        if daily["day"].nunique() >= 3:
            x = daily["day"].to_numpy(dtype=float)
            y = np.log(daily["tac_mg_c3g_L"].to_numpy(dtype=float))
            slope, intercept = np.polyfit(x, y, 1)
            prediction = intercept + slope * x
            ss_res = float(np.sum((y - prediction) ** 2))
            ss_tot = float(np.sum((y - np.mean(y)) ** 2))
            r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
            k = -float(slope)
            row.update({"k_per_day": k, "r_squared": r_squared,
                        "half_life_days": math.log(2) / k if k > 0 else np.nan,
                        "fit_note": "Ajuste exploratório; validar resíduos e comparar modelos" if k > 0
                                    else "Sem degradação exponencial positiva estimada; meia-vida não calculada"})
        records.append(row)
    return pd.DataFrame(records)


def add_hsv_and_delta_e(frame: pd.DataFrame) -> pd.DataFrame:
    required = set(COLOR_COLUMNS) - {"notes"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Colunas ausentes em color_measurements.csv: " + ", ".join(sorted(missing)))
    df = frame.copy()
    numeric_columns(df, ["day", "replicate", "target_pH", "measured_pH_final", "r", "g", "b",
                         "L_star", "a_star", "b_star", "absorbance_max_nm", "absorbance_max"])
    hsv_values = []
    for row in df[["r", "g", "b"]].itertuples(index=False, name=None):
        r, g, b = row
        if any(pd.isna(v) or v < 0 or v > 255 for v in (r, g, b)):
            hsv_values.append((np.nan, np.nan, np.nan))
        else:
            h, s, v = colorsys.rgb_to_hsv(float(r) / 255, float(g) / 255, float(b) / 255)
            hsv_values.append((h * 360.0, s, v))
    df[["hue_deg", "saturation_0_1", "value_0_1"]] = pd.DataFrame(hsv_values, index=df.index)

    # CIE76 Delta E uses L*, a*, b* and is a simple first-pass drift metric.
    keys = ["batch_id", "formulation", "storage_condition", "target_pH"]
    shared_keys = ["batch_id", "formulation", "target_pH"]
    lab_cols = ["L_star", "a_star", "b_star"]
    base = df.loc[(df["day"] == 0) & df[lab_cols].notna().all(axis=1), keys + lab_cols]
    if not base.empty:
        specific = base.groupby(keys)[lab_cols].mean().add_suffix("_day0_specific")
        shared = base.groupby(shared_keys)[lab_cols].mean().add_suffix("_day0_shared")
        df = df.join(specific, on=keys)
        df = df.join(shared, on=shared_keys)
        for col in lab_cols:
            df[f"{col}_day0"] = df[f"{col}_day0_specific"].combine_first(df[f"{col}_day0_shared"])
        d_l = df["L_star"] - df["L_star_day0"]
        d_a = df["a_star"] - df["a_star_day0"]
        d_b = df["b_star"] - df["b_star_day0"]
        df["delta_e_cie76_vs_day0"] = np.sqrt(d_l ** 2 + d_a ** 2 + d_b ** 2)
        helper_cols = [f"{col}_day0_specific" for col in lab_cols] + [f"{col}_day0_shared" for col in lab_cols]
        df = df.drop(columns=helper_cols)
    else:
        df["delta_e_cie76_vs_day0"] = np.nan
    return df


def plot_retention(stability: pd.DataFrame, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_data = stability.dropna(subset=["retention_pct", "day"]).copy()
    if plot_data.empty:
        return
    # Show a common day-0 baseline for each storage condition when day 0 was
    # measured once before storage allocation. These rows are plotting copies,
    # not additional measurements or experimental replicates.
    observed_conditions = plot_data.loc[plot_data["day"] > 0,
        ["batch_id", "formulation", "storage_condition"]].drop_duplicates()
    baseline_rows = []
    shared_baselines = plot_data.loc[plot_data["day"] == 0]
    for item in observed_conditions.itertuples(index=False):
        already_has = ((plot_data["batch_id"] == item.batch_id)
            & (plot_data["formulation"] == item.formulation)
            & (plot_data["storage_condition"] == item.storage_condition)
            & (plot_data["day"] == 0)).any()
        if already_has:
            continue
        candidate = shared_baselines.loc[
            (shared_baselines["batch_id"] == item.batch_id)
            & (shared_baselines["formulation"] == item.formulation)
        ]
        if not candidate.empty:
            clone = candidate.iloc[[0]].copy()
            clone["storage_condition"] = item.storage_condition
            clone["day"] = 0
            clone["retention_pct"] = 100.0
            baseline_rows.append(clone)
    if baseline_rows:
        plot_data = pd.concat([plot_data, *baseline_rows], ignore_index=True)
    summary = plot_data.groupby(["formulation", "storage_condition", "day"])["retention_pct"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    for (formulation, condition), group in summary.groupby(["formulation", "storage_condition"]):
        group = group.sort_values("day")
        ax.errorbar(group["day"], group["mean"], yerr=group["std"].fillna(0), marker="o",
                    capsize=3, label=f"{formulation} | {condition}")
    ax.axhline(100, linestyle="--", linewidth=1)
    ax.set_xlabel("Tempo de armazenamento (dias)")
    ax.set_ylabel("Antocianinas monoméricas retidas (%)")
    ax.set_title("Retenção de antocianinas vs. tempo")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "anthocyanin_retention.png", dpi=180)
    plt.close(fig)


def plot_delta_e(color: pd.DataFrame, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_data = color.dropna(subset=["delta_e_cie76_vs_day0", "day"])
    if plot_data.empty:
        return
    summary = plot_data.groupby(["formulation", "storage_condition", "target_pH", "day"])["delta_e_cie76_vs_day0"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    for (formulation, condition, ph), group in summary.groupby(["formulation", "storage_condition", "target_pH"]):
        group = group.sort_values("day")
        ax.plot(group["day"], group["mean"], marker="o", label=f"{formulation} | {condition} | pH {ph:g}")
    ax.set_xlabel("Tempo de armazenamento (dias)")
    ax.set_ylabel("ΔE*ab (CIE76) em relação ao dia 0")
    ax.set_title("Deriva de cor durante o armazenamento")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "color_drift_deltaE.png", dpi=180)
    plt.close(fig)



def plot_tac_concentration(stability: pd.DataFrame, out_dir: Path) -> Path | None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = stability.dropna(subset=["tac_mg_c3g_L", "day"]).copy()
    if data.empty:
        return None
    # Visual-only copies make a shared day-0 baseline appear at the start of
    # each storage curve without creating new measurements or replicates.
    observed = data.loc[data["day"] > 0, ["batch_id", "formulation", "storage_condition"]].drop_duplicates()
    baseline = data.loc[data["day"] == 0]
    copies = []
    for item in observed.itertuples(index=False):
        exists = ((data["batch_id"] == item.batch_id) & (data["formulation"] == item.formulation)
                  & (data["storage_condition"] == item.storage_condition) & (data["day"] == 0)).any()
        if exists:
            continue
        candidates = baseline.loc[(baseline["batch_id"] == item.batch_id) & (baseline["formulation"] == item.formulation)]
        if not candidates.empty:
            clone = candidates.copy()
            clone["storage_condition"] = item.storage_condition
            clone["day"] = 0
            copies.append(clone)
    if copies:
        data = pd.concat([data, *copies], ignore_index=True)
    summary = data.groupby(["formulation", "storage_condition", "day"])["tac_mg_c3g_L"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    for (formulation, condition), group in summary.groupby(["formulation", "storage_condition"]):
        group = group.sort_values("day")
        ax.errorbar(group["day"], group["mean"], yerr=group["std"].fillna(0), marker="o", capsize=3,
                    label=f"{formulation} | {condition}")
    ax.set_xlabel("Armazenamento (dias)")
    ax.set_ylabel("Antocianinas monoméricas (mg equivalentes C3G/L)")
    ax.set_title("Concentração aparente de antocianinas ao longo do tempo")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    path = out_dir / "tac_concentration.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_kinetics_summary(kinetics: pd.DataFrame, out_dir: Path) -> Path | None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if kinetics.empty or "k_per_day" not in kinetics:
        return None
    data = kinetics.dropna(subset=["k_per_day"]).copy()
    if data.empty:
        return None
    data["group_label"] = data["formulation"].astype(str) + " | " + data["storage_condition"].astype(str) + " | " + data["batch_id"].astype(str)
    data = data.sort_values("k_per_day", ascending=True)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.45 * len(data))))
    ax.barh(data["group_label"], data["k_per_day"])
    ax.set_xlabel("Constante de degradação estimada k (dia⁻¹)")
    ax.set_title("Ajuste cinético exploratório por lote e condição")
    ax.grid(True, axis="x", alpha=0.25)
    fig.tight_layout()
    path = out_dir / "kinetics_rate_constants.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_hue_by_ph(color: pd.DataFrame, out_dir: Path) -> Path | None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = color.dropna(subset=["hue_deg", "target_pH"]).copy()
    if data.empty:
        return None
    # Copy shared day-0 values for plotting only, so the comparison curve
    # starts at baseline for each condition where no dedicated day-0 vial exists.
    observed = data.loc[data["day"] > 0, ["batch_id", "formulation", "storage_condition"]].drop_duplicates()
    baseline = data.loc[data["day"] == 0]
    copies = []
    for item in observed.itertuples(index=False):
        exists = ((data["batch_id"] == item.batch_id) & (data["formulation"] == item.formulation)
                  & (data["storage_condition"] == item.storage_condition) & (data["day"] == 0)).any()
        if exists:
            continue
        candidates = baseline.loc[(baseline["batch_id"] == item.batch_id) & (baseline["formulation"] == item.formulation)]
        if not candidates.empty:
            clone = candidates.copy()
            clone["storage_condition"] = item.storage_condition
            clone["day"] = 0
            copies.append(clone)
    if copies:
        data = pd.concat([data, *copies], ignore_index=True)
    days = sorted(data["day"].dropna().unique())
    selected_days = sorted(set([days[0], days[-1]])) if days else []
    data = data.loc[data["day"].isin(selected_days)]
    if data.empty:
        return None
    summary = data.groupby(["formulation", "storage_condition", "day", "target_pH"], dropna=False)["hue_deg"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    for (formulation, condition, day), group in summary.groupby(["formulation", "storage_condition", "day"], dropna=False):
        group = group.sort_values("target_pH")
        ax.plot(group["target_pH"], group["hue_deg"], marker="o",
                label=f"{formulation} | {condition} | dia {day:g}")
    ax.set_xlabel("pH-alvo da solução de teste")
    ax.set_ylabel("Matiz H (graus, HSV)")
    ax.set_title("Resposta de matiz ao pH: dia inicial e final disponíveis")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    path = out_dir / "color_hue_by_pH.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _image_as_data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def generate_html_report(title: str, notice: str, tables: list[tuple[str, pd.DataFrame]],
                         images: list[tuple[str, Path]], output_path: Path) -> None:
    """Create a self-contained HTML report with tables and embedded plots."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sections: list[str] = []
    sections.append(f"<header><h1>{html.escape(title)}</h1><p class='notice'>{html.escape(notice)}</p></header>")
    for label, path in images:
        if path.exists():
            sections.append(f"<section><h2>{html.escape(label)}</h2><img alt='{html.escape(label)}' src='{_image_as_data_uri(path)}'></section>")
    for label, frame in tables:
        sections.append(f"<section><h2>{html.escape(label)}</h2>")
        if frame is None or frame.empty:
            sections.append("<p>Sem dados disponíveis para esta seção.</p>")
        else:
            shown = frame.copy()
            for col in shown.select_dtypes(include=["number"]).columns:
                shown[col] = shown[col].map(lambda v: "—" if pd.isna(v) else (f"{v:.5g}" if isinstance(v, (float, np.floating)) else str(v)))
            sections.append(shown.to_html(index=False, escape=True, border=0, classes="data-table"))
        sections.append("</section>")
    page = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>
:root{{font-family:Inter,Segoe UI,Arial,sans-serif;color:#202733;background:#f4f6f8}}
body{{margin:0;padding:24px;max-width:1200px;margin-inline:auto}}header,section{{background:white;border:1px solid #dce2e8;border-radius:12px;padding:20px;margin-bottom:18px;box-shadow:0 2px 8px #1220330a}}
h1{{margin-top:0}}h2{{font-size:1.1rem}}.notice{{padding:12px;border-left:4px solid #64748b;background:#f1f5f9;line-height:1.5}}
img{{display:block;max-width:100%;height:auto;margin:auto}}.data-table{{border-collapse:collapse;width:100%;font-size:.9rem;display:block;overflow-x:auto;white-space:nowrap}}
.data-table th,.data-table td{{padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:left}}.data-table th{{background:#eef2f6;position:sticky;top:0}}
footer{{color:#5b6470;font-size:.85rem;padding:6px 2px}}@media(max-width:600px){{body{{padding:10px}}section,header{{padding:12px}}}}
</style></head><body>{sections}<footer>Gerado localmente pelo anthocyanin_lab.py. Verifique unidades, controles analíticos e pressupostos antes de interpretar ou publicar.</footer></body></html>""".format(title=html.escape(title), sections="\n".join(sections))
    output_path.write_text(page, encoding="utf-8")


def _demo_simulation_config() -> dict:
    """Artificial example parameters solely to test the software workflow."""
    cfg = default_simulation_config()
    cfg.update({
        "purpose": "DEMONSTRAÇÃO ARTIFICIAL: parâmetros escolhidos para testar o código, não obtidos de experimento nem calibrados para prever o extrato do usuário.",
        "reference_half_life_days": 10.0,
        "activation_energy_kj_mol": 40.0,
        "scenarios": [
            {"scenario_id": "C4_DARK", "label": "4 °C, escuro; fatores neutros", "temperature_c": 4.0,
             "pH_factor": 1.0, "light_factor": 1.0, "oxygen_factor": 1.0, "packaging_factor": 1.0,
             "notes": "Somente temperatura; multiplicadores de efeito iguais a 1."},
            {"scenario_id": "C25_DARK", "label": "25 °C, escuro; referência", "temperature_c": 25.0,
             "pH_factor": 1.0, "light_factor": 1.0, "oxygen_factor": 1.0, "packaging_factor": 1.0,
             "notes": "Cenário de referência artificial."},
            {"scenario_id": "C4_LIGHT_HYP", "label": "4 °C, luz (fator hipotético 1,5)", "temperature_c": 4.0,
             "pH_factor": 1.0, "light_factor": 1.5, "oxygen_factor": 1.0, "packaging_factor": 1.0,
             "notes": "Fator de luz hipotético para demonstrar sensibilidade; não é estimativa publicada."},
            {"scenario_id": "C4_LOW_O2_HYP", "label": "4 °C, menor exposição ao O₂ (fator hipotético 0,8)", "temperature_c": 4.0,
             "pH_factor": 1.0, "light_factor": 1.0, "oxygen_factor": 0.8, "packaging_factor": 1.0,
             "notes": "Multiplicador de degradação hipotético; precisa ser calibrado experimentalmente."},
            {"scenario_id": "C4_PH_HYP", "label": "4 °C, formulação/pH alternativo (fator hipotético 0,8)", "temperature_c": 4.0,
             "pH_factor": 0.8, "light_factor": 1.0, "oxygen_factor": 1.0, "packaging_factor": 1.0,
             "notes": "Efeito de pH artificialmente assumido para demonstrar o modelo; a direção real precisa ser testada."}
        ]
    })
    return cfg


def validate_simulation_config(cfg: dict) -> None:
    required_top = ["reference_temperature_c", "reference_half_life_days", "activation_energy_kj_mol", "initial_retention_pct", "days", "scenarios"]
    missing = [key for key in required_top if key not in cfg or cfg[key] is None]
    if missing:
        raise ValueError("Configuração de simulação incompleta: " + ", ".join(missing) + ". Edite data/config/simulation_parameters.json ou use --demo apenas para testar o fluxo.")
    if float(cfg["reference_half_life_days"]) <= 0:
        raise ValueError("reference_half_life_days deve ser maior que zero.")
    if float(cfg["activation_energy_kj_mol"]) < 0:
        raise ValueError("activation_energy_kj_mol não pode ser negativa.")
    if float(cfg["reference_temperature_c"]) <= -273.15:
        raise ValueError("A temperatura de referência deve ser maior que o zero absoluto.")
    days = cfg["days"]
    if not isinstance(days, list) or not days or any(float(day) < 0 for day in days):
        raise ValueError("days deve ser uma lista não vazia de tempos não negativos.")
    if not isinstance(cfg["scenarios"], list) or not cfg["scenarios"]:
        raise ValueError("scenarios precisa conter pelo menos um cenário.")
    factor_keys = ["pH_factor", "light_factor", "oxygen_factor", "packaging_factor"]
    for i, scenario in enumerate(cfg["scenarios"], 1):
        for key in ["scenario_id", "label", "temperature_c"]:
            if key not in scenario:
                raise ValueError(f"Cenário {i} não contém o campo obrigatório {key}.")
        if float(scenario["temperature_c"]) <= -273.15:
            raise ValueError(f"Temperatura inválida no cenário {scenario['scenario_id']}.")
        for factor in factor_keys:
            value = float(scenario.get(factor, 1.0))
            if value <= 0:
                raise ValueError(f"O multiplicador {factor} deve ser maior que zero no cenário {scenario['scenario_id']}.")


def simulate_scenarios(cfg: dict) -> pd.DataFrame:
    """Apply a first-order decay plus Arrhenius temperature factor and explicit user multipliers."""
    validate_simulation_config(cfg)
    gas_constant = 8.314462618  # J mol-1 K-1
    t_ref = float(cfg["reference_temperature_c"]) + 273.15
    k_ref = math.log(2.0) / float(cfg["reference_half_life_days"])
    ea = float(cfg["activation_energy_kj_mol"]) * 1000.0
    initial = float(cfg["initial_retention_pct"])
    records: list[dict] = []
    for scenario in cfg["scenarios"]:
        temp_c = float(scenario["temperature_c"])
        temp_k = temp_c + 273.15
        arrhenius_factor = math.exp((-ea / gas_constant) * (1.0 / temp_k - 1.0 / t_ref))
        modifiers = {key: float(scenario.get(key, 1.0)) for key in ["pH_factor", "light_factor", "oxygen_factor", "packaging_factor"]}
        modifier_total = math.prod(modifiers.values())
        k = k_ref * arrhenius_factor * modifier_total
        half_life = math.log(2.0) / k if k > 0 else math.inf
        for day in cfg["days"]:
            retention = initial * math.exp(-k * float(day))
            records.append({
                "data_origin": "SIMULATION_ONLY",
                "scenario_id": scenario["scenario_id"],
                "scenario_label": scenario["label"],
                "temperature_c": temp_c,
                "day": float(day),
                "initial_retention_pct": initial,
                "retention_pct_simulated": retention,
                "k_per_day_simulated": k,
                "half_life_days_simulated": half_life,
                "arrhenius_factor": arrhenius_factor,
                **modifiers,
                "combined_factor": modifier_total,
                "scenario_notes": scenario.get("notes", ""),
                "model_notice": "SIMULADO; não é medição, previsão validada nem recomendação de prazo de validade"
            })
    return pd.DataFrame(records)


def plot_simulation(results: pd.DataFrame, out_dir: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))
    for label, group in results.groupby("scenario_label", sort=False):
        group = group.sort_values("day")
        ax.plot(group["day"], group["retention_pct_simulated"], marker="o", label=label)
    ax.set_xlabel("Tempo simulado (dias)")
    ax.set_ylabel("Retenção simulada (%)")
    ax.set_title("Simulação de cenários — modelo hipotético, não dados de laboratório")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    path = out_dir / "simulation_retention.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def simulate(root: Path, demo: bool = False) -> None:
    config_path = root / "data" / "config" / "simulation_parameters.json"
    output_dir = root / "data" / "simulation"
    output_dir.mkdir(parents=True, exist_ok=True)
    if demo:
        cfg = _demo_simulation_config()
    else:
        if not config_path.exists():
            raise FileNotFoundError(f"Configuração não encontrada: {config_path}. Execute `python anthocyanin_lab.py init --dir .`.")
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
    results = simulate_scenarios(cfg)
    csv_path = output_dir / ("simulation_demo_results.csv" if demo else "simulation_results.csv")
    plot_path = plot_simulation(results, output_dir)
    results.to_csv(csv_path, index=False)
    parameters_path = output_dir / ("simulation_demo_parameters_used.json" if demo else "simulation_parameters_used.json")
    parameters_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = results.groupby(["scenario_id", "scenario_label", "temperature_c"], as_index=False).agg(
        k_per_day_simulated=("k_per_day_simulated", "first"),
        half_life_days_simulated=("half_life_days_simulated", "first"),
        retention_day_0_pct=("retention_pct_simulated", "first"),
        retention_last_day_pct=("retention_pct_simulated", "last"),
    )
    title = "Simulador de estabilidade de antocianinas"
    notice = str(cfg.get("purpose", "SIMULAÇÃO; não são resultados experimentais.")) + " Todos os multiplicadores de pH/luz/oxigênio/embalagem são pressupostos do modelo até serem fundamentados ou calibrados com dados reais. Não use para declarar validade ou segurança."
    report_path = output_dir / ("simulation_demo_report.html" if demo else "simulation_report.html")
    generate_html_report(title, notice, [("Comparação resumida dos cenários", summary), ("Resultados por tempo (simulados)", results)],
                         [("Retenção modelada por cenário", plot_path)], report_path)
    print("SIMULAÇÃO concluída. Nenhum arquivo de medições laboratoriais foi alterado.")
    print(f"CSV: {csv_path.resolve()}")
    print(f"Gráfico: {plot_path.resolve()}")
    print(f"Relatório HTML: {report_path.resolve()}")
    print("AVISO: saída simulada; não é dado experimental nem previsão validada.")

def analyze(root: Path) -> None:
    raw = root / "data" / "raw"
    out = root / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    stability_path = raw / "stability_measurements.csv"
    color_path = raw / "color_measurements.csv"
    if not stability_path.exists() or not color_path.exists():
        raise FileNotFoundError("Templates ausentes. Execute primeiro: python anthocyanin_lab.py init --dir .")

    stability_input = pd.read_csv(stability_path)
    if stability_input.empty:
        raise ValueError(f"{stability_path} ainda não contém dados. Preencha-o com medições reais.")
    stability = calculate_tac(stability_input)
    stability.to_csv(out / "stability_processed.csv", index=False)
    kinetics = fit_kinetics(stability)
    kinetics.to_csv(out / "kinetics_summary.csv", index=False)

    plot_retention(stability, out)
    concentration_plot = plot_tac_concentration(stability, out)
    kinetics_plot = plot_kinetics_summary(kinetics, out)

    summary = stability.groupby(["formulation", "storage_condition", "day"], dropna=False).agg(
        tac_mean_mg_c3g_L=("tac_mg_c3g_L", "mean"),
        tac_sd_mg_c3g_L=("tac_mg_c3g_L", "std"),
        retention_mean_pct=("retention_pct", "mean"),
        retention_sd_pct=("retention_pct", "std"),
        n_measurements=("tac_mg_c3g_L", "count"),
    ).reset_index()
    summary.to_csv(out / "stability_summary.csv", index=False)

    color_summary = pd.DataFrame()
    color_input = pd.read_csv(color_path)
    color_plot = out / "color_drift_deltaE.png"
    hue_plot = None
    if not color_input.empty:
        color = add_hsv_and_delta_e(color_input)
        color.to_csv(out / "color_processed.csv", index=False)
        plot_delta_e(color, out)
        hue_plot = plot_hue_by_ph(color, out)
        color_summary = color.groupby(["formulation", "storage_condition", "day", "target_pH"], dropna=False).agg(
            mean_hue_deg=("hue_deg", "mean"), sd_hue_deg=("hue_deg", "std"),
            mean_saturation=("saturation_0_1", "mean"), mean_value=("value_0_1", "mean"),
            mean_delta_e=("delta_e_cie76_vs_day0", "mean"), n_color_measurements=("hue_deg", "count")
        ).reset_index()
        color_summary.to_csv(out / "color_summary.csv", index=False)
    else:
        print("Aviso: color_measurements.csv está vazio; análise de cor ignorada nesta execução.")

    visual_images: list[tuple[str, Path]] = [("Retenção de antocianinas (%)", out / "anthocyanin_retention.png")]
    if concentration_plot:
        visual_images.append(("Concentração de antocianinas", concentration_plot))
    if kinetics_plot:
        visual_images.append(("Constantes cinéticas (ajuste exploratório)", kinetics_plot))
    if not color_input.empty and color_plot.exists():
        visual_images.append(("Mudança de cor ΔE CIE76", color_plot))
    if hue_plot:
        visual_images.append(("Matiz versus pH", hue_plot))
    report_path = out / "results_dashboard.html"
    generate_html_report(
        "Painel de resultados experimentais — extrato de repolho roxo",
        "Este relatório resume apenas as medições contidas em data/raw. Ajustes cinéticos e métricas de cor são exploratórios; verifique controles, unidades, réplicas independentes e pressupostos antes de tirar conclusões.",
        [("Resumo de estabilidade por formulação, armazenamento e dia", summary),
         ("Parâmetros cinéticos por lote", kinetics),
         ("Resumo de cor por pH e dia", color_summary)],
        visual_images, report_path
    )
    print(f"Análise concluída. Resultados em: {out.resolve()}")
    print("Tabelas: stability_processed.csv, stability_summary.csv, kinetics_summary.csv")
    print("Painel visual: results_dashboard.html")
    print("Gráficos: anthocyanin_retention.png, tac_concentration.png; kinetics_rate_constants.png quando calculável")
    if not color_input.empty:
        print("Também: color_processed.csv, color_summary.csv, color_drift_deltaE.png e color_hue_by_pH.png quando aplicável")
    literature_path = raw / "literature_records.csv"
    if literature_path.exists() and not pd.read_csv(literature_path).empty:
        print("Nota: literature_records.csv continua separado e não foi combinado automaticamente com dados do laboratório.")
    print("Simulações ficam separadas em data/simulation/ e nunca são misturadas a data/processed/.")


ML_NUMERIC_FEATURES = [
    "temperature_c", "day", "initial_pH", "pH_day", "headspace_ratio_pct"
]
ML_CATEGORICAL_FEATURES = [
    "formulation", "storage_condition", "light_condition", "oxygen_condition",
    "container_material", "preservative_or_additive", "assay_method", "instrument"
]
ML_ALLOWED_TARGETS = ["retention_pct", "tac_mg_c3g_L", "delta_e_cie76_vs_day0"]


def train_ml_model(root: Path, target: str = "retention_pct",
                   include_literature: bool = False) -> None:
    """Train an exploratory model on experimental observations only, grouped by independent batch."""
    try:
        from sklearn.compose import ColumnTransformer
        from sklearn.dummy import DummyRegressor
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import GroupKFold, cross_val_predict
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder
        import joblib
    except ImportError as exc:
        raise ValueError("Dependência ausente. Execute: python -m pip install -r requirements.txt") from exc

    if target not in ML_ALLOWED_TARGETS:
        raise ValueError("Alvo inválido. Escolha: " + ", ".join(ML_ALLOWED_TARGETS))
    source = root / "data" / "raw" / "ml_observations.csv"
    if not source.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {source}. Execute `python anthocyanin_lab.py init --dir .`.")
    data = pd.read_csv(source)
    required = {"data_origin", "batch_id", "independent_batch", target}
    missing = required - set(data.columns)
    if missing:
        raise ValueError("Colunas obrigatórias ausentes em ml_observations.csv: " + ", ".join(sorted(missing)))
    if data.empty:
        raise ValueError("ml_observations.csv está vazio. Insira observações experimentais reais antes de treinar.")

    origins = data["data_origin"].astype(str).str.strip().str.upper()
    experimental = data.loc[origins.eq("EXPERIMENTAL")].copy()
    literature = data.loc[origins.eq("LITERATURE")].copy()
    if experimental.empty and (not include_literature or literature.empty):
        found = sorted(origins.dropna().unique().tolist())
        raise ValueError(
            "Nenhuma linha EXPERIMENTAL disponível. Literatura e simulações não são incluídas automaticamente. "
            f"Origens encontradas: {found}"
        )

    if include_literature:
        if literature.empty:
            raise ValueError("A opção --include-literature exige linhas explicitamente mapeadas com data_origin=LITERATURE.")
        if "study_id" not in data.columns:
            raise ValueError("Para inclusão explícita de literatura, adicione study_id a ml_observations.csv.")
        study_ids = literature["study_id"].astype("string").str.strip()
        if study_ids.isna().any() or study_ids.eq("").any():
            raise ValueError("Preencha study_id em todas as linhas LITERATURE para evitar vazamento entre estudos.")
        literature_studies = study_ids.nunique()
        if literature_studies < 5:
            raise ValueError(
                f"Apenas {literature_studies} estudos bibliográficos independentes; são necessários pelo menos 5 "
                "para qualquer validação agrupada com inclusão de literatura."
            )
        selected = pd.concat([experimental, literature], ignore_index=True)
        selected["data_origin"] = selected["data_origin"].astype(str).str.strip().str.upper()
    else:
        selected = experimental.copy()
        selected["data_origin"] = "EXPERIMENTAL"

    selected[target] = pd.to_numeric(selected[target], errors="coerce")
    for col in ML_NUMERIC_FEATURES:
        if col in selected.columns:
            selected[col] = pd.to_numeric(selected[col], errors="coerce")
    selected = selected.loc[selected[target].notna()].copy()
    if len(selected) < 10:
        raise ValueError(f"Apenas {len(selected)} observações válidas para {target}; são necessárias pelo menos 10 para este fluxo exploratório.")
    if include_literature:
        usable_studies = selected.loc[selected["data_origin"] == "LITERATURE", "study_id"].nunique()
        if usable_studies < 5:
            raise ValueError(
                f"Restaram apenas {usable_studies} estudos com alvo {target}; são necessários pelo menos 5 "
                "estudos com observações utilizáveis para validação agrupada."
            )

    experimental_mask = selected["data_origin"].eq("EXPERIMENTAL")
    exp_group_values = selected.loc[experimental_mask, "independent_batch"].astype("string").str.strip()
    use_batch_id = exp_group_values.isna() | exp_group_values.eq("")
    exp_group_values = exp_group_values.where(
        ~use_batch_id, selected.loc[experimental_mask, "batch_id"].astype("string").str.strip()
    )
    if exp_group_values.isna().any() or exp_group_values.eq("").any():
        raise ValueError("Preencha independent_batch ou batch_id em todas as linhas experimentais.")

    group_values = pd.Series(index=selected.index, dtype="string")
    group_values.loc[experimental_mask] = "EXPERIMENTAL:" + exp_group_values.astype(str)
    literature_mask = selected["data_origin"].eq("LITERATURE")
    if literature_mask.any():
        study_ids = selected.loc[literature_mask, "study_id"].astype("string").str.strip()
        if study_ids.isna().any() or study_ids.eq("").any():
            raise ValueError("Preencha study_id em todas as linhas LITERATURE para evitar vazamento entre estudos.")
        group_values.loc[literature_mask] = "LITERATURE:" + study_ids
    if group_values.isna().any() or group_values.eq("").any():
        raise ValueError("Origem inválida para treino: use EXPERIMENTAL ou LITERATURE (com inclusão explícita).")
    selected["_cv_group"] = group_values.astype(str)
    experimental_groups = selected.loc[experimental_mask, "_cv_group"].nunique()
    if experimental_groups < 3:
        raise ValueError(f"Foram encontrados apenas {experimental_groups} lotes experimentais independentes. São necessários pelo menos 3.")
    if include_literature and literature_studies < 5:
        raise ValueError("São necessários pelo menos 5 estudos independentes para validação agrupada de literatura.")
    n_groups = selected["_cv_group"].nunique()

    numeric_features = [c for c in ML_NUMERIC_FEATURES if c in selected.columns and selected[c].notna().any()]
    categorical_features = [c for c in ML_CATEGORICAL_FEATURES if c in selected.columns and selected[c].notna().any()]
    features = numeric_features + categorical_features
    if not features:
        raise ValueError("Nenhuma variável preditora disponível. Preencha temperatura, tempo, pH inicial e/ou fatores de armazenamento no CSV.")

    X = selected[features].copy()
    y = selected[target].astype(float)
    groups = selected["_cv_group"]
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])
    transformers = []
    if numeric_features:
        transformers.append(("numeric", numeric_pipe, numeric_features))
    if categorical_features:
        transformers.append(("categorical", categorical_pipe, categorical_features))
    preprocess = ColumnTransformer(transformers=transformers, remainder="drop")
    model = Pipeline([
        ("preprocess", preprocess),
        ("model", RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1))
    ])
    baseline = Pipeline([
        ("preprocess", preprocess),
        ("model", DummyRegressor(strategy="mean"))
    ])

    n_splits = min(5, n_groups)
    cv = GroupKFold(n_splits=n_splits)
    # Each batch is held out as a group to reduce leakage between timepoints from the same batch.
    predictions = cross_val_predict(model, X, y, groups=groups, cv=cv, n_jobs=1)
    baseline_predictions = cross_val_predict(baseline, X, y, groups=groups, cv=cv, n_jobs=1)
    def metrics(actual, predicted):
        return {
            "MAE": float(mean_absolute_error(actual, predicted)),
            "RMSE": float(np.sqrt(mean_squared_error(actual, predicted))),
            "R2_pooled": float(r2_score(actual, predicted)) if len(actual) >= 2 else None,
        }
    model_metrics = metrics(y, predictions)
    baseline_metrics = metrics(y, baseline_predictions)

    out = root / "data" / "ml"
    out.mkdir(parents=True, exist_ok=True)
    pred_frame = selected[[c for c in ["record_id", "data_origin", "study_id", "batch_id", "independent_batch", "formulation", "storage_condition", "day", target] if c in selected.columns]].copy()
    pred_frame["cv_group"] = groups.to_numpy()
    pred_frame["prediction_group_cv"] = predictions
    pred_frame["baseline_group_cv"] = baseline_predictions
    pred_frame["residual_model"] = y.to_numpy() - predictions
    pred_frame.to_csv(out / "cross_validated_predictions.csv", index=False)

    report = {
        "status": "EXPLORATORY_ONLY",
        "target": target,
        "data_source": str(source),
        "training_rows": int(len(selected)),
        "independent_groups": int(n_groups),
        "cv_method": f"GroupKFold({n_splits}) grouped by study_id for LITERATURE and independent_batch (fallback batch_id) for EXPERIMENTAL",
        "features_numeric": numeric_features,
        "features_categorical": categorical_features,
        "random_forest": model_metrics,
        "mean_baseline": baseline_metrics,
        "interpretation": "Compare MAE/RMSE with the mean baseline. A lower error is better. Exploratory grouped metrics are not proof of generalization; assess domain shift and use independent prospective studies before scientific claims.",
        "data_policy": (
            "Literature inclusion was explicitly requested. Literature rows must be manually mapped into ml_observations.csv; "
            "GroupKFold keeps every study together. Domain shift remains and metrics are exploratory."
            if include_literature else
            "Only data_origin=EXPERIMENTAL was used. LITERATURE, SIMULATION_ONLY, and other rows were excluded."
        ),
        "domain_shift_warning": (
            "Domain shift: published studies differ in matrix, method, units, and protocols; performance across this mixture is not "
            "generalization to the user's formulation."
            if include_literature else ""
        ),
    }
    (out / "ml_metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    model.fit(X, y)
    joblib.dump({"pipeline": model, "target": target, "features": features, "training_groups": sorted(groups.unique().tolist()), "warning": "Exploratory model; validate externally before use."}, out / f"model_{target}.joblib")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(y, predictions)
    lo = float(min(y.min(), np.min(predictions)))
    hi = float(max(y.max(), np.max(predictions)))
    if lo == hi:
        hi = lo + 1.0
    ax.plot([lo, hi], [lo, hi], linestyle="--")
    ax.set_xlabel(f"Valor observado: {target}")
    ax.set_ylabel("Previsão fora do lote (validação agrupada)")
    ax.set_title("ML exploratório — observado versus previsto")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    plot_path = out / "observed_vs_predicted.png"
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    metric_table = pd.DataFrame([
        {"model": "RandomForestRegressor", **model_metrics},
        {"model": "Baseline (média de treino)", **baseline_metrics},
    ])
    metric_table.to_csv(out / "ml_metrics.csv", index=False)
    html_path = out / "ml_report.html"
    generate_html_report(
        f"Relatório exploratório de aprendizado de máquina — {target}",
        "Apenas dados com data_origin=EXPERIMENTAL foram usados. Métricas por validação agrupada são exploratórias e não comprovam desempenho futuro. Não use este modelo para declarar prazo de validade ou segurança.",
        [("Métricas de validação agrupada", metric_table), ("Configuração e limitações", pd.DataFrame([report]))],
        [("Observado versus previsto", plot_path)], html_path
    )
    if include_literature:
        print("Treinamento exploratório concluído com literatura incluída por opção explícita e mapeamento manual.")
    else:
        print("Treinamento exploratório concluído; somente dados EXPERIMENTAL foram usados.")
    print(f"Observações: {len(selected)} | grupos independentes: {n_groups} | validação: GroupKFold({n_splits})")
    if include_literature:
        print("AVISO DE DOMÍNIO: literatura incluída explicitamente; diferenças de matriz/método/unidade limitam a interpretação.")
    print(f"Métricas: {(out / 'ml_metrics.csv').resolve()}")
    print(f"Previsões de validação: {(out / 'cross_validated_predictions.csv').resolve()}")
    print(f"Gráfico: {plot_path.resolve()}")
    print(f"Relatório HTML: {html_path.resolve()}")
    print(f"Modelo exploratório salvo: {(out / f'model_{target}.joblib').resolve()}")
    print("AVISO: modelo exploratório; valide com novos lotes independentes antes de qualquer conclusão científica.")

def validate_literature_data(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load literature tables and reject incomplete, untraceable, or misclassified rows."""
    lit_dir = root / "data" / "literature"
    studies_path = lit_dir / "literature_studies.csv"
    measurements_path = lit_dir / "literature_measurements.csv"
    evidence_path = lit_dir / "literature_evidence.csv"

    for path in (studies_path, measurements_path, evidence_path):
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de literatura não encontrado: {path}. Execute init primeiro.")

    studies = pd.read_csv(studies_path)
    measurements = pd.read_csv(measurements_path)
    evidence = pd.read_csv(evidence_path)
    for name, frame, required in (
        ("literature_studies.csv", studies, LITERATURE_STUDY_COLUMNS),
        ("literature_measurements.csv", measurements, LITERATURE_COLUMNS),
        ("literature_evidence.csv", evidence, LITERATURE_EVIDENCE_COLUMNS),
    ):
        missing = set(required) - set(frame.columns)
        if missing:
            raise ValueError(f"Colunas obrigatórias ausentes em {name}: " + ", ".join(sorted(missing)))

    if studies.empty:
        raise ValueError("literature_studies.csv está vazio.")
    if measurements.empty:
        raise ValueError("literature_measurements.csv está vazio.")
    required_study_values = ["study_id", "citation", "title", "doi", "url", "species", "matrix"]
    for column in required_study_values:
        if studies[column].isna().any() or studies[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"literature_studies.csv contém valores ausentes em {column}.")
    if studies["study_id"].duplicated().any():
        raise ValueError("study_id duplicado em literature_studies.csv.")
    study_ids = set(studies["study_id"].astype(str))
    for name, frame in (("literature_measurements.csv", measurements), ("literature_evidence.csv", evidence)):
        if not frame.empty:
            missing_ids = set(frame["study_id"].dropna().astype(str)) - study_ids
            if missing_ids or frame["study_id"].isna().any():
                raise ValueError(f"{name} referencia study_id ausente em literature_studies.csv: {sorted(missing_ids)}")

    required_measurement_values = [
        "study_id", "treatment_id", "source_url", "doi", "source_location",
        "matrix", "time_value", "time_unit", "measurement", "value", "value_unit",
        "data_origin", "reported_or_calculated",
    ]
    for column in required_measurement_values:
        if measurements[column].isna().any() or measurements[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"literature_measurements.csv contém valores ausentes em {column}.")
    if not measurements["data_origin"].astype(str).str.upper().eq("PUBLISHED_ARTICLE").all():
        raise ValueError("Dados da literatura devem ter data_origin=PUBLISHED_ARTICLE; não rotule literatura como laboratório ou simulação.")
    if not measurements["reported_or_calculated"].astype(str).str.lower().eq("reported").all():
        raise ValueError("literature_measurements.csv aceita apenas valores publicados; derivados devem ficar nas saídas processed.")

    measurement_numeric = ["time_value", "value", "standard_deviation", "replicate_count",
                           "temperature_c", "pH", "additive_concentration_pct"]
    for column in measurement_numeric:
        raw = measurements[column]
        has_value = raw.notna() & raw.astype(str).str.strip().ne("")
        parsed = pd.to_numeric(raw, errors="coerce")
        if (has_value & parsed.isna()).any():
            raise ValueError(f"{column} deve ser numérico quando informado em literature_measurements.csv.")
    numeric_columns(measurements, measurement_numeric)
    if measurements[["time_value", "value"]].isna().any().any():
        raise ValueError("time_value e value devem ser numéricos.")
    if (measurements["time_value"] < 0).any() or (measurements["value"] < 0).any():
        raise ValueError("time_value e value devem ser não negativos.")
    if measurements["standard_deviation"].dropna().lt(0).any():
        raise ValueError("standard_deviation não pode ser negativo.")
    if measurements["replicate_count"].dropna().le(0).any():
        raise ValueError("replicate_count deve ser positivo quando informado.")
    if (measurements["replicate_count"].dropna() % 1 != 0).any():
        raise ValueError("replicate_count deve ser inteiro quando informado.")
    valid_time_units = {"d", "day", "days", "dia", "dias", "h", "hour", "hours",
                        "hora", "horas", "min", "minute", "minutes", "minuto", "minutos",
                        "month", "months", "mês", "meses", "week", "weeks", "semana", "semanas"}
    bad_time_units = sorted(set(measurements["time_unit"].astype(str).str.strip().str.lower()) - valid_time_units)
    if bad_time_units:
        raise ValueError(f"Unidades de tempo não reconhecidas: {bad_time_units}.")
    anthocyanin = measurements["measurement"].astype(str).str.strip().str.lower().isin(
        {"anthocyanin content", "anthocyanin"}
    )
    valid_anthocyanin_units = {
        "mg cge/100 g fw",
        "mg equivalentes de cianidina-3-glicosídeo/l",
        "mg/l",
    }
    invalid_anthocyanin_units = measurements.loc[
        anthocyanin & ~measurements["value_unit"].astype(str).str.strip().str.lower().isin(valid_anthocyanin_units),
        "value_unit",
    ].drop_duplicates().tolist()
    if invalid_anthocyanin_units:
        raise ValueError(f"Unidade incompatível ou desconhecida para teor de antocianinas: {invalid_anthocyanin_units}.")
    if measurements["pH"].dropna().lt(0).any() or measurements["pH"].dropna().gt(14).any():
        raise ValueError("pH deve estar entre 0 e 14 quando informado.")
    duplicate_key = ["study_id", "treatment_id", "time_value", "time_unit", "measurement", "value_unit"]
    if measurements.duplicated(duplicate_key).any():
        raise ValueError("Combinação study/treatment/tempo/variável duplicada em literature_measurements.csv.")

    study_sources = studies.set_index("study_id")[["doi", "url"]]
    for name, frame in (("literature_measurements.csv", measurements), ("literature_evidence.csv", evidence)):
        if frame.empty:
            continue
        for _, row in frame.iterrows():
            source = study_sources.loc[row["study_id"]]
            if row["doi"] != source["doi"] or row["source_url"] != source["url"]:
                raise ValueError(f"DOI/URL não corresponde ao estudo em {name}: {row['study_id']}.")

    if not evidence.empty:
        for column in ("study_id", "evidence_type", "evidence_category", "evidence_text", "origin_source",
                       "source_url", "doi", "source_location"):
            if evidence[column].isna().any() or evidence[column].astype(str).str.strip().eq("").any():
                raise ValueError(f"literature_evidence.csv contém valores ausentes em {column}.")
        evidence_numeric = ["temperature_c", "pH", "time_value", "value",
                            "standard_deviation", "additive_concentration_pct",
                            "k_value", "half_life"]
        for column in evidence_numeric:
            raw = evidence[column]
            has_value = raw.notna() & raw.astype(str).str.strip().ne("")
            parsed = pd.to_numeric(raw, errors="coerce")
            if (has_value & parsed.isna()).any():
                raise ValueError(f"{column} deve ser numérico quando informado em literature_evidence.csv.")
        numeric_columns(evidence, evidence_numeric)
        if evidence["pH"].dropna().lt(0).any() or evidence["pH"].dropna().gt(14).any():
            raise ValueError("pH deve estar entre 0 e 14 quando informado em literature_evidence.csv.")
        if evidence["standard_deviation"].dropna().lt(0).any():
            raise ValueError("standard_deviation não pode ser negativo em literature_evidence.csv.")
        if evidence["time_value"].dropna().lt(0).any():
            raise ValueError("time_value não pode ser negativo em literature_evidence.csv.")
        evidence_with_time = evidence["time_value"].notna()
        if evidence.loc[evidence_with_time, "time_unit"].isna().any():
            raise ValueError("time_unit é obrigatório quando literature_evidence.csv informa time_value.")
        bad_evidence_units = sorted(
            set(evidence.loc[evidence_with_time, "time_unit"].astype(str).str.strip().str.lower())
            - valid_time_units
        )
        if bad_evidence_units:
            raise ValueError(f"Unidades de tempo não reconhecidas em literature_evidence.csv: {bad_evidence_units}.")

    return studies, measurements, evidence


def calculate_literature_retention(measurements: pd.DataFrame) -> pd.DataFrame:
    """Calculate retention from the earliest measured value within each compatible series."""
    df = measurements.copy()
    numeric_columns(df, ["time_value", "value"])
    retention_records = []

    keys = [
        "study_id", "treatment_id", "matrix", "measurement", "value_unit", "time_unit",
        "solvent", "temperature_c", "light_condition", "oxygen_condition", "package_material",
        "pH", "additive", "additive_concentration_pct",
    ]
    for _, group in df.groupby(keys, dropna=False, sort=False):
        group = group.sort_values("time_value")
        group = group.loc[group["value"].notna() & group["time_value"].notna()]
        if group.empty:
            continue

        initial = group.iloc[0]
        initial_value = float(initial["value"])
        if initial_value <= 0:
            continue
        for _, row in group.iterrows():
            retention_records.append({
                **row.to_dict(),
                "retention_pct": 100.0 * float(row["value"]) / initial_value,
                "retention_origin": "calculated",
                "reported_or_calculated_retention": "calculated",
                "retention_reference_time_value": float(initial["time_value"]),
                "retention_reference_value": initial_value,
                "retention_formula": "100 * value / measured_value_at_earliest_time",
            })

    if retention_records:
        return pd.DataFrame(retention_records)
    else:
        for column in ("retention_pct", "retention_reference_time_value", "retention_reference_value"):
            df[column] = np.nan
        df["retention_origin"] = ""
        df["reported_or_calculated_retention"] = ""
        df["retention_formula"] = ""
        return df


def fit_literature_kinetics(measurements: pd.DataFrame) -> pd.DataFrame:
    """Fit first-order kinetics only to individual, compatible, published time series."""
    df = measurements.copy()
    numeric_columns(df, ["time_value", "value"])
    records = []

    keys = [
        "study_id", "treatment_id", "matrix", "measurement", "value_unit", "time_unit",
        "solvent", "temperature_c", "light_condition", "oxygen_condition", "package_material",
        "pH", "additive", "additive_concentration_pct",
    ]
    for group_key, group in df.groupby(keys, dropna=False, sort=False):
        if not group["data_origin"].astype(str).str.upper().eq("PUBLISHED_ARTICLE").all():
            continue
        valid = group.loc[(group["value"] > 0) & group["time_value"].notna()].sort_values("time_value")
        if valid["time_value"].nunique() < 3:
            continue
        if valid["time_unit"].nunique() != 1 or valid["value_unit"].nunique() != 1:
            continue
        x = valid["time_value"].to_numpy(dtype=float)
        y = np.log(valid["value"].to_numpy(dtype=float))
        slope, intercept = np.polyfit(x, y, 1)
        predicted_log = intercept + slope * x
        residuals_log = y - predicted_log
        ss_res = float(np.sum(residuals_log ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
        k = -float(slope)
        residuals_original = valid["value"].to_numpy(dtype=float) - np.exp(predicted_log)
        row = dict(zip(keys, group_key))
        row.update({
            "n_timepoints": int(valid["time_value"].nunique()),
            "k_per_time_unit": k,
            "half_life_time_unit": math.log(2) / k if k > 0 else np.nan,
            "r_squared": r_squared,
            "residual_rmse_log": float(np.sqrt(np.mean(residuals_log ** 2))),
            "residual_rmse_value": float(np.sqrt(np.mean(residuals_original ** 2))),
            "fit_method": "OLS de ln(valor) versus tempo; dados publicados, sem conversão de unidades",
            "data_origin": "PUBLISHED_ARTICLE",
            "reported_or_calculated": "calculated_from_published_series",
            "source_url": valid.iloc[0]["source_url"],
            "doi": valid.iloc[0]["doi"],
            "source_location": valid.iloc[0]["source_location"],
            "fit_note": "Ajuste exploratório; comparar resíduos e validar pressupostos antes de interpretar.",
        })
        records.append(row)

    return pd.DataFrame(records)


def plot_literature_series(measurements: pd.DataFrame, out_dir: Path) -> Path:
    """Plot small multiples so incompatible matrices and units never share an axis."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    plot_data = measurements.dropna(subset=["value", "time_value"]).copy()
    if plot_data.empty:
        return None
    
    panel_keys = ["study_id", "matrix", "measurement", "value_unit", "time_unit"]
    panels = list(plot_data.groupby(panel_keys, dropna=False, sort=False))
    fig, axes = plt.subplots(max(1, len(panels)), 1, figsize=(12, 5 * max(1, len(panels))),
                             squeeze=False)
    for ax, (panel, panel_data) in zip(axes[:, 0], panels):
        for _, group in panel_data.groupby(["treatment_id"], dropna=False, sort=False):
            group = group.sort_values("time_value")
            row = group.iloc[0]
            display = lambda name: str(row[name]) if pd.notna(row[name]) else "not reported"
            conditions = [
                f"solvent={display('solvent')}",
                f"temperature={display('temperature_c')} °C",
                f"light={display('light_condition')}",
                f"oxygen={display('oxygen_condition')}",
                f"package={display('package_material')}",
            ]
            label = f"{row['treatment_id']}: " + ", ".join(conditions)
            ax.plot(group["time_value"], group["value"], marker="o", label=label, alpha=0.8)
        ax.set_title(f"{panel[0]} — {panel[1]} — {panel[2]}")
        ax.set_xlabel(f"Tempo ({panel[4]})")
        ax.set_ylabel(f"{panel[3]}")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.25)
    fig.suptitle("Séries publicadas — painéis separados por estudo, matriz, variável e unidade")
    fig.tight_layout()
    path = out_dir / "literature_time_series.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_literature_retention(measurements_with_retention: pd.DataFrame, out_dir: Path) -> Path:
    """Plot calculated retention using the same unit- and matrix-separated panels."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    plot_data = measurements_with_retention.dropna(subset=["retention_pct", "time_value"]).copy()
    if plot_data.empty:
        return None
    
    panel_keys = ["study_id", "matrix", "measurement", "value_unit", "time_unit"]
    panels = list(plot_data.groupby(panel_keys, dropna=False, sort=False))
    fig, axes = plt.subplots(max(1, len(panels)), 1, figsize=(12, 5 * max(1, len(panels))),
                             squeeze=False)
    for ax, (panel, panel_data) in zip(axes[:, 0], panels):
        for _, group in panel_data.groupby(["treatment_id"], dropna=False, sort=False):
            group = group.sort_values("time_value")
            row = group.iloc[0]
            display = lambda name: str(row[name]) if pd.notna(row[name]) else "not reported"
            label = (
                f"{row['treatment_id']}: solvent={display('solvent')}, "
                f"temperature={display('temperature_c')} °C, light={display('light_condition')}, "
                f"oxygen={display('oxygen_condition')}, package={display('package_material')}"
            )
            ax.plot(group["time_value"], group["retention_pct"], marker="o", label=label, alpha=0.8)
        ax.axhline(100, linestyle="--", linewidth=1, color="gray")
        ax.set_title(f"{panel[0]} — {panel[1]} — {panel[2]}")
        ax.set_xlabel(f"Tempo ({panel[4]})")
        ax.set_ylabel("Retenção calculada (%)")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.25)
    fig.suptitle("Retenção calculada — painéis separados por estudo, matriz, variável e unidade")
    fig.tight_layout()
    path = out_dir / "literature_retention.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def analyze_literature(root: Path) -> None:
    """Analyze literature data and generate HTML report."""
    lit_dir = root / "data" / "literature"
    out_dir = root / "data" / "literature" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    studies, measurements, evidence = validate_literature_data(root)
    
    measurements_with_retention = calculate_literature_retention(measurements)
    kinetics = fit_literature_kinetics(measurements)
    
    series_plot = plot_literature_series(measurements, out_dir)
    retention_plot = plot_literature_retention(measurements_with_retention, out_dir)
    
    measurements_with_retention.to_csv(out_dir / "literature_measurements_with_retention.csv", index=False)
    kinetics.to_csv(out_dir / "literature_kinetics.csv", index=False)
    
    images = []
    if series_plot:
        images.append(("Séries temporais da literatura", series_plot))
    if retention_plot:
        images.append(("Retenção calculada", retention_plot))
    
    title = "Análise de literatura — estabilidade de antocianinas"
    notice = ("Esta análise resume apenas dados publicados. Cada série é separada por tratamento, matriz, "
              "variável e unidade; não misture resultados com data/raw nem use literatura automaticamente no ML. "
              "Retenção e ajustes cinéticos são cálculos identificados nas saídas.")
    
    generate_html_report(
        title,
        notice,
        [("Estudos registrados", studies),
         ("Medições quantitativas", measurements_with_retention),
         ("Resumos cinéticos e evidências qualitativas", evidence),
         ("Ajustes cinéticos exploratórios", kinetics)],
        images,
        out_dir / "literature_report.html"
    )
    
    print(f"Análise de literatura concluída. Resultados em: {out_dir.resolve()}")
    print(f"Relatório HTML: {(out_dir / 'literature_report.html').resolve()}")
    print("AVISO: dados de literatura são de artigos publicados; não substituem medições próprias.")


def generate_experimental_plan(root: Path, concentrations: list[float] | None = None) -> None:
    """Generate experimental plan for stabilization hypothesis based on literature."""
    lit_dir = root / "data" / "literature"
    out_dir = root / "data" / "literature" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence_path = lit_dir / "literature_evidence.csv"
    if not evidence_path.exists():
        raise FileNotFoundError(f"Evidence file not found: {evidence_path}")

    dose_levels = list(dict.fromkeys([*(concentrations or [0.1, 0.2, 0.4, 0.6]), 0.4]))
    if any(not math.isfinite(concentration) or concentration <= 0 or concentration > 100
           for concentration in dose_levels):
        raise ValueError("As concentrações selecionadas devem ser maiores que 0 e até 100%.")

    plan_rows = []

    shared = {
        "target_pH": 3.0,
        "storage_temperature_c": 4,
        "light_condition": "dark",
        "storage_condition": "4C_DARK",
        "outcomes": "anthocyanin_retention; color_response_by_pH_discrimination",
        "color_outcome": "Medir separadamente durante armazenamento e no ensaio de discriminação de pH",
        "pH_discrimination_outcome": "Resposta de cor em níveis de desafio de pH pré-definidos no protocolo; avaliar separabilidade entre níveis sem confundir com retenção",
        "pH_outcome": "Medir pH inicial e durante armazenamento; todas as formulações devem iniciar no pH-alvo",
        "alert_rule": "Sinalizar pH fora da tolerância pré-registrada ou diferença de cor estatisticamente significativa versus controle; definir tolerância, teste e alfa antes do ensaio",
    }
    plan_rows.append({
        **shared,
        "formulation_id": "CONTROL_PH3",
        "additive": "none",
        "additive_concentration_pct": 0.0,
        "literature_reference": "",
        "notes": "Controle sem aditivo, acidificado ao mesmo pH inicial das formulações com ácido gálico.",
    })
    for concentration in dose_levels:
        is_reference = math.isclose(concentration, 0.4)
        plan_rows.append({
            **shared,
            "formulation_id": f"GALLIC_{concentration:g}",
            "additive": "gallic_acid",
            "additive_concentration_pct": concentration,
            "literature_reference": (
                "Lin et al. (2023), 0.4% em bebida simulada com ácido ascórbico; referência, "
                "não uma previsão para extrato aquoso de repolho"
            ) if is_reference else "",
            "notes": "Dose de referência bibliográfica." if is_reference else
                     "Dose selecionada para estimar experimentalmente a resposta à concentração.",
        })

    plan_df = pd.DataFrame(plan_rows)
    plan_path = out_dir / "experimental_plan_stabilization.csv"
    plan_df.to_csv(plan_path, index=False)

    print(f"Plano experimental gerado: {plan_path.resolve()}")
    print("Todas as formulações têm pH inicial-alvo 3,0, armazenamento a 4 °C no escuro e desfechos separados.")
    print("AVISO: a dose ótima será determinada experimentalmente; a referência de 0,4% veio de uma bebida simulada.")
    print("Compare cor e pH ao controle, aplicando tolerâncias e critérios estatísticos pré-definidos.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Análise inicial de extrato líquido de repolho roxo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="Criar modelos CSV sem sobrescrever arquivos existentes")
    init_parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Pasta do projeto (padrão: pasta atual)")
    analyze_parser = subparsers.add_parser("analyze", help="Calcular resultados reais, tabelas, gráficos e painel HTML")
    analyze_parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Pasta do projeto (padrão: pasta atual)")
    simulate_parser = subparsers.add_parser("simulate", help="Simular cenários hipotéticos sem alterar dados reais")
    simulate_parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Pasta do projeto (padrão: pasta atual)")
    simulate_parser.add_argument("--demo", action="store_true", help="Usar parâmetros artificiais apenas para testar o software")
    ml_parser = subparsers.add_parser("ml", help="Treinar com dados experimentais; literatura apenas com opt-in")
    ml_parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Pasta do projeto (padrão: pasta atual)")
    ml_parser.add_argument("--target", choices=ML_ALLOWED_TARGETS, default="retention_pct", help="Variável que o modelo tentará prever")
    ml_parser.add_argument(
        "--include-literature", action="store_true",
        help="Inclusão opt-in de linhas LITERATURE manualmente mapeadas; exige pelo menos 5 estudos e emite alerta de domínio",
    )
    literature_parser = subparsers.add_parser("literature", help="Analisar dados de literatura e gerar relatório HTML")
    literature_parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Pasta do projeto (padrão: pasta atual)")
    plan_parser = subparsers.add_parser("plan", help="Gerar plano experimental para hipótese de estabilização")
    plan_parser.add_argument("--dir", type=Path, default=Path.cwd(), help="Pasta do projeto (padrão: pasta atual)")
    plan_parser.add_argument("--concentrations", type=float, nargs="+", default=[0.1, 0.2, 0.4, 0.6],
                             help="Concentrações experimentais selecionadas de ácido gálico em %% (0,4%% é sempre incluído como referência)")
    args = parser.parse_args()
    try:
        if args.command == "init":
            make_templates(args.dir)
        elif args.command == "analyze":
            analyze(args.dir)
        elif args.command == "simulate":
            simulate(args.dir, demo=args.demo)
        elif args.command == "ml":
            train_ml_model(args.dir, target=args.target, include_literature=args.include_literature)
        elif args.command == "literature":
            analyze_literature(args.dir)
        elif args.command == "plan":
            generate_experimental_plan(args.dir, concentrations=args.concentrations)
    except (ValueError, FileNotFoundError, pd.errors.ParserError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
