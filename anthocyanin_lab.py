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
import shutil
import sys
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import t as student_t

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
LITERATURE_STATUS_COLUMNS = [
    "study_id", "doi", "treatment_id", "time_value", "time_unit", "measurement",
    "value_unit", "verification_status", "verified_source_location", "reviewed_on",
    "reviewer", "verification_notes",
]
LITERATURE_STATUS_KEY = [
    "study_id", "doi", "treatment_id", "time_value", "time_unit", "measurement", "value_unit",
]
LITERATURE_VERIFICATION_STATUSES = {"VERIFIED", "VERIFICATION_PENDING", "REJECTED"}

# --- Integracao Fase 3: classes de evidencia, visoes e base harmonizada ---
LITERATURE_EVIDENCE_CLASSES = {
    "QUANTITATIVE_MEASUREMENT",
    "PUBLISHED_KINETIC_PARAMETER",
    "QUALITATIVE_NARRATIVE",
}
LITERATURE_VIEWS = ("verified", "pending", "rejected", "combined")
VIEW_STATUS_SETS = {
    "verified": frozenset({"VERIFIED"}),
    "pending": frozenset({"VERIFICATION_PENDING"}),
    "rejected": frozenset({"REJECTED"}),
    "combined": frozenset({"VERIFIED", "VERIFICATION_PENDING"}),
}
VIEW_DIR_NAMES = {
    "verified": "verified",
    "pending": "pending_exploratory",
    "rejected": "rejected",
    "combined": "combined_exploratory",
}
HARMONIZED_CATALOG_RELATIVE = Path(
    "data/literature/processed/harmonized/harmonized_measurements.csv"
)
HARMONIZED_REQUIRED_COLUMNS = [
    "execution_id", "generated_on_utc", "observation_id", "source_record_id",
    "study_id", "treatment_id", "measurement", "value_original", "unit_original",
    "time_value_original", "time_unit_original", "doi", "source_url",
    "source_version", "source_locator", "source_locator_class", "provenance_class",
    "verification_status", "verification_note", "matrix_type", "species",
    "extraction_method", "solvent", "solvent_composition", "additive",
    "additive_concentration_pct", "pH", "temperature_c", "light_condition",
    "oxygen_condition", "package_material", "storage_conditions",
    "measurement_name", "standard_deviation", "replicate_count", "replicate_type",
    "normalization_formula", "normalized_value", "normalized_unit",
    "comparability_group", "exclusion_reason", "evidence_class", "evidence_type",
    "evidence_text", "k_value", "k_unit", "half_life", "half_life_unit", "formula",
    "data_origin", "reported_or_calculated", "notes",
]
ANALYSIS_MEASUREMENT_COLUMNS = [
    "study_id", "treatment_id", "source_url", "doi", "source_location", "matrix",
    "measurement", "value", "value_unit", "time_value", "time_unit", "solvent",
    "temperature_c", "light_condition", "oxygen_condition", "package_material",
    "pH", "additive", "additive_concentration_pct", "data_origin",
    "reported_or_calculated", "verification_status", "verification_note",
    "observation_id", "source_record_id", "evidence_class", "provenance_class",
    "comparability_group", "exclusion_reason", "standard_deviation",
    "replicate_count", "notes",
]
SERIES_GROUP_KEYS = [
    "study_id", "treatment_id", "matrix", "measurement", "value_unit", "time_unit",
    "solvent", "temperature_c", "light_condition", "oxygen_condition",
    "package_material", "pH", "additive", "additive_concentration_pct",
]
LITERATURE_FIT_COLUMNS = SERIES_GROUP_KEYS + [
    "n_timepoints", "k_per_time_unit", "half_life_time_unit", "r_squared",
    "residual_rmse_log", "residual_rmse_value", "fit_method", "data_origin",
    "reported_or_calculated", "source_url", "doi", "source_location",
    "verification_status", "fit_note",
]
LEGACY_OUTPUT_NAMES = [
    "literature_measurements_with_retention.csv",
    "literature_kinetics.csv",
    "literature_kinetic_model_comparison.csv",
    "literature_kinetic_parameter_uncertainty.csv",
    "literature_kinetic_concentration_uncertainty.csv",
    "literature_report.html",
    "literature_time_series.png",
    "literature_retention.png",
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
        "literature_verification_status.csv": LITERATURE_STATUS_COLUMNS,
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
    baseline = df["_baseline_specific"].combine_first(df["_baseline_shared"])
    invalid_baseline = baseline.notna() & (baseline <= 0)
    df["day0_tac_mg_c3g_L"] = baseline.mask(invalid_baseline)
    df = df.drop(columns=["_baseline_specific", "_baseline_shared"])
    df["retention_pct"] = 100.0 * df["tac_mg_c3g_L"] / df["day0_tac_mg_c3g_L"]
    df["qc_flag"] = ""
    df.loc[df["absorbance_difference"] < 0, "qc_flag"] = "A diferencial negativa: verificar branco, diluição e leitura"
    df.loc[baseline.isna(), "qc_flag"] = "Sem baseline válida no dia 0 para este grupo"
    df.loc[invalid_baseline, "qc_flag"] = (
        "Baseline nula ou negativa no dia 0; retenção não calculada"
    )
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
        valid = group.loc[
            (group["tac_mg_c3g_L"] > 0) & group["day"].notna() & (group["day"] != 0)
        ].copy()
        if isinstance(group_key, tuple) and len(group_key) == 3:
            batch_val, formulation_val, condition_val = group_key
            baseline_pool = stability.loc[
                (stability["batch_id"] == batch_val)
                & (stability["formulation"] == formulation_val)
                & (stability["day"] == 0)
                & stability["tac_mg_c3g_L"].notna()
            ]
            condition_baseline = baseline_pool.loc[baseline_pool["storage_condition"] == condition_val]
            use_base = condition_baseline if not condition_baseline.empty else baseline_pool
            if not use_base.empty:
                base_row = use_base.iloc[[0]].copy()
                base_row["tac_mg_c3g_L"] = use_base["tac_mg_c3g_L"].mean()
                base_row["day"] = 0
                if base_row.iloc[0]["tac_mg_c3g_L"] > 0:
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


def srgb_to_cielab(r: float, g: float, b: float) -> tuple:
    """Converte RGB sRGB (0-255) para coordenadas CIELAB sob iluminante D65.

    Implementa a conversao padrao sRGB (expansao de gamma) -> XYZ (primarias
    CIE D65) -> CIELAB, conforme formulas CIE 1976.

    Esta funcao cobre a lacuna RGB->CIELAB identificada no roadmap da Fase 5.
    Ela NAO e aplicada automaticamente pelo pipeline: L*, a*, b* medidos
    continuam sendo a unica origem aceita para ``delta_e_cie76_vs_day0``.
    Derivar L*, a*, b* de RGB exige decisao explicita apos validacao contra
    instrumento, e qualquer uso deve registrar a origem como derivada.

    Retorna (nan, nan, nan) para entradas ausentes ou fora de [0, 255].
    """
    try:
        values = (float(r), float(g), float(b))
    except (TypeError, ValueError):
        return (np.nan, np.nan, np.nan)
    if any(np.isnan(v) or v < 0 or v > 255 for v in values):
        return (np.nan, np.nan, np.nan)

    def _to_linear(channel: float) -> float:
        c = channel / 255.0
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    red_l, green_l, blue_l = (_to_linear(v) for v in values)
    # Primarias sRGB / iluminante CIE D65.
    x = 0.4124564 * red_l + 0.3575761 * green_l + 0.1804375 * blue_l
    y = 0.2126729 * red_l + 0.7151522 * green_l + 0.0721750 * blue_l
    z = 0.0193339 * red_l + 0.1191920 * green_l + 0.9503041 * blue_l

    # Branco de referencia D65 (CIE, normalizado para 1.0).
    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def _f(t: float) -> float:
        if t > 0.008856:
            return t ** (1.0 / 3.0)
        return 7.787 * t + 16.0 / 116.0

    fx, fy, fz = _f(x / xn), _f(y / yn), _f(z / zn)
    l_star = 116.0 * fy - 16.0
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)
    return (l_star, a_star, b_star)


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
    numeric_top = {
        key: float(cfg[key])
        for key in ("reference_temperature_c", "reference_half_life_days",
                    "activation_energy_kj_mol", "initial_retention_pct")
    }
    for key, value in numeric_top.items():
        if not math.isfinite(value):
            raise ValueError(f"{key} deve ser finito.")
    if numeric_top["reference_half_life_days"] <= 0:
        raise ValueError("reference_half_life_days deve ser maior que zero.")
    if numeric_top["activation_energy_kj_mol"] < 0:
        raise ValueError("activation_energy_kj_mol não pode ser negativa.")
    if numeric_top["reference_temperature_c"] <= -273.15:
        raise ValueError("A temperatura de referência deve ser maior que o zero absoluto.")
    if not 0 <= numeric_top["initial_retention_pct"] <= 100:
        raise ValueError("initial_retention_pct deve estar entre 0 e 100.")
    days = cfg["days"]
    if (not isinstance(days, list) or not days
            or any(not math.isfinite(float(day)) or float(day) < 0 for day in days)):
        raise ValueError("days deve ser uma lista não vazia de tempos não negativos.")
    if not isinstance(cfg["scenarios"], list) or not cfg["scenarios"]:
        raise ValueError("scenarios precisa conter pelo menos um cenário.")
    factor_keys = ["pH_factor", "light_factor", "oxygen_factor", "packaging_factor"]
    for i, scenario in enumerate(cfg["scenarios"], 1):
        for key in ["scenario_id", "label", "temperature_c"]:
            if key not in scenario:
                raise ValueError(f"Cenário {i} não contém o campo obrigatório {key}.")
        temperature = float(scenario["temperature_c"])
        if not math.isfinite(temperature) or temperature <= -273.15:
            raise ValueError(f"Temperatura inválida no cenário {scenario['scenario_id']}.")
        for factor in factor_keys:
            value = float(scenario.get(factor, 1.0))
            if not math.isfinite(value) or value <= 0:
                raise ValueError(
                    f"O multiplicador {factor} deve ser finito e maior que zero "
                    f"no cenário {scenario['scenario_id']}."
                )
        combined_factor = math.prod(float(scenario.get(key, 1.0)) for key in factor_keys)
        if not math.isfinite(combined_factor):
            raise ValueError(f"Produto de multiplicadores não finito no cenário {scenario['scenario_id']}.")


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
        exponent = (-ea / gas_constant) * (1.0 / temp_k - 1.0 / t_ref)
        if not math.isfinite(exponent) or exponent > math.log(sys.float_info.max):
            raise ValueError(f"Fator de Arrhenius não finito no cenário {scenario['scenario_id']}.")
        arrhenius_factor = math.exp(exponent)
        modifiers = {key: float(scenario.get(key, 1.0)) for key in ["pH_factor", "light_factor", "oxygen_factor", "packaging_factor"]}
        modifier_total = math.prod(modifiers.values())
        k = k_ref * arrhenius_factor * modifier_total
        if not math.isfinite(k) or k <= 0:
            raise ValueError(f"A constante cinética simulada não é finita no cenário {scenario['scenario_id']}.")
        half_life = math.log(2.0) / k
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

def _literature_verification_key(row: pd.Series | dict) -> tuple:
    def text(value: object) -> str:
        return str(value).strip().casefold()

    return (
        text(row["study_id"]),
        text(row["doi"]),
        text(row["treatment_id"]),
        float(row["time_value"]),
        text(row["time_unit"]),
        text(row["measurement"]),
        text(row["value_unit"]),
    )


def _load_literature_verification_status(
    lit_dir: Path, measurements: pd.DataFrame, include_pending: bool
) -> tuple[pd.DataFrame, dict[str, str]]:
    status_path = lit_dir / "literature_verification_status.csv"
    if not status_path.exists():
        raise FileNotFoundError(
            f"Manifesto de verificação ausente: {status_path}. "
            "Crie o manifesto lateral; os CSVs bibliográficos originais não serão alterados."
        )
    status = pd.read_csv(status_path, dtype={"time_unit": "string"})
    missing_columns = set(LITERATURE_STATUS_COLUMNS) - set(status.columns)
    if missing_columns:
        raise ValueError(
            "Colunas obrigatórias ausentes em literature_verification_status.csv: "
            + ", ".join(sorted(missing_columns))
        )

    if not status.empty:
        status_values = status["verification_status"].astype("string").str.strip().str.upper()
        if status_values.isna().any() or status_values.eq("").any():
            raise ValueError("Todo registro do manifesto precisa de verification_status explícito.")
        invalid_statuses = sorted(set(status_values) - LITERATURE_VERIFICATION_STATUSES)
        if invalid_statuses:
            raise ValueError(f"verification_status desconhecido no manifesto: {invalid_statuses}.")
        status["verification_status"] = status_values

    source_keys = [_literature_verification_key(row) for _, row in measurements.iterrows()]
    status_keys = [_literature_verification_key(row) for _, row in status.iterrows()]
    if len(set(source_keys)) != len(source_keys):
        raise ValueError("Chave de verificação duplicada em literature_measurements.csv.")
    if len(set(status_keys)) != len(status_keys):
        raise ValueError("Chave duplicada em literature_verification_status.csv.")
    source_key_set = set(source_keys)
    status_key_set = set(status_keys)
    missing_keys = source_key_set - status_key_set
    extra_keys = status_key_set - source_key_set
    if missing_keys or extra_keys:
        raise ValueError(
            f"Chaves do manifesto não correspondem às medições: "
            f"{len(missing_keys)} ausentes e {len(extra_keys)} sem medição correspondente."
        )

    for _, row in status.loc[status["verification_status"] == "VERIFIED"].iterrows():
        location = str(row["verified_source_location"]).strip()
        if (not location or "pending" in location.casefold()
                or "pendente" in location.casefold()):
            raise ValueError("Registros VERIFIED exigem localização primária específica e confirmada.")
        review_date = str(row["reviewed_on"]).strip()
        if not review_date or pd.isna(pd.to_datetime(review_date, format="%Y-%m-%d", errors="coerce")):
            raise ValueError("Registros VERIFIED exigem reviewed_on no formato ISO YYYY-MM-DD.")
        if pd.isna(row["reviewer"]) or not str(row["reviewer"]).strip():
            raise ValueError("Registros VERIFIED exigem reviewer identificado.")

    status_by_key = {
        key: row for key, (_, row) in zip(status_keys, status.iterrows())
    }
    annotated = measurements.copy()
    annotated["verification_status"] = [
        status_by_key[key]["verification_status"] for key in source_keys
    ]
    for column in ("verified_source_location", "reviewed_on", "reviewer", "verification_notes"):
        annotated[column] = [
            status_by_key[key][column] for key in source_keys
        ]

    study_status: dict[str, str] = {}
    for study_id, group in annotated.groupby("study_id", dropna=False):
        statuses = set(group["verification_status"])
        if statuses == {"VERIFIED"}:
            study_status[str(study_id)] = "VERIFIED"
        elif "VERIFICATION_PENDING" in statuses:
            study_status[str(study_id)] = "VERIFICATION_PENDING"
        else:
            study_status[str(study_id)] = "REJECTED"

    pending_count = int(annotated["verification_status"].eq("VERIFICATION_PENDING").sum())
    if pending_count:
        if include_pending:
            warnings.warn(
                f"Análise exploratória inclui {pending_count} registros VERIFICATION_PENDING; "
                "eles não são benchmarks aprovados.",
                UserWarning,
                stacklevel=2,
            )
            annotated = annotated.loc[
                annotated["verification_status"].isin(["VERIFIED", "VERIFICATION_PENDING"])
            ].copy()
        else:
            warnings.warn(
                f"{pending_count} registros VERIFICATION_PENDING foram excluídos da análise aprovada.",
                UserWarning,
                stacklevel=2,
            )
            annotated = annotated.loc[annotated["verification_status"] == "VERIFIED"].copy()
    else:
        annotated = annotated.loc[annotated["verification_status"] == "VERIFIED"].copy()
    return annotated, study_status


def validate_literature_data(
    root: Path, include_pending: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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

    measurements, study_status = _load_literature_verification_status(
        lit_dir, measurements, include_pending=include_pending
    )
    evidence["verification_status"] = evidence["study_id"].astype(str).map(study_status).fillna(
        "VERIFICATION_PENDING"
    )
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


def fit_literature_kinetics(
    measurements: pd.DataFrame, include_pending: bool = False
) -> pd.DataFrame:
    """Fit first-order kinetics only to individual, compatible, published time series."""
    df = measurements.copy()
    if "verification_status" not in df.columns:
        raise ValueError("Ajustes bibliográficos exigem verification_status validado pelo manifesto lateral.")
    statuses = df["verification_status"].astype("string").str.strip().str.upper()
    invalid_statuses = sorted(set(statuses.dropna()) - LITERATURE_VERIFICATION_STATUSES)
    if statuses.isna().any() or statuses.eq("").any() or invalid_statuses:
        raise ValueError(f"verification_status inválido nos dados cinéticos: {invalid_statuses}.")
    pending_count = int(statuses.eq("VERIFICATION_PENDING").sum())
    if pending_count and include_pending:
        warnings.warn(
            f"Ajuste cinético exploratório inclui {pending_count} registros VERIFICATION_PENDING.",
            UserWarning,
            stacklevel=2,
        )
        df = df.loc[statuses.isin(["VERIFIED", "VERIFICATION_PENDING"])].copy()
    else:
        if pending_count:
            warnings.warn(
                f"{pending_count} registros VERIFICATION_PENDING foram excluídos dos ajustes aprovados.",
                UserWarning,
                stacklevel=2,
            )
        df = df.loc[statuses.eq("VERIFIED")].copy()
    numeric_columns(df, ["time_value", "value"])
    records = []

    keys = [
        "study_id", "treatment_id", "matrix", "measurement", "value_unit", "time_unit",
        "solvent", "temperature_c", "light_condition", "oxygen_condition", "package_material",
        "pH", "additive", "additive_concentration_pct",
    ]
    for group_key, group in df.groupby(keys, dropna=False, sort=False):
        if (not group["data_origin"].astype(str).str.upper().eq("PUBLISHED_ARTICLE").all()
                or not group["verification_status"].eq("VERIFIED").all()
                and not (include_pending and group["verification_status"].eq("VERIFICATION_PENDING").all())):
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
            "verification_status": valid.iloc[0]["verification_status"],
            "fit_note": "Ajuste exploratório; comparar resíduos e validar pressupostos antes de interpretar.",
        })
        records.append(row)

    return pd.DataFrame(records)


def _fit_kinetic_model(model: str, times: Iterable[float], values: Iterable[float]) -> dict:
    """Fit a two-parameter decay model by least squares on the original value scale."""
    x = np.asarray(list(times), dtype=float)
    y = np.asarray(list(values), dtype=float)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("Tempos e valores devem ser vetores unidimensionais de mesmo tamanho.")
    if len(x) < 3 or len(np.unique(x)) < 3:
        raise ValueError("O ajuste cinético requer ao menos três tempos distintos.")
    if not np.isfinite(x).all() or not np.isfinite(y).all() or (y <= 0).any():
        raise ValueError("Tempos devem ser finitos e concentrações positivas e finitas.")

    elapsed = x - float(np.min(x))
    if model == "zero_order":
        equation = lambda time, initial, rate: initial - rate * time
        slope, intercept = np.polyfit(elapsed, y, 1)
        initial_guess = (max(float(intercept), np.finfo(float).eps), max(float(-slope), 1e-12))
        rate_name = "k0"
    elif model == "first_order":
        equation = lambda time, initial, rate: initial * np.exp(-rate * time)
        slope, intercept = np.polyfit(elapsed, np.log(y), 1)
        initial_guess = (max(float(np.exp(intercept)), np.finfo(float).eps),
                         max(float(-slope), 1e-12))
        elapsed_span = float(np.max(elapsed))
        endpoint_rate = -np.log(float(y[-1]) / float(y[0])) / elapsed_span
        saturation_rate = -np.log(np.finfo(float).tiny) / elapsed_span
        initial_guesses = [
            initial_guess,
            (float(y[0]), max(float(endpoint_rate), np.finfo(float).eps)),
            (float(y[0]), saturation_rate),
        ]
        rate_name = "k1"
    elif model == "second_order":
        equation = lambda time, initial, rate: initial / (1 + rate * initial * time)
        slope, intercept = np.polyfit(elapsed, 1 / y, 1)
        initial_guess = (max(float(1 / intercept), np.finfo(float).eps),
                         max(float(slope), 1e-12))
        rate_name = "k2"
    else:
        raise ValueError(f"Modelo cinético não suportado: {model}")

    if model != "first_order":
        initial_guesses = [initial_guess]

    candidates = []
    for guess in initial_guesses:
        try:
            parameters, _ = curve_fit(
                equation,
                elapsed,
                y,
                p0=guess,
                bounds=(0, np.inf),
                method="trf",
                x_scale="jac",
                max_nfev=50000,
            )
        except RuntimeError:
            continue
        predictions = equation(elapsed, *parameters)
        if not np.isfinite(parameters).all() or not np.isfinite(predictions).all():
            continue
        residuals = y - predictions
        sse = float(np.sum(residuals ** 2))
        if np.isfinite(sse):
            candidates.append((sse, parameters, predictions))
    if not candidates:
        raise RuntimeError(f"Nenhum ajuste cinético válido convergiu para o modelo {model}.")

    sse, parameters, predictions = min(candidates, key=lambda candidate: candidate[0])
    residuals = y - predictions
    n = len(y)
    parameter_count = 3  # Two fitted parameters and the residual variance.
    if n > parameter_count + 1 and sse > 0:
        aicc = float(
            n * np.log(sse / n)
            + 2 * parameter_count
            + 2 * parameter_count * (parameter_count + 1) / (n - parameter_count - 1)
        )
    else:
        aicc = np.nan

    return {
        "initial_concentration": float(parameters[0]),
        "rate_parameter_name": rate_name,
        "rate_parameter_value": float(parameters[1]),
        "predictions": predictions.tolist(),
        "residuals": residuals.tolist(),
        "rmse": float(np.sqrt(np.mean(residuals ** 2))),
        "mae": float(np.mean(np.abs(residuals))),
        "sse": sse,
        "aicc": aicc,
    }


def compare_literature_kinetic_models(
    measurements: pd.DataFrame, studies: pd.DataFrame, include_pending: bool = False
) -> pd.DataFrame:
    """Compare simple decay models without pooling literature series or extrapolating."""
    required_measurement_columns = {
        "study_id", "treatment_id", "source_url", "doi", "source_location",
        "time_value", "time_unit", "measurement", "value", "value_unit",
        "data_origin", "verification_status",
    }
    missing = required_measurement_columns - set(measurements.columns)
    if missing:
        raise ValueError(f"Colunas ausentes para comparação cinética: {sorted(missing)}.")
    required_study_columns = {"study_id", "citation", "title", "doi", "url"}
    missing = required_study_columns - set(studies.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em metadados dos estudos: {sorted(missing)}.")
    if studies["study_id"].duplicated().any():
        raise ValueError("study_id duplicado em metadados dos estudos.")

    df = measurements.copy()
    if "verification_status" not in df.columns:
        raise ValueError("A comparação exige verification_status validado pelo manifesto lateral.")
    statuses = df["verification_status"].astype("string").str.strip().str.upper()
    invalid_statuses = sorted(set(statuses.dropna()) - LITERATURE_VERIFICATION_STATUSES)
    if statuses.isna().any() or statuses.eq("").any() or invalid_statuses:
        raise ValueError(f"verification_status inválido nos dados cinéticos: {invalid_statuses}.")
    pending_count = int(statuses.eq("VERIFICATION_PENDING").sum())
    if pending_count and include_pending:
        warnings.warn(
            f"A comparação cinética exploratória inclui {pending_count} registros VERIFICATION_PENDING.",
            UserWarning,
            stacklevel=2,
        )
        df = df.loc[statuses.isin(["VERIFIED", "VERIFICATION_PENDING"])].copy()
    else:
        if pending_count:
            warnings.warn(
                f"{pending_count} registros VERIFICATION_PENDING foram excluídos da comparação cinética.",
                UserWarning,
                stacklevel=2,
            )
        df = df.loc[statuses.eq("VERIFIED")].copy()

    numeric_columns(df, ["time_value", "value"])
    grouping_keys = [
        "study_id", "treatment_id", "source_url", "doi", "source_location",
        "matrix", "measurement", "value_unit", "time_unit", "solvent",
        "temperature_c", "light_condition", "oxygen_condition", "package_material",
        "pH", "additive", "additive_concentration_pct", "data_origin",
        "verification_status",
    ]
    missing_grouping_columns = set(grouping_keys) - set(df.columns)
    if missing_grouping_columns:
        raise ValueError(f"Colunas ausentes para separar séries: {sorted(missing_grouping_columns)}.")

    study_metadata = studies.set_index("study_id")
    model_definitions = {
        "zero_order": "C(t)=C0-k0*(t-t_min)",
        "first_order": "C(t)=C0*exp(-k1*(t-t_min))",
        "second_order": "C(t)=C0/(1+k2*C0*(t-t_min))",
    }
    output_columns = grouping_keys + [
        "citation", "title", "study_url", "model", "model_equation",
        "initial_concentration_fit", "initial_concentration_unit", "rate_parameter",
        "rate_parameter_value", "rate_parameter_unit", "n_observations", "n_timepoints",
        "fit_time_min", "fit_time_max", "observed_times_json", "observed_values_json",
        "predicted_values_json", "residuals_json", "residual_rmse", "residual_mae",
        "residual_sse", "aicc", "aicc_assumption", "model_selection_status",
        "fit_method", "analysis_scope", "reported_or_calculated", "calculation_formula",
        "extrapolation_policy", "uncertainty_status", "uncertainty_note",
        "uncertainty_recommendation",
    ]
    records = []
    for group_key, group in df.groupby(grouping_keys, dropna=False, sort=False):
        row = dict(zip(grouping_keys, group_key))
        study_id = row["study_id"]
        if study_id not in study_metadata.index:
            raise ValueError(f"Metadados ausentes para estudo cinético: {study_id}.")
        study = study_metadata.loc[study_id]
        if str(row["doi"]).strip().casefold() != str(study["doi"]).strip().casefold():
            raise ValueError(f"DOI das medições não corresponde ao registro do estudo {study_id}.")
        if str(row["source_url"]).strip() != str(study["url"]).strip():
            raise ValueError(f"URL das medições não corresponde ao registro do estudo {study_id}.")
        if str(row["data_origin"]).upper() != "PUBLISHED_ARTICLE":
            continue

        valid = group.sort_values("time_value")
        x = valid["time_value"].to_numpy(dtype=float)
        y = valid["value"].to_numpy(dtype=float)
        if len(np.unique(x)) < 3:
            continue
        if not np.isfinite(x).all() or not np.isfinite(y).all() or (y <= 0).any():
            raise ValueError(f"Série cinética inválida para {study_id}/{row['treatment_id']}.")

        for model, formula in model_definitions.items():
            fit = _fit_kinetic_model(model, x, y)
            if model == "zero_order":
                rate_unit = f"{row['value_unit']} per {row['time_unit']}"
            elif model == "first_order":
                rate_unit = f"1/{row['time_unit']}"
            else:
                rate_unit = f"1/({row['value_unit']}*{row['time_unit']})"
            status = row["verification_status"]
            records.append({
                **row,
                "citation": study["citation"],
                "title": study["title"],
                "study_url": study["url"],
                "model": model,
                "model_equation": formula,
                "initial_concentration_fit": fit["initial_concentration"],
                "initial_concentration_unit": row["value_unit"],
                "rate_parameter": fit["rate_parameter_name"],
                "rate_parameter_value": fit["rate_parameter_value"],
                "rate_parameter_unit": rate_unit,
                "n_observations": len(x),
                "n_timepoints": len(np.unique(x)),
                "fit_time_min": float(np.min(x)),
                "fit_time_max": float(np.max(x)),
                "observed_times_json": json.dumps(x.tolist(), separators=(",", ":")),
                "observed_values_json": json.dumps(y.tolist(), separators=(",", ":")),
                "predicted_values_json": json.dumps(fit["predictions"], separators=(",", ":")),
                "residuals_json": json.dumps(fit["residuals"], separators=(",", ":")),
                "residual_rmse": fit["rmse"],
                "residual_mae": fit["mae"],
                "residual_sse": fit["sse"],
                "aicc": fit["aicc"],
                "aicc_assumption": "Gaussian iid residuals on original value scale; descriptive only",
                "model_selection_status": (
                    "INSUFFICIENT_SAMPLE_SIZE_FOR_AICC"
                    if not np.isfinite(fit["aicc"])
                    else "DESCRIPTIVE_AICC_IID_ASSUMPTION_ONLY"
                ),
                "fit_method": "Nonlinear least squares on original value scale",
                "verification_status": status,
                "analysis_scope": (
                    "EXPLORATORY_SOURCE_PENDING"
                    if status == "VERIFICATION_PENDING"
                    else "SOURCE_VERIFIED"
                ),
                "reported_or_calculated": "CALCULATED",
                "calculation_formula": formula,
                "extrapolation_policy": "NONE_WITHIN_OBSERVED_INTERVAL",
                "uncertainty_status": "NOT_ESTIMATED_NO_INDEPENDENT_REPLICATES",
                "uncertainty_note": (
                    "Temporal observations are not independent replicates; source data provide "
                    "no independent lot-level replication or standard errors for this series."
                ),
                "uncertainty_recommendation": (
                    "With independent lots, use a lot-level cluster bootstrap or a hierarchical "
                    "nonlinear model with lot effects; do not resample timepoints as independent."
                ),
            })

    return pd.DataFrame(records, columns=output_columns)


def estimate_literature_kinetic_parameter_uncertainty(
    comparison: pd.DataFrame, confidence_level: float = 0.95
) -> pd.DataFrame:
    """Create conditional, exploratory parameter intervals from stored model fits."""
    required = {
        "model", "initial_concentration_fit", "rate_parameter_value", "n_observations",
        "observed_times_json", "observed_values_json", "predicted_values_json",
    }
    missing = required - set(comparison.columns)
    if missing:
        raise ValueError(f"Colunas ausentes para incerteza cinética: {sorted(missing)}.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level deve estar entre 0 e 1.")

    report = comparison.copy()
    interval_columns = [
        "initial_concentration_se", "initial_concentration_ci_lower",
        "initial_concentration_ci_upper", "rate_parameter_se",
        "rate_parameter_ci_lower", "rate_parameter_ci_upper",
    ]
    for column in interval_columns:
        report[column] = np.nan
    report["parameter_ci_confidence_level"] = confidence_level
    report["parameter_residual_degrees_of_freedom"] = np.nan
    report["parameter_uncertainty_method"] = "NOT_ESTIMATED"
    report["parameter_uncertainty_status"] = ""
    report["parameter_uncertainty_assumptions"] = (
        "Conditional nonlinear least squares covariance; Gaussian, homoscedastic, "
        "independent residuals; local linear approximation."
    )
    report["parameter_uncertainty_limitations"] = (
        "Exploratory parameter intervals only; temporal dependence, no independent lot "
        "replicates, pending source verification, and no external validation. "
        "Intervals are not calibrated prediction intervals."
    )

    jacobian_functions = {
        "zero_order": lambda time, initial, rate: np.column_stack(
            (np.ones_like(time), -time)
        ),
        "first_order": lambda time, initial, rate: np.column_stack(
            (np.exp(-rate * time), -time * initial * np.exp(-rate * time))
        ),
        "second_order": lambda time, initial, rate: np.column_stack(
            (
                1 / (1 + rate * initial * time) ** 2,
                -(initial ** 2) * time / (1 + rate * initial * time) ** 2,
            )
        ),
    }

    for index, row in report.iterrows():
        times = np.asarray(json.loads(row["observed_times_json"]), dtype=float)
        values = np.asarray(json.loads(row["observed_values_json"]), dtype=float)
        predictions = np.asarray(json.loads(row["predicted_values_json"]), dtype=float)
        n = len(values)
        if (
            times.ndim != 1
            or predictions.ndim != 1
            or len(times) != n
            or len(predictions) != n
            or not np.isfinite(times).all()
            or not np.isfinite(values).all()
            or not np.isfinite(predictions).all()
        ):
            raise ValueError("Tempos, valores e previsões devem ser vetores finitos de mesmo tamanho.")
        if int(row["n_observations"]) != n:
            raise ValueError("n_observations não corresponde às observações armazenadas.")

        degrees_of_freedom = n - 2
        report.at[index, "parameter_residual_degrees_of_freedom"] = degrees_of_freedom
        if n <= 3:
            report.at[index, "parameter_uncertainty_status"] = (
                "INSUFFICIENT_FOR_ROBUST_MODEL_SELECTION"
            )
            report.at[index, "parameter_uncertainty_limitations"] += (
                " Only three observations are available; no parameter intervals are reported "
                "because uncertainty and model selection are not robustly estimable."
            )
            continue

        model = row["model"]
        if model not in jacobian_functions:
            raise ValueError(f"Modelo cinético não suportado para incerteza: {model}.")
        elapsed = times - float(np.min(times))
        initial = float(row["initial_concentration_fit"])
        rate = float(row["rate_parameter_value"])
        jacobian = jacobian_functions[model](elapsed, initial, rate)
        residuals = values - predictions
        residual_variance = float(residuals @ residuals / degrees_of_freedom)
        information = jacobian.T @ jacobian
        if np.linalg.matrix_rank(information) < 2:
            report.at[index, "parameter_uncertainty_status"] = "COVARIANCE_UNAVAILABLE"
            report.at[index, "parameter_uncertainty_limitations"] += (
                " The local parameter Jacobian is rank deficient."
            )
            continue

        try:
            covariance = residual_variance * np.linalg.inv(information)
        except np.linalg.LinAlgError:
            report.at[index, "parameter_uncertainty_status"] = "COVARIANCE_UNAVAILABLE"
            report.at[index, "parameter_uncertainty_limitations"] += (
                " The local covariance matrix could not be inverted."
            )
            continue
        if not np.isfinite(covariance).all() or np.any(np.diag(covariance) < 0):
            report.at[index, "parameter_uncertainty_status"] = "COVARIANCE_UNAVAILABLE"
            report.at[index, "parameter_uncertainty_limitations"] += (
                " The local covariance matrix is non-finite or invalid."
            )
            continue

        standard_errors = np.sqrt(np.diag(covariance))
        critical_value = float(student_t.ppf((1 + confidence_level) / 2, degrees_of_freedom))
        report.at[index, "initial_concentration_se"] = standard_errors[0]
        report.at[index, "initial_concentration_ci_lower"] = initial - critical_value * standard_errors[0]
        report.at[index, "initial_concentration_ci_upper"] = initial + critical_value * standard_errors[0]
        report.at[index, "rate_parameter_se"] = standard_errors[1]
        report.at[index, "rate_parameter_ci_lower"] = rate - critical_value * standard_errors[1]
        report.at[index, "rate_parameter_ci_upper"] = rate + critical_value * standard_errors[1]
        report.at[index, "parameter_uncertainty_method"] = (
            "Local Jacobian covariance with Student-t Wald intervals"
        )
        report.at[index, "parameter_uncertainty_status"] = (
            "EXPLORATORY_CONDITIONAL_INTERVALS"
        )

    return report


def estimate_literature_kinetic_concentration_intervals(
    comparison: pd.DataFrame,
    confidence_level: float = 0.95,
    n_simulations: int = 10000,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Simulate conditional mean-response and individual-observation intervals."""
    required = {
        "study_id", "treatment_id", "model", "initial_concentration_fit",
        "rate_parameter_value", "n_observations", "time_unit", "value_unit",
        "observed_times_json", "observed_values_json", "predicted_values_json",
    }
    missing = required - set(comparison.columns)
    if missing:
        raise ValueError(f"Colunas ausentes para intervalos de concentração: {sorted(missing)}.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level deve estar entre 0 e 1.")
    if not isinstance(n_simulations, int) or n_simulations < 1000:
        raise ValueError("n_simulations deve ser um inteiro maior ou igual a 1000.")

    interval_columns = [
        "time_value", "observed_value", "mean_response_estimate",
        "mean_response_ci_lower", "mean_response_ci_upper",
        "individual_observation_prediction",
        "individual_observation_pi_lower", "individual_observation_pi_upper",
        "interval_confidence_level", "concentration_interval_method",
        "concentration_uncertainty_status", "concentration_interval_assumptions",
        "concentration_interval_limitations", "parameter_residual_degrees_of_freedom",
        "requested_simulations", "accepted_parameter_draws",
    ]
    excluded = {
        "observed_times_json", "observed_values_json", "predicted_values_json",
        "residuals_json",
    }
    output_columns = [column for column in comparison.columns if column not in excluded]
    output_columns.extend(interval_columns)
    records = []
    rng = np.random.default_rng(random_seed)
    alpha = (1 - confidence_level) / 2
    assumptions = (
        "Conditional parametric simulation: local least-squares covariance; Gaussian, "
        "homoscedastic and independent residuals; scaled-chi-square residual variance; "
        "local linear approximation; parameter draws conditioned on the nonnegative "
        "fit constraints."
    )
    limitations = (
        "Exploratory conditional intervals only; temporal dependence is not represented, "
        "there are no independent lot replicates, source verification remains pending, "
        "and there is no external calibration. Not suitable as calibrated forecasts."
    )
    model_functions = {
        "zero_order": lambda elapsed, initial, rate: initial - rate * elapsed,
        "first_order": lambda elapsed, initial, rate: initial * np.exp(-rate * elapsed),
        "second_order": lambda elapsed, initial, rate: (
            initial / (1 + rate * initial * elapsed)
        ),
    }
    jacobian_functions = {
        "zero_order": lambda elapsed, initial, rate: np.column_stack(
            (np.ones_like(elapsed), -elapsed)
        ),
        "first_order": lambda elapsed, initial, rate: np.column_stack(
            (
                np.exp(-rate * elapsed),
                -elapsed * initial * np.exp(-rate * elapsed),
            )
        ),
        "second_order": lambda elapsed, initial, rate: np.column_stack(
            (
                1 / (1 + rate * initial * elapsed) ** 2,
                -(initial ** 2) * elapsed / (1 + rate * initial * elapsed) ** 2,
            )
        ),
    }

    for _, row in comparison.iterrows():
        times = np.asarray(json.loads(row["observed_times_json"]), dtype=float)
        values = np.asarray(json.loads(row["observed_values_json"]), dtype=float)
        stored_predictions = np.asarray(json.loads(row["predicted_values_json"]), dtype=float)
        n = len(values)
        if (
            times.ndim != 1
            or values.ndim != 1
            or stored_predictions.ndim != 1
            or len(times) != n
            or len(stored_predictions) != n
            or not np.isfinite(times).all()
            or not np.isfinite(values).all()
            or not np.isfinite(stored_predictions).all()
        ):
            raise ValueError(
                "Tempos, valores e previsões devem ser vetores finitos de mesmo tamanho."
            )
        if int(row["n_observations"]) != n:
            raise ValueError("n_observations não corresponde às observações armazenadas.")

        model = row["model"]
        if model not in model_functions:
            raise ValueError(f"Modelo cinético não suportado para intervalos: {model}.")
        initial = float(row["initial_concentration_fit"])
        rate = float(row["rate_parameter_value"])
        elapsed = times - float(np.min(times))
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            mean_estimate = model_functions[model](elapsed, initial, rate)
        fitted_parameters_valid = (
            math.isfinite(initial)
            and math.isfinite(rate)
            and initial > 0
            and rate >= 0
        )
        fitted_domain_valid = (
            np.isfinite(mean_estimate).all() and (mean_estimate > 0).all()
        )
        fit_values_valid = (
            fitted_parameters_valid and fitted_domain_valid
        )
        residuals = values - mean_estimate
        degrees_of_freedom = n - 2

        status = "INSUFFICIENT_FOR_CONDITIONAL_INTERVALS"
        mean_lower = mean_upper = prediction_lower = prediction_upper = np.nan
        accepted_count = 0
        method = "NOT_ESTIMATED"
        if n > 3 and fit_values_valid:
            jacobian = jacobian_functions[model](elapsed, initial, rate)
            information = jacobian.T @ jacobian
            residual_variance = float(residuals @ residuals / degrees_of_freedom)
            if (
                np.linalg.matrix_rank(information) == 2
                and math.isfinite(residual_variance)
                and residual_variance > 0
            ):
                try:
                    inverse_information = np.linalg.inv(information)
                    cholesky = np.linalg.cholesky(inverse_information)
                except np.linalg.LinAlgError:
                    cholesky = None
                if cholesky is not None and np.isfinite(cholesky).all():
                    parameter_draws = []
                    residual_sd_draws = []
                    for _ in range(20):
                        variance_draws = (
                            residual_variance * degrees_of_freedom
                            / rng.chisquare(degrees_of_freedom, size=n_simulations)
                        )
                        standard_normals = rng.standard_normal((n_simulations, 2))
                        draws = np.array([initial, rate]) + (
                            standard_normals @ cholesky.T
                        ) * np.sqrt(variance_draws)[:, None]
                        draw_initial = draws[:, 0]
                        draw_rate = draws[:, 1]
                        if model == "zero_order":
                            draw_predictions = (
                                draw_initial[:, None] - draw_rate[:, None] * elapsed
                            )
                        elif model == "first_order":
                            draw_predictions = draw_initial[:, None] * np.exp(
                                -draw_rate[:, None] * elapsed
                            )
                        else:
                            draw_predictions = draw_initial[:, None] / (
                                1 + draw_rate[:, None] * draw_initial[:, None] * elapsed
                            )
                        valid = (
                            (draw_initial > 0)
                            & (draw_rate >= 0)
                            & np.isfinite(draw_predictions).all(axis=1)
                            & (draw_predictions > 0).all(axis=1)
                        )
                        parameter_draws.extend(draws[valid].tolist())
                        residual_sd_draws.extend(np.sqrt(variance_draws[valid]).tolist())
                        if len(parameter_draws) >= n_simulations:
                            break

                    accepted_count = min(len(parameter_draws), n_simulations)
                    if accepted_count == n_simulations:
                        draws = np.asarray(parameter_draws[:n_simulations], dtype=float)
                        residual_sd = np.asarray(
                            residual_sd_draws[:n_simulations], dtype=float
                        )
                        simulated_mean = model_functions[model](
                            elapsed[None, :], draws[:, 0, None], draws[:, 1, None]
                        )
                        simulated_individual = simulated_mean + (
                            rng.standard_normal(simulated_mean.shape)
                            * residual_sd[:, None]
                        )
                        mean_lower, mean_upper = np.quantile(
                            simulated_mean, [alpha, 1 - alpha], axis=0
                        )
                        prediction_lower, prediction_upper = np.quantile(
                            simulated_individual, [alpha, 1 - alpha], axis=0
                        )
                        status = "EXPLORATORY_CONDITIONAL_SIMULATION"
                        method = (
                            "Parametric Monte Carlo: local covariance parameter draws "
                            "and Gaussian residual prediction"
                        )
                    else:
                        status = "INSUFFICIENT_VALID_PARAMETER_DRAWS"
                        limitations += (
                            " Nonnegative parameter/domain constraints prevented enough "
                            "valid simulation draws."
                        )
                else:
                    status = "COVARIANCE_UNAVAILABLE"
            else:
                status = "COVARIANCE_UNAVAILABLE"
        elif n > 3:
            if fitted_parameters_valid and np.isfinite(mean_estimate).all():
                status = "MODEL_OUTSIDE_PHYSICAL_DOMAIN"
                limitations += (
                    " The fitted model predicts a nonpositive concentration at one or "
                    "more observed times; intervals are withheld for the series."
                )
            else:
                status = "INVALID_FITTED_PARAMETERS"

        if status == "EXPLORATORY_CONDITIONAL_SIMULATION":
            mean_lower_values = mean_lower
            mean_upper_values = mean_upper
            prediction_lower_values = prediction_lower
            prediction_upper_values = prediction_upper
        else:
            mean_lower_values = np.full(n, np.nan)
            mean_upper_values = np.full(n, np.nan)
            prediction_lower_values = np.full(n, np.nan)
            prediction_upper_values = np.full(n, np.nan)

        for position, time_value in enumerate(times):
            record = {key: value for key, value in row.items() if key not in excluded}
            record.update({
                "time_value": float(time_value),
                "observed_value": float(values[position]),
                "mean_response_estimate": float(mean_estimate[position]),
                "mean_response_ci_lower": float(mean_lower_values[position]),
                "mean_response_ci_upper": float(mean_upper_values[position]),
                "individual_observation_prediction": float(mean_estimate[position]),
                "individual_observation_pi_lower": float(prediction_lower_values[position]),
                "individual_observation_pi_upper": float(prediction_upper_values[position]),
                "interval_confidence_level": confidence_level,
                "concentration_interval_method": method,
                "concentration_uncertainty_status": status,
                "concentration_interval_assumptions": assumptions,
                "concentration_interval_limitations": limitations,
                "parameter_residual_degrees_of_freedom": degrees_of_freedom,
                "requested_simulations": n_simulations,
                "accepted_parameter_draws": accepted_count,
            })
            records.append(record)

    return pd.DataFrame(records, columns=output_columns)


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


def load_harmonized_catalog(root: Path) -> pd.DataFrame:
    """Carrega e valida a base harmonizada derivada (Fase 2) como fonte da analise.

    Os CSVs brutos continuam sendo as fontes de dados: cada linha da base e
    conferida, linha a linha, contra o CSV bruto correspondente
    (source_record_id -> numero de linha). Qualquer divergencia interrompe a
    analise com instrucao de regeneracao; nada e corrigido silenciosamente.
    Nenhuma promocao de status acontece nesta camada: VERIFIED so e aceito com
    localizacao primaria especifica e confirmada.
    """
    catalog_path = root / HARMONIZED_CATALOG_RELATIVE
    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Base harmonizada ausente: {catalog_path}. "
            "Gere-a com: python tools/harmonize_literature.py --dir ."
        )
    catalog = pd.read_csv(catalog_path, dtype=str, keep_default_na=False)
    missing = set(HARMONIZED_REQUIRED_COLUMNS) - set(catalog.columns)
    if missing:
        raise ValueError(
            "Base harmonizada sem colunas obrigatorias: " + ", ".join(sorted(missing))
            + ". Regenere com tools/harmonize_literature.py."
        )
    if catalog.empty:
        raise ValueError("Base harmonizada vazia; regenere com tools/harmonize_literature.py.")

    statuses = catalog["verification_status"].str.strip().str.upper()
    if statuses.eq("").any():
        raise ValueError("Toda observacao da base harmonizada precisa de verification_status explicito.")
    invalid_statuses = sorted(set(statuses) - LITERATURE_VERIFICATION_STATUSES)
    if invalid_statuses:
        raise ValueError(f"verification_status fora do vocabulario do projeto: {invalid_statuses}.")
    catalog["verification_status"] = statuses

    classes = catalog["evidence_class"].str.strip()
    if classes.eq("").any():
        raise ValueError("Toda observacao da base harmonizada precisa de evidence_class.")
    invalid_classes = sorted(set(classes) - LITERATURE_EVIDENCE_CLASSES)
    if invalid_classes:
        raise ValueError(f"evidence_class desconhecida na base harmonizada: {invalid_classes}.")
    catalog["evidence_class"] = classes

    if not catalog["observation_id"].is_unique:
        raise ValueError("observation_id duplicado na base harmonizada.")
    if not catalog["source_record_id"].is_unique:
        raise ValueError("source_record_id duplicado na base harmonizada.")
    execution_ids = {value for value in catalog["execution_id"].str.strip() if value}
    if len(execution_ids) != 1:
        raise ValueError(
            "A base harmonizada deve conter exatamente um execution_id "
            "(uma unica execucao deterministica)."
        )

    verified_rows = catalog.loc[catalog["verification_status"] == "VERIFIED"]
    if not verified_rows.empty:
        locations = verified_rows["source_locator"].str.strip()
        folded = locations.str.casefold()
        unpinned = locations.eq("") | folded.str.contains("pendente") | folded.str.contains("pending")
        if unpinned.any():
            raise ValueError(
                "Promocao de status bloqueada: ha observacoes VERIFIED sem "
                "localizacao primaria especifica e confirmada na base harmonizada."
            )

    _check_catalog_against_raw_sources(root / "data" / "literature", catalog)
    return catalog


def _check_catalog_against_raw_sources(lit_dir: Path, catalog: pd.DataFrame) -> None:
    """Confere a base derivada contra os CSVs brutos (medições e evidencias).

    Compara por source_record_id (STUDY|L{n} / STUDY|E{n} -> linha do CSV, com
    cabecalho na linha 1). Falha = base desatualizada; a correcao e sempre a
    regeneracao, nunca edicao da base por esta camada.
    """

    def same_text(left: object, right: object) -> bool:
        return str(left).strip() == str(right).strip()

    def same_number(left: object, right: object) -> bool:
        try:
            return float(left) == float(right)
        except (TypeError, ValueError):
            return same_text(left, right)

    measurements_path = lit_dir / "literature_measurements.csv"
    evidence_path = lit_dir / "literature_evidence.csv"
    for path in (measurements_path, evidence_path):
        if not path.exists():
            raise FileNotFoundError(f"CSV bibliografico bruto ausente: {path}.")

    by_source = dict(zip(catalog["source_record_id"], catalog.to_dict("records")))

    raw_measurements = pd.read_csv(measurements_path, dtype=str, keep_default_na=False)
    expected_measurement_ids = set()
    for line_number, raw in enumerate(raw_measurements.to_dict("records"), start=2):
        source_id = f"{raw['study_id']}|L{line_number}"
        expected_measurement_ids.add(source_id)
        row = by_source.get(source_id)
        if row is None:
            raise ValueError(
                f"Base harmonizada nao contem a medicao {source_id}; "
                "regenere com tools/harmonize_literature.py."
            )
        for field, raw_key, catalog_key in (
            ("study_id", "study_id", "study_id"),
            ("treatment_id", "treatment_id", "treatment_id"),
            ("measurement", "measurement", "measurement"),
            ("value_unit", "value_unit", "unit_original"),
            ("time_unit", "time_unit", "time_unit_original"),
            ("data_origin", "data_origin", "data_origin"),
            ("reported_or_calculated", "reported_or_calculated", "reported_or_calculated"),
        ):
            if not same_text(raw[raw_key], row[catalog_key]):
                raise ValueError(
                    f"Divergencia entre CSV bruto e base harmonizada em {source_id} "
                    f"({field}); regenere com tools/harmonize_literature.py."
                )
        for field, raw_key, catalog_key in (
            ("value", "value", "value_original"),
            ("time_value", "time_value", "time_value_original"),
        ):
            if not same_number(raw[raw_key], row[catalog_key]):
                raise ValueError(
                    f"Divergencia de {field} entre CSV bruto e base harmonizada em "
                    f"{source_id}; regenere com tools/harmonize_literature.py."
                )
        if row["evidence_class"] != "QUANTITATIVE_MEASUREMENT":
            raise ValueError(f"{source_id} deve ser QUANTITATIVE_MEASUREMENT na base harmonizada.")
    catalog_measurement_ids = {sid for sid in catalog["source_record_id"] if "|L" in sid}
    if catalog_measurement_ids != expected_measurement_ids:
        raise ValueError(
            "A base harmonizada nao corresponde 1:1 as medicoes de "
            "literature_measurements.csv; regenere com tools/harmonize_literature.py."
        )

    raw_evidence = pd.read_csv(evidence_path, dtype=str, keep_default_na=False)
    for line_number, raw in enumerate(raw_evidence.to_dict("records"), start=2):
        if not any(str(value).strip() for value in raw.values()):
            continue
        source_id = f"{raw['study_id']}|E{line_number}"
        row = by_source.get(source_id)
        if row is None:
            raise ValueError(
                f"Base harmonizada nao contem a evidencia {source_id}; "
                "regenere com tools/harmonize_literature.py."
            )
        for field in ("study_id", "evidence_type", "evidence_text"):
            if not same_text(raw[field], row[field]):
                raise ValueError(
                    f"Divergencia entre CSV bruto e base harmonizada em {source_id} "
                    f"({field}); regenere com tools/harmonize_literature.py."
                )
        for field in ("k_value", "half_life", "value"):
            raw_number = str(raw[field]).strip()
            catalog_key = "value_original" if field == "value" else field
            catalog_number = str(row[catalog_key]).strip()
            if raw_number and not same_number(raw_number, catalog_number):
                raise ValueError(
                    f"Divergencia de {field} entre CSV bruto e base harmonizada em "
                    f"{source_id}; regenere com tools/harmonize_literature.py."
                )
            if not raw_number and catalog_number:
                raise ValueError(
                    f"Campo {field} presente na base mas ausente no bruto em {source_id}; "
                    "regenere com tools/harmonize_literature.py."
                )


def split_literature_views(catalog: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Particiona o catalogo harmonizado nas visoes cientificas do projeto."""
    if "verification_status" not in catalog.columns:
        raise ValueError("O catalogo precisa da coluna verification_status para separar visoes.")
    views: dict[str, pd.DataFrame] = {}
    for view_name in LITERATURE_VIEWS:
        allowed = VIEW_STATUS_SETS[view_name]
        selected = catalog.loc[catalog["verification_status"].isin(allowed)].copy()
        views[view_name] = selected.reset_index(drop=True)
    return views


def adapt_measurements_for_analysis(series_rows: pd.DataFrame) -> pd.DataFrame:
    """Adapta linhas quantitativas do catalogo ao esquema exigido pelos modelos."""
    if "evidence_class" in series_rows.columns:
        foreign = sorted(set(series_rows["evidence_class"].astype(str)) - {"QUANTITATIVE_MEASUREMENT"})
        if foreign:
            raise ValueError(
                "Somente QUANTITATIVE_MEASUREMENT entra nos ajustes; "
                f"classes incompativeis recebidas: {foreign}."
            )
    mapping = {
        "value_original": "value",
        "unit_original": "value_unit",
        "time_value_original": "time_value",
        "time_unit_original": "time_unit",
        "matrix_type": "matrix",
        "source_locator": "source_location",
    }
    adapted = series_rows.copy()
    for source_column, target_column in mapping.items():
        if source_column in adapted.columns:
            adapted[target_column] = adapted[source_column]
    numeric_columns(adapted, [
        "value", "time_value", "temperature_c", "pH",
        "additive_concentration_pct", "standard_deviation", "replicate_count",
    ])
    missing = set(ANALYSIS_MEASUREMENT_COLUMNS) - set(adapted.columns)
    if missing:
        raise ValueError(f"Colunas ausentes para analise quantitativa: {sorted(missing)}.")
    return adapted.reindex(columns=ANALYSIS_MEASUREMENT_COLUMNS)


def _series_eligible_mask(fit_input: pd.DataFrame) -> pd.Series:
    """Replica os criterios de elegibilidade dos ajustes por serie compativel."""
    values = pd.to_numeric(fit_input["value"], errors="coerce")
    times = pd.to_numeric(fit_input["time_value"], errors="coerce")
    group_codes, _ = pd.factorize(
        fit_input[SERIES_GROUP_KEYS].fillna("").astype(str).agg("|".join, axis=1), sort=False
    )
    frame = pd.DataFrame({"_value": values.to_numpy(), "_time": times.to_numpy(), "_code": group_codes})
    eligible_codes: dict[int, bool] = {}
    for code, group in frame.groupby("_code", sort=False):
        eligible_codes[int(code)] = bool(
            group["_value"].notna().all() and (group["_value"] > 0).all()
            and group["_time"].notna().all() and group["_time"].nunique() >= 3
        )
    per_group_units: dict[int, bool] = {}
    work = fit_input.assign(_code=group_codes)
    for code, group in work.groupby("_code", sort=False):
        per_group_units[int(code)] = bool(
            group["time_unit"].nunique() == 1 and group["value_unit"].nunique() == 1
        )
    mask = [
        eligible_codes[int(code)] and per_group_units[int(code)]
        for code in group_codes
    ]
    return pd.Series(mask, index=fit_input.index)


def build_inclusion_exclusion_summary(
    catalog: pd.DataFrame,
    view_name: str,
    selected: pd.DataFrame,
    fit_input: pd.DataFrame,
) -> pd.DataFrame:
    """Resume inclusao/exclusao por visao com motivos explicitos auditaveis."""
    if view_name not in LITERATURE_VIEWS:
        raise ValueError(f"Visao desconhecida: {view_name}.")
    eligible_count = int(_series_eligible_mask(fit_input).sum()) if not fit_input.empty else 0
    total_by_status = catalog["verification_status"].value_counts().to_dict()
    total_by_class = catalog["evidence_class"].value_counts().to_dict()
    selected_by_class = selected["evidence_class"].value_counts().to_dict() if not selected.empty else {}
    quantitative_selected = int(selected_by_class.get("QUANTITATIVE_MEASUREMENT", 0))
    rows = [
        ("catalog", "TOTAL_CATALOG_OBSERVATIONS", len(catalog),
         "Linhas da base harmonizada (derivada reproduzivel dos CSVs brutos)."),
        ("catalog", "STATUS_VERIFIED", int(total_by_status.get("VERIFIED", 0)),
         "Observacoes VERIFIED no catalogo."),
        ("catalog", "STATUS_VERIFICATION_PENDING", int(total_by_status.get("VERIFICATION_PENDING", 0)),
         "Observacoes VERIFICATION_PENDING no catalogo."),
        ("catalog", "STATUS_REJECTED", int(total_by_status.get("REJECTED", 0)),
         "Observacoes REJECTED no catalogo (preservadas, nunca ajustadas)."),
        ("view", "INCLUDED_IN_VIEW", len(selected),
         f"Observacoes com status em {sorted(VIEW_STATUS_SETS[view_name])} na visao '{view_name}'."),
        ("view", "EXCLUDED_BY_STATUS", len(catalog) - len(selected),
         "Observacoes fora do conjunto de status da visao."),
        ("class", "EVIDENCE_CLASS_QUANTITATIVE", int(total_by_class.get("QUANTITATIVE_MEASUREMENT", 0)),
         "Medicoes quantitativas no catalogo (inclui quantitativas transcritas de evidence)."),
        ("class", "EVIDENCE_CLASS_PUBLISHED_KINETIC", int(total_by_class.get("PUBLISHED_KINETIC_PARAMETER", 0)),
         "Parametros k/meia-vida publicados; nunca viram serie temporal."),
        ("class", "EVIDENCE_CLASS_QUALITATIVE", int(total_by_class.get("QUALITATIVE_NARRATIVE", 0)),
         "Narrativas qualitativas; nunca misturadas com medicoes numericas."),
        ("fit", "EXCLUDED_NOT_QUANTITATIVE", len(selected) - quantitative_selected,
         "Linhas da visao fora de QUANTITATIVE_MEASUREMENT (parametros/narrativas)."),
        ("fit", "ELIGIBLE_FOR_FIT", eligible_count,
         "Medicoes quantitativas em series compativeis (>=3 tempos, unidade unica)."),
        ("fit", "EXCLUDED_NO_TIME_SERIES", quantitative_selected - eligible_count,
         "Quantitativas sem serie ajustavel (tempo ausente, <3 tempos ou unidade mista)."),
    ]
    if view_name == "rejected":
        rows.append(("policy", "EXCLUDED_REJECTED_POLICY", len(selected),
                     "Visao rejected: registros preservados com motivo; excluidos de ajuste por padrao."))
    blocked_details: list[str] = []
    if not fit_input.empty:
        pooled_units = sorted({str(value) for value in fit_input["value_unit"].dropna().astype(str)})
        pooled_times = sorted({str(value) for value in fit_input["time_unit"].dropna().astype(str)})
        pooled_matrices = sorted({str(value) for value in fit_input["matrix"].dropna().astype(str)})
        blocked_details.append(
            "Curva unica entre estudos bloqueada: unidades "
            f"{pooled_units}, escalas {pooled_times}, matrizes {pooled_matrices}; "
            "ajustes somente dentro de grupos compativeis."
        )
    rows.append(("comparability", "CROSS_STUDY_POOLING_BLOCKED", len(blocked_details),
                 "; ".join(blocked_details) if blocked_details else "Sem insumo quantitativo nesta visao."))
    return pd.DataFrame(rows, columns=["stage", "reason", "count", "detail"])


def analyze_literature(
    root: Path,
    include_pending: bool = False,
    view: str | None = None,
) -> None:
    """Analisa a literatura a partir da base harmonizada, por visao cientifica."""
    resolved_view = view or ("combined" if include_pending else "verified")
    if resolved_view not in LITERATURE_VIEWS:
        raise ValueError(f"Visao desconhecida: {resolved_view}. Use uma de {list(LITERATURE_VIEWS)}.")
    if include_pending and resolved_view in ("verified", "rejected"):
        raise ValueError("include_pending=True exige a visao 'combined' (ou 'pending').")
    exploratory = resolved_view in ("pending", "combined")

    lit_dir = root / "data" / "literature"
    out_root = lit_dir / "processed"
    view_dir = out_root / "views" / VIEW_DIR_NAMES[resolved_view]
    view_dir.mkdir(parents=True, exist_ok=True)

    catalog = load_harmonized_catalog(root)
    views = split_literature_views(catalog)
    selected = views[resolved_view]

    studies_path = lit_dir / "literature_studies.csv"
    if not studies_path.exists():
        raise FileNotFoundError(f"Arquivo de literatura nao encontrado: {studies_path}. Execute init primeiro.")
    studies = pd.read_csv(studies_path)
    missing_study_columns = set(LITERATURE_STUDY_COLUMNS) - set(studies.columns)
    if missing_study_columns:
        raise ValueError(
            "Colunas obrigatorias ausentes em literature_studies.csv: " + ", ".join(sorted(missing_study_columns))
        )
    if studies.empty:
        raise ValueError("literature_studies.csv esta vazio.")

    pending_total = int(catalog["verification_status"].eq("VERIFICATION_PENDING").sum())
    if resolved_view == "verified":
        warnings.warn(
            f"{pending_total} registros VERIFICATION_PENDING foram excluidos da analise aprovada.",
            UserWarning,
            stacklevel=2,
        )
    elif exploratory:
        warnings.warn(
            f"Analise exploratoria '{resolved_view}' inclui {len(selected)} registros "
            "VERIFICATION_PENDING; eles nao sao benchmarks aprovados.",
            UserWarning,
            stacklevel=2,
        )
    else:
        warnings.warn(
            "Visao 'rejected': registros preservados com motivo e excluidos de ajuste por padrao.",
            UserWarning,
            stacklevel=2,
        )

    quantitative = selected.loc[selected["evidence_class"] == "QUANTITATIVE_MEASUREMENT"].copy()
    published_params = selected.loc[selected["evidence_class"] == "PUBLISHED_KINETIC_PARAMETER"].copy()
    narratives = selected.loc[selected["evidence_class"] == "QUALITATIVE_NARRATIVE"].copy()
    series_source = quantitative.loc[quantitative["source_record_id"].str.contains("|L", regex=False)].copy()
    if resolved_view == "rejected":
        series_source = series_source.iloc[0:0].copy()
    fit_input = adapt_measurements_for_analysis(series_source)
    fit_input["analysis_view"] = resolved_view

    measurements_with_retention = calculate_literature_retention(fit_input)
    kinetics = fit_literature_kinetics(fit_input, include_pending=exploratory)
    if kinetics.empty:
        kinetics = kinetics.reindex(columns=LITERATURE_FIT_COLUMNS)
    else:
        kinetics["analysis_view"] = resolved_view
    model_comparison = compare_literature_kinetic_models(fit_input, studies, include_pending=exploratory)
    if not model_comparison.empty:
        model_comparison["analysis_view"] = resolved_view
    parameter_uncertainty = estimate_literature_kinetic_parameter_uncertainty(model_comparison)
    concentration_uncertainty = estimate_literature_kinetic_concentration_intervals(model_comparison)

    summary = build_inclusion_exclusion_summary(catalog, resolved_view, selected, fit_input)
    series_plot = plot_literature_series(fit_input, view_dir)
    retention_plot = plot_literature_retention(measurements_with_retention, view_dir)

    selected.to_csv(view_dir / "catalog_view.csv", index=False)
    quantitative.to_csv(view_dir / "quantitative_measurements.csv", index=False)
    published_params.to_csv(view_dir / "published_kinetic_parameters.csv", index=False)
    narratives.to_csv(view_dir / "qualitative_narrative_evidence.csv", index=False)
    measurements_with_retention.to_csv(view_dir / "literature_measurements_with_retention.csv", index=False)
    kinetics.to_csv(view_dir / "literature_kinetics.csv", index=False)
    model_comparison.to_csv(view_dir / "literature_kinetic_model_comparison.csv", index=False)
    parameter_uncertainty.to_csv(view_dir / "literature_kinetic_parameter_uncertainty.csv", index=False)
    concentration_uncertainty.to_csv(view_dir / "literature_kinetic_concentration_uncertainty.csv", index=False)
    summary.to_csv(view_dir / "inclusion_exclusion_summary.csv", index=False)

    legacy_targets = {
        "literature_measurements_with_retention.csv": measurements_with_retention,
        "literature_kinetics.csv": kinetics,
        "literature_kinetic_model_comparison.csv": model_comparison,
        "literature_kinetic_parameter_uncertainty.csv": parameter_uncertainty,
        "literature_kinetic_concentration_uncertainty.csv": concentration_uncertainty,
        "inclusion_exclusion_summary.csv": summary,
    }
    for name, frame in legacy_targets.items():
        frame.to_csv(out_root / name, index=False)
    for png_name, source in (("literature_time_series.png", series_plot), ("literature_retention.png", retention_plot)):
        legacy_png = out_root / png_name
        if source is not None and Path(source).exists():
            shutil.copyfile(source, legacy_png)
        elif legacy_png.exists():
            legacy_png.unlink()

    images = []
    if series_plot:
        images.append(("Series temporais da literatura", series_plot))
    if retention_plot:
        images.append(("Retencao calculada", retention_plot))

    eligible = int(summary.loc[summary["reason"] == "ELIGIBLE_FOR_FIT", "count"].iloc[0])
    scope_phrase = {
        "verified": "Visao VERIFICADA (analysis_view='verified'): apenas registros VERIFIED; sem fallback para pendentes.",
        "pending": "Visao PENDENTE EXPLORATORIA (analysis_view='pending'): VERIFICATION_PENDING ainda nao confirmados.",
        "rejected": "Visao REJEITADA (analysis_view='rejected'): registros preservados com motivo; excluidos de ajuste.",
        "combined": "Visao COMBINADA EXPLORATORIA (analysis_view='combined'): VERIFIED + PENDING; REJECTED excluido.",
    }[resolved_view]
    count_phrase = (
        f"Catalogo: {len(catalog)} observacoes; incluidas nesta visao: {len(selected)}; "
        f"quantitativas na visao: {len(quantitative)}; elegiveis para ajuste: {eligible}; "
        f"parametros publicados: {len(published_params)}; narrativas: {len(narratives)}."
    )
    empty_phrase = ""
    if fit_input.empty or eligible == 0:
        empty_phrase = " Nenhuma serie elegivel nesta visao; saidas vazias validas."
    notice = (
        "Esta analise resume apenas dados publicados e le a BASE HARMONIZADA DERIVADA "
        "(os CSVs brutos continuam sendo as fontes; a base e conferida linha a linha). "
        "Cada serie e separada por tratamento, matriz, variavel e unidade; "
        "nao misture resultados com data/raw nem use literatura automaticamente no ML. "
        "Retencao e ajustes cineticos sao calculos identificados nas saidas. "
        + scope_phrase + " " + count_phrase + empty_phrase
    )
    title = f"Analise de literatura [{resolved_view}] - estabilidade de antocianinas"
    generate_html_report(
        title,
        notice,
        [("Estudos registrados", studies),
         ("Resumo de inclusao/exclusao", summary),
         ("Medicoes quantitativas (visao)", measurements_with_retention),
         ("Parametros cineticos publicados (nao ajustados)", published_params),
         ("Evidencias qualitativas/narrativas", narratives),
         ("Ajustes cineticos", kinetics)],
        images,
        view_dir / "literature_report.html",
    )
    shutil.copyfile(view_dir / "literature_report.html", out_root / "literature_report.html")

    print(f"Analise de literatura [{resolved_view}] concluida. Resultados em: {view_dir.resolve()}")
    print(f"Relatorio HTML: {(view_dir / 'literature_report.html').resolve()}")
    print("AVISO: dados de literatura sao de artigos publicados; nao substituem medicoes proprias.")
    if exploratory:
        print("AVISO EXPLICITO: analise exploratoria inclui registros VERIFICATION_PENDING.")
    if resolved_view == "verified" and (fit_input.empty or eligible == 0):
        print(f"AVISO: {pending_total} registros VERIFICATION_PENDING excluidos da analise aprovada.")


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
    literature_parser.add_argument(
        "--include-pending", action="store_true",
        help="Incluir linhas VERIFICATION_PENDING somente para exploração, com aviso explícito",
    )
    literature_parser.add_argument(
        "--view", choices=list(LITERATURE_VIEWS), default=None,
        help="Visão científica da base harmonizada (padrão: verified; --include-pending equivale a combined)",
    )
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
            analyze_literature(args.dir, include_pending=args.include_pending, view=args.view)
        elif args.command == "plan":
            generate_experimental_plan(args.dir, concentrations=args.concentrations)
    except (ValueError, FileNotFoundError, pd.errors.ParserError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
