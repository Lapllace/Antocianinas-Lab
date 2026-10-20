"""Interface Streamlit para o projeto de estabilidade de antocianinas.

Módulo de interface: consome os dados dos CSVs, expõe formulários de
registro, painel de análise, consulta, literatura, simulador e aprendizado
de máquina. As regras de validação, persistência, prevenção de duplicidade e
backup ficam em ``anthocyanin_persistence``; os cálculos científicos em
``anthocyanin_lab`` (reutilizados sempre que possível).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import anthocyanin_lab as lab
import anthocyanin_persistence as persist

# Caminhos dos artefatos do projeto.
STABILITY_CSV = ROOT / "data" / "raw" / "stability_measurements.csv"
COLOR_CSV = ROOT / "data" / "raw" / "color_measurements.csv"
MICRO_CSV = ROOT / "data" / "raw" / "microbiology_measurements.csv"
ML_CSV = ROOT / "data" / "raw" / "ml_observations.csv"
CONFIG_PATH = ROOT / "data" / "config" / "simulation_parameters.json"
BACKUPS_DIR = ROOT / "data" / "backups"

st.set_page_config(
    page_title="Estabilidade de Antocianinas – Repolho Roxo",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Reseta o estado de formulários a cada nova execução.
if "form_step" not in st.session_state:
    st.session_state.form_step = "home"
if "last_saved" not in st.session_state:
    st.session_state.last_saved = None


def read_raw(path: Path, default_columns: list[str]) -> pd.DataFrame:
    """Carrega um CSV real; em caso de erro ou vazio, retorna DataFrame vazio com cabeçalho."""
    try:
        return persist.load_csv(path, default_columns)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Não foi possível carregar {path.name}: {exc}")
        return pd.DataFrame(columns=default_columns)


def empty_with_header(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def counts(frame: pd.DataFrame, group_col: str) -> tuple[int, int]:
    """Retorna (nós lotes, nº de amostras/retinhas)."""
    return frame[group_col].nunique() if group_col in frame.columns else 0, len(frame)

# Colunas por tipo de registro (contratos fixos).
STABILITY_COLUMNS = list(persist.STABILITY_COLUMNS)
COLOR_COLUMNS = list(persist.COLOR_COLUMNS)
MICRO_COLUMNS = list(persist.MICRO_COLUMNS)
STABILITY_KEY = list(persist.STABILITY_KEY)
COLOR_KEY = list(persist.COLOR_KEY)
MICRO_KEY = list(persist.MICRO_KEY)
VAL_FUNCTION = {
    "stability": persist.validate_stab_descriptions,
    "color": persist.validate_color_descriptions,
    "micro": persist.validate_micro_descriptions,
}
CSV_PATH = {
    "stability": STABILITY_CSV,
    "color": COLOR_CSV,
    "micro": MICRO_CSV,
}


def render_home(stability: pd.DataFrame, color: pd.DataFrame) -> None:
    """Painel inicial: contadores, filtros e gráficos de retenção/pH/cor."""
    st.header("Painel inicial")
    st.caption("Dados reais dos laboratórios. Gráficos aparecem somente com medições.")

    n_lotes = stability["batch_id"].nunique() if "batch_id" in stability.columns else 0
    n_amostras = stability["vial_id"].nunique() if "vial_id" in stability.columns else 0
    n_medições = len(stability)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Lotes", n_lotes)
    col_b.metric("Amostras (viales)", n_amostras)
    col_c.metric("Medições", n_medições)
    st.divider()

    st.write("**Filtros**")
    f_lote = st.selectbox("Lote", ["todos"] + stability["batch_id"].astype(str).unique().tolist(), key="home_lote")
    f_formula = st.selectbox("Formulação", ["todos"] + stability["formulation"].astype(str).unique().tolist(), key="home_formula")
    f_cond = st.selectbox("Condição de armazenamento", ["todos"] + stability["storage_condition"].astype(str).unique().tolist(), key="home_cond")
    f_day = st.selectbox("Dia", ["todos"] + sorted(stability["day"].dropna().unique().tolist()), key="home_day")

    filtered = stability.copy()
    if f_lote != "todos":
        filtered = filtered[filtered["batch_id"].astype(str) == f_lote]
    if f_formula != "todos":
        filtered = filtered[filtered["formulation"].astype(str) == f_formula]
    if f_cond != "todos":
        filtered = filtered[filtered["storage_condition"].astype(str) == f_cond]
    if f_day != "todos":
        filtered = filtered[filtered["day"] == int(f_day)]

    if filtered.empty:
        st.info("Nenhum registro coincide com os filtros ou ainda não há medições.")
    else:
        stab = lab.calculate_tac(filtered).dropna(subset=["day", "retention_pct"])
        if not stab.empty:
            st.line_chart(stab.set_index("day")["retention_pct"], use_container_width=True)
        ph = stab.groupby("day")["pH_storage"].mean().reset_index()
        if not ph.empty:
            st.line_chart(ph.set_index("day")["pH_storage"], use_container_width=True)
            st.caption("pH de armazenamento (média por dia)")

    st.subheader("Evolução da cor e retenção")
    if color.empty:
        st.info("Sem medições de cor para exibir.")
    else:
        color = lab.add_hsv_and_delta_e(color)
        hue = color.dropna(subset=["hue_deg", "day"])
        if not hue.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.line_chart(
                    hue.groupby("day")["hue_deg"].mean().reset_index().set_index("day")["hue_deg"],
                    use_container_width=True,
                )
            with c2:
                st.line_chart(
                    hue.groupby("day")["delta_e_cie76_vs_day0"].mean().reset_index().set_index("day")["delta_e_cie76_vs_day0"],
                    use_container_width=True,
                )


def _row_stab() -> dict:
    return {
        "batch_id": st.text_input("batch_id"),
        "formulation": st.text_input("formulação", placeholder="ex.: native / pH3"),
        "storage_condition": st.text_input("storage_condition", placeholder="ex.: 4C_dark / 25C_dark"),
        "day": st.text_input("day"),
        "vial_id": st.text_input("vial_id"),
        "replicate": st.text_input("replicate"),
        "pH_storage": st.text_input("pH_storage"),
        "a520_ph1": st.text_input("a520_ph1"),
        "a700_ph1": st.text_input("a700_ph1"),
        "a520_ph45": st.text_input("a520_ph45"),
        "a700_ph45": st.text_input("a700_ph45"),
        "dilution_factor": st.text_input("dilution_factor"),
        "path_length_cm": st.text_input("path_length_cm"),
        "notes": st.text_area("notes", height=60, placeholder="Opcional"),
    }


def render_stability_form() -> None:
    st.header("Cadastro de medições de estabilidade")
    st.caption("Grava em ``data/raw/stability_measurements.csv`` mantendo os cabeçalhos originais.")

    last = st.session_state.get("stable_last")
    if last:
        if last["status"] == "success":
            st.success(last["message"])
            st.caption("Arquivo atualizado. Próximo registro:")
            if st.button("Cadastrar outra medição", key="stable_new_btn"):
                st.session_state["stable_last"] = None
                st.session_state["stable_form"] = "stability"
        else:
            st.error(last["message"])
            st.session_state["stable_last"] = None

    with st.form("stab_form", clear_on_submit=True):
        row = _row_stab()
        submitted = st.form_submit_button("Salvar medição")
    if not submitted:
        return

    df = pd.DataFrame([row])
    result = persist.append_row_safely(STABILITY_CSV, df, STABILITY_KEY, VAL_FUNCTION["stability"])
    st.session_state["stable_last"] = result
    st.rerun()


@st.cache_data
def read_stability() -> pd.DataFrame:
    return read_raw(STABILITY_CSV, STABILITY_COLUMNS)


def _row_color() -> dict:
    return {
        "batch_id": st.text_input("batch_id"),
        "formulation": st.text_input("formulação", placeholder="ex.: native / pH3"),
        "storage_condition": st.text_input("storage_condition", placeholder="ex.: 4C_dark / 25C_dark"),
        "day": st.text_input("day"),
        "vial_id": st.text_input("vial_id"),
        "replicate": st.text_input("replicate"),
        "target_pH": st.text_input("target_pH"),
        "measured_pH_final": st.text_input("measured_pH_final"),
        "r": st.text_input("r", placeholder="0-255"),
        "g": st.text_input("g", placeholder="0-255"),
        "b": st.text_input("b", placeholder="0-255"),
        "L_star": st.text_input("L_star", placeholder="opcional"),
        "a_star": st.text_input("a_star", placeholder="opcional"),
        "b_star": st.text_input("b_star", placeholder="opcional"),
        "absorbance_max_nm": st.text_input("absorbance_max_nm", placeholder="opcional"),
        "absorbance_max": st.text_input("absorbance_max", placeholder="opcional"),
        "notes": st.text_area("notes", height=60, placeholder="Opcional"),
    }


def render_color_form() -> None:
    st.header("Cadastro de cor")
    st.caption("Grava em ``data/raw/color_measurements.csv``. CIELAB e absorbância máxima são opcionais e não são preenchidos automaticamente.")
    st.warning("RGB fora de faixa são rejeitados; L*, a*, b* não são derivados de RGB nesta interface.")

    last = st.session_state.get("color_last")
    if last:
        if last["status"] == "success":
            st.success(last["message"])
            st.caption("Arquivo atualizado. Próximo registro:")
            if st.button("Cadastrar outra medição", key="color_new_btn"):
                st.session_state["color_last"] = None
                st.session_state["color_form"] = "color"
        else:
            st.error(last["message"])
            st.session_state["color_last"] = None

    with st.form("color_form", clear_on_submit=True):
        row = _row_color()
        submitted = st.form_submit_button("Salvar medição")
    if not submitted:
        return

    df = pd.DataFrame([row])
    result = persist.append_row_safely(COLOR_CSV, df, COLOR_KEY, VAL_FUNCTION["color"])
    st.session_state["color_last"] = result
    st.rerun()


@st.cache_data
def read_color() -> pd.DataFrame:
    return read_raw(COLOR_CSV, COLOR_COLUMNS)


def _filtered_selection(df: pd.DataFrame) -> pd.DataFrame:
    """Filtro simples por colunas textuais/numéricas; usado nas tabelas de consulta."""
    if df is None or df.empty:
        return df
    tmp = df.copy()
    for col in ("batch_id", "formulation", "storage_condition"):
        if col in tmp.columns:
            opts = ["todos"] + sorted(tmp[col].dropna().astype(str).unique().tolist())
            choice = st.selectbox(f"Filtrar por {col}", opts, key=f"q_{col}")
            if choice != "todos":
                tmp = tmp[tmp[col].astype(str) == choice]
    if "day" in tmp.columns:
        days = sorted(tmp["day"].dropna().unique().tolist())
        choice = st.selectbox("Filtrar por dia", ["todos"] + [int(d) for d in days], key="q_day")
        if choice != "todos":
            tmp = tmp[tmp["day"] == float(choice)]
    return tmp


def render_query_management() -> None:
    st.header("Consulta e gestão dos registros")
    st.caption("Dados reais dos laboratórios. A gravação é protegida contra duplicidade e com backup; "
               "nenhum arquivo é sobrescrito silenciosamente.")

    tab_s, tab_c, tab_m = st.tabs(["Estabilidade", "Cor", "Microbiologia"])

    with tab_s:
        st.subheader("Medições de estabilidade")
        data = read_stability()
        if data.empty:
            st.info("Nenhuma medição de estabilidade gravada ainda.")
        else:
            filtered = _filtered_selection(data)
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Estabilidade)", csv_bytes,
                               "estabilidade_selecionados.csv", mime="text/csv")

    with tab_c:
        st.subheader("Medições de cor")
        data = read_color()
        if data.empty:
            st.info("Nenhuma medição de cor gravada ainda.")
        else:
            filtered = _filtered_selection(data)
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Cor)", csv_bytes, "cor_selecionados.csv", mime="text/csv")

    with tab_m:
        st.subheader("Medições de microbiologia")
        data = read_micro()
        if data.empty:
            st.info("Nenhuma medição microbiológica gravada ainda.")
        else:
            filtered = _filtered_selection(data)
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Microbiologia)", csv_bytes,
                               "microbiologia_selecionados.csv", mime="text/csv")

    st.divider()
    st.subheader("Regras de guarda")
    st.write("- Nada é sobrescrito automaticamente; gravações duplicadas são rejeitadas e não alteram o arquivo.")
    st.write("- Um backup timestampado de cada CSV é mantido antes de adicionar registros.")
    st.write("- Duplicidade avaliada por: lote, formulação, condição, dia, recipiente (vial_id) e réplica.")


def _row_micro() -> dict:
    return {
        "batch_id": st.text_input("batch_id"),
        "formulation": st.text_input("formulação", placeholder="ex.: native / pH3"),
        "storage_condition": st.text_input("storage_condition", placeholder="ex.: 4C_dark"),
        "day": st.text_input("day"),
        "vial_id": st.text_input("vial_id"),
        "test_type": st.text_input("test_type", placeholder="ex.: PCR, count, enumeration"),
        "result_value": st.text_input("result_value"),
        "result_unit": st.text_input("result_unit", placeholder="ex.: CFU/g, log CFU/mL"),
        "method": st.text_input("method", placeholder="Opcional"),
        "notes": st.text_area("notes", height=60, placeholder="Observação — não inferir segurança microbiológica da química."),
    }


def render_micro_form() -> None:
    st.header("Cadastro de microbiologia")
    st.caption("Grava em ``data/raw/microbiology_measurements.csv`` usando exatamente os campos do CSV.")
    st.warning("Estabilidade química/colorimétrica NÃO é prova de segurança microbiológica. Campos não realizados deixem em branco.")

    last = st.session_state.get("micro_last")
    if last:
        if last["status"] == "success":
            st.success(last["message"])
            st.caption("Arquivo atualizado. Próximo registro:")
            if st.button("Cadastrar outra medição", key="micro_new_btn"):
                st.session_state["micro_last"] = None
                st.session_state["micro_form"] = "micro"
        else:
            st.error(last["message"])
            st.session_state["micro_last"] = None

    with st.form("micro_form", clear_on_submit=True):
        row = _row_micro()
        submitted = st.form_submit_button("Salvar medição")
    if not submitted:
        return

    df = pd.DataFrame([row])
    result = persist.append_row_safely(MICRO_CSV, df, MICRO_KEY, VAL_FUNCTION["micro"])
    st.session_state["micro_last"] = result
    st.rerun()


@st.cache_data
def read_micro() -> pd.DataFrame:
    return read_raw(MICRO_CSV, MICRO_COLUMNS)

def render_simulator() -> None:
    st.header("Simulador")
    st.caption("Integra o simulador existente (``anthocyanin_lab.simulate_scenarios``). "
               "Apenas os parâmetros efetivamente usados pelo modelo são expostos.")

    if not CONFIG_PATH.exists():
        st.info("Arquivo de configuração não encontrado. Execute ``python anthocyanin_lab.py init --dir .``.")
        return

    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Configuração inválida: {exc}")
        return

    st.warning("Qualquer saída aqui é simulada. Não substitua evidência experimental nem previsão validada.")

    # Parâmetros de referência/calibrated do modelo.
    st.subheader("Parâmetros de referência do modelo")
    ref_temp = st.number_input("reference_temperature_c (ºC)", value=float(cfg.get("reference_temperature_c", 25.0)), format="%.2f")
    ref_hl = st.number_input("reference_half_life_days", value=(float(cfg.get("reference_half_life_days", 0)) if cfg.get("reference_half_life_days") is not None else 0.0), format="%.2f")
    ea = st.number_input("activation_energy_kj_mol", value=(float(cfg.get("activation_energy_kj_mol", 0)) if cfg.get("activation_energy_kj_mol") is not None else 0.0), format="%.2f")
    init_pct = st.number_input("initial_retention_pct", value=float(cfg.get("initial_retention_pct", 100.0)), format="%.2f")
    days = st.text_input("days (separados por vírgula)", value=",".join(str(d) for d in cfg.get("days", [0, 3, 7, 10, 14, 28])))

    # Cenários: temperatura + fatores multiplicativos do modelo.
    st.subheader("Cenários (temperatura e multiplicadores do modelo)")
    scenarios = cfg.get("scenarios", [])
    scenario_keys = [str(s.get("scenario_id", i)) for i, s in enumerate(scenarios)]
    edited_scenarios = []
    for i, s in enumerate(scenarios):
        sid = st.text_input(f"scenario_id[{i}]", value=s.get("scenario_id", scenario_keys[i]))
        label = st.text_input(f"label[{i}]", value=s.get("label", s.get("label", "")))
        temp = st.number_input(f"temperature_c[{i}]", value=float(s.get("temperature_c", 4.0)), format="%.2f")
        ph_f = st.number_input(f"pH_factor[{i}]", value=float(s.get("pH_factor", 1.0)), format="%.2f")
        light_f = st.number_input(f"light_factor[{i}]", value=float(s.get("light_factor", 1.0)), format="%.2f")
        oxygen_f = st.number_input(f"oxygen_factor[{i}]", value=float(s.get("oxygen_factor", 1.0)), format="%.2f")
        pkg_f = st.number_input(f"packaging_factor[{i}]", value=float(s.get("packaging_factor", 1.0)), format="%.2f")
        edited_scenarios.append({
            "scenario_id": sid, "label": label, "temperature_c": temp,
            "pH_factor": ph_f, "light_factor": light_f, "oxygen_factor": oxygen_f, "packaging_factor": pkg_f,
            "notes": s.get("notes", ""),
        })

    if st.button("Executar simulação"):
        if ref_hl <= 0 or ea <= 0:
            st.error("reference_half_life_days e activation_energy_kj_mol devem ser informados para a simulação.")
            return
        try:
            days_list = [float(d) for d in days.split(",") if d.strip() != ""]
        except ValueError:
            st.error("Formato de dias inválido.")
            return
        if not days_list:
            st.error("Informe ao menos um dia.")
            return

        scenario_cfg = {
            "model": "first_order_arrhenius_scenario",
            "purpose": "Exploração de hipóteses; não é previsão validada nem dado experimental.",
            "reference_temperature_c": float(ref_temp),
            "reference_half_life_days": float(ref_hl),
            "activation_energy_kj_mol": float(ea),
            "initial_retention_pct": float(init_pct),
            "days": days_list,
            "scenarios": edited_scenarios,
        }
        try:
            results = lab.simulate_scenarios(scenario_cfg)
        except ValueError as exc:
            st.error(f"Simulação recusada: {exc}")
            return

        st.success("Simulação concluída.")
        st.caption("✅ Tudo abaixo é SIMULADO — não é medição, previsão validada nem recomendação de prazo de validade.")
        st.dataframe(results, use_container_width=True, height=360)
        st.caption("data_origin de todas as linhas é SIMULATION_ONLY; o modelo é hipotético até calibração.")


# Contratos de literatura importados do módulo científico.
LITERATURE_STUDY_COLUMNS = list(lab.LITERATURE_STUDY_COLUMNS)
LITERATURE_MEASUREMENT_COLUMNS = list(lab.LITERATURE_COLUMNS)
LITERATURE_EVIDENCE_COLUMNS = list(lab.LITERATURE_EVIDENCE_COLUMNS)
LITERATURE_DIR = ROOT / "data" / "literature"

STUDY_CSV = LITERATURE_DIR / "literature_studies.csv"
MEASUREMENT_CSV = LITERATURE_DIR / "literature_measurements.csv"
EVIDENCE_CSV = LITERATURE_DIR / "literature_evidence.csv"


def read_literature_studies() -> pd.DataFrame:
    return read_raw(STUDY_CSV, LITERATURE_STUDY_COLUMNS)


def read_literature_measurements() -> pd.DataFrame:
    return read_raw(MEASUREMENT_CSV, LITERATURE_MEASUREMENT_COLUMNS)


def read_literature_evidence() -> pd.DataFrame:
    return read_raw(EVIDENCE_CSV, LITERATURE_EVIDENCE_COLUMNS)


def render_literature() -> None:
    st.header("Literatura científica")
    st.caption("Estudos em ``data/literature/``. Valores publicados, calculados e evidências qualitativas são exibidos "
               "separadamente dos dados do laboratório.")

    tab_st, tab_me, tab_ev = st.tabs(["Estudos", "Medições", "Evidências"])
    with tab_st:
        st.subheader("Estudios de literatura")
        data = read_literature_studies()
        cols = ["study_id", "citation", "doi", "url", "species", "matrix", "solvent", "analysis_unit", "limitations"]
        if not data.empty:
            st.dataframe(data[cols], use_container_width=True, height=360)
        else:
            st.info("Nenhum estudo de literatura carregado.")

    with tab_me:
        st.subheader("Medições e séries publicadas")
        data = read_literature_measurements()
        if not data.empty:
            origin = data["data_origin"].fillna("").astype(str)
            reported = data["reported_or_calculated"].fillna("").astype(str)
            st.caption("Legenda: PUBLISHED_ARTICLE = valor publicado; reported_or_calculated=reported = informado. "
                       "Calculated = derivado (nunca usado como evidência crua).")
            pub = data[origin == "PUBLISHED_ARTICLE"]
            if not pub.empty:
                pub_cols = ["study_id", "treatment_id", "time_value", "time_unit", "measurement",
                            "value", "value_unit", "standard_deviation", "replicate_count", "source_location",
                            "package_material", "data_origin", "reported_or_calculated"]
                st.dataframe(pub[pub_cols], use_container_width=True, height=360)
            else:
                st.info("Nenhuma medição publicada (PUBLISHED_ARTICLE) encontrada.")
        else:
            st.info("Nenhuma medição de literatura gravada ainda.")

    with tab_ev:
        st.subheader("Evidências e resumo cinético")
        data = read_literature_evidence()
        cols = ["study_id", "evidence_type", "evidence_category", "evidence_text", "origin_source",
                "source_url", "source_location", "conditions", "temperature_c", "pH", "half_life", "k_value", "notes"]
        if not data.empty:
            st.dataframe(data[cols], use_container_width=True, height=360)
        else:
            st.info("Nenhuma evidência de literatura carregada.")

    st.divider()
    st.subheader("Adequação de pontos de gráfico")
    st.warning("Você deve manter a origem (DOI/URL, study_id, data_origin) de cada linha; pontos calculados (retention derivado)"
               " são rótulos, não novas medições. Não misture estudos de literatura com medições do laboratório.")



@st.cache_data
def read_ml_observations() -> pd.DataFrame:
    return read_raw(ML_CSV, lab.ml_template_columns())


def render_ml() -> None:
    st.header("Aprendizado de máquina")
    st.caption("Módulo exploratório do ``anthocyanin_lab.train_ml_model``. "
               "Por padrão usa somente ``data_origin=EXPERIMENTAL``; literatura exige mapeamento manual.")

    data = read_ml_observations()
    origins = data["data_origin"].fillna("").astype(str).str.upper() if not data.empty else pd.Series(dtype=str)
    n_rows = len(data)
    n_experimental = int((origins == "EXPERIMENTAL").sum()) if not data.empty else 0
    n_literature = int((origins == "LITERATURE").sum()) if not data.empty else 0
    n_simulation = int((origins == "SIMULATION_ONLY").sum()) if not data.empty else 0

    st.subheader("Disponibilidade de dados")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Observações", n_rows)
    col_b.metric("EXPERIMENTAL", n_experimental)
    col_b.metric("LITERATURE", n_literature)
    col_c.metric("SIMULATION_ONLY", n_simulation)
    st.caption("A ausência de dados experimentais impede o treinamento; a literatura e a simulação não substituem "
               "nem são carregadas automaticamente para o treino.")

    if n_rows == 0:
        st.error("ml_observations.csv está vazio. Insira observações experimentais (data_origin=EXPERIMENTAL) antes de treinar.")
        st.info("Nenhum modelo será treinado automaticamente.")
        return

    st.subheader("Configuração do modelo")
    target = st.selectbox("Variável-alvo", lab.ML_ALLOWED_TARGETS)
    include_literature = st.checkbox("Incluir literatura (mapeamento manual)", value=False)
    if include_literature:
        st.info("Opcional: exige >=5 estudos com study_id mapeado e acende alerta de domínio. Ignorado se <5.")

    if st.button("Treinar modelo exploratório"):
        if include_literature and n_literature < 5:
            st.error("Inclusão de literatura requer pelo menos 5 estudos com study_id mapeado.")
            return
        try:
            lab.train_ml_model(ROOT, target=target, include_literature=include_literature)
        except ValueError as exc:
            st.error(f"Treino recusado: {exc}")
            return

        st.success("Modelo exploratório gerado (somente dados EXPERIMENTAL, a menos que você escolha incluir literatura).")
        st.caption("Arquivos gerados: ml/cross_validated_predictions.csv · ml_metrics.json · ml_metrics.csv · ml_report.html · model_<target>.joblib")

        metrics_path = ROOT / "data" / "ml" / "ml_metrics.json"
        if metrics_path.exists():
            try:
                report = json.loads(metrics_path.read_text(encoding="utf-8"))
                st.markdown("#### Métricas de validação agrupada")
                st.json(report)
            except Exception:  # noqa: BLE001
                st.info("Métricas de validação não disponíveis.")

        st.caption("AVISO: métricas são exploração agrupada; não comprovam generalização. Valide com novos lotes "
                   "independentes antes de qualquer conclusão científica.")


def main() -> None:
    st.title("🧪 Estabilidade de Antocianinas – Repolho Roxo")
    st.sidebar.title("Navegação")
    pages = [
        "Painel inicial",
        "Cadastro de estabilidade",
        "Cadastro de cor",
        "Cadastro de microbiologia",
        "Consulta e gestão",
        "Literatura",
        "Simulador",
        "Aprendizado de máquina",
    ]
    page = st.sidebar.selectbox("Seção", pages)
    st.sidebar.caption("Aplicação local. Nenhum dado é enviado à rede.")

    stability = read_stability()
    color = read_color()

    if page == "Painel inicial":
        render_home(stability, color)
    elif page == "Cadastro de estabilidade":
        render_stability_form()
    elif page == "Cadastro de cor":
        render_color_form()
    elif page == "Cadastro de microbiologia":
        render_micro_form()
    elif page == "Consulta e gestão":
        render_query_management()
    elif page == "Literatura":
        render_literature()
    elif page == "Simulador":
        render_simulator()
    elif page == "Aprendizado de máquina":
        render_ml()


if __name__ == "__main__":
    main()

