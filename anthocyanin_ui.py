"""Interface Streamlit para o projeto de estabilidade de antocianinas.

Módulo de interface: consome os dados dos CSVs, expõe formulários de
registro, painel de análise, consulta, literatura, simulador e aprendizado
de máquina. As regras de validação, persistência, prevenção de duplicidade e
backup ficam em ``anthocyanin_persistence``; os cálculos científicos em
``anthocyanin_lab`` (reutilizados sempre que possível).
"""

from __future__ import annotations

# GUI_GUIDANCE_PATCH_V1

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
from ui_theme import apply_theme

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
    """Dashboard experimental; apresenta apenas medições existentes, sem dados demonstrativos."""
    n_batches = stability["batch_id"].nunique() if "batch_id" in stability.columns else 0
    n_vials = stability["vial_id"].nunique() if "vial_id" in stability.columns else 0
    n_stability = len(stability)
    n_color = len(color)

    st.markdown(
        """<section class="lab-hero">
          <div class="lab-hero-kicker">Painel de pesquisa · Repolho roxo</div>
          <h2>Estabilidade do extrato, acompanhada com rigor.</h2>
          <p>Organize medições de estabilidade, pH e resposta colorimétrica ao longo do armazenamento. O painel só apresenta resultados quando existem registros no banco local.</p>
          <div class="lab-hero-foot">
            <span class="lab-hero-chip">Dados locais</span>
            <span class="lab-hero-chip">Origem experimental preservada</span>
            <span class="lab-hero-chip">Sem envio de dados à rede</span>
          </div>
        </section>""",
        unsafe_allow_html=True,
    )

    st.subheader("Visão geral do experimento")
    st.markdown('<p class="lab-section-caption">Resumo calculado a partir dos CSVs locais — não inclui simulações nem valores de literatura.</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lotes registrados", f"{n_batches:,}".replace(",", "."))
    c2.metric("Recipientes", f"{n_vials:,}".replace(",", "."))
    c3.metric("Medições de estabilidade", f"{n_stability:,}".replace(",", "."))
    c4.metric("Registros de cor", f"{n_color:,}".replace(",", "."))

    if n_stability == 0 and n_color == 0:
        st.markdown(
            """<div class="lab-empty-card"><strong>A coleta ainda não começou</strong>
            Os modelos de CSV estão prontos, mas não há medições experimentais registradas. Cadastre os resultados reais do laboratório para ativar as curvas. Não são inseridos valores fictícios automaticamente.</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.success("A base contém registros locais. A disponibilidade de cada análise depende dos campos preenchidos.")

    st.subheader("Explorar resultados")
    with st.expander("Filtros de análise", expanded=False):
        f1, f2, f3, f4 = st.columns(4)
        batches = ["Todos"] + (sorted(stability["batch_id"].dropna().astype(str).unique().tolist()) if "batch_id" in stability.columns else [])
        formulations = ["Todas"] + (sorted(stability["formulation"].dropna().astype(str).unique().tolist()) if "formulation" in stability.columns else [])
        conditions = ["Todas"] + (sorted(stability["storage_condition"].dropna().astype(str).unique().tolist()) if "storage_condition" in stability.columns else [])
        days = sorted(stability["day"].dropna().unique().tolist()) if "day" in stability.columns else []
        day_options = ["Todos"] + [int(d) if float(d).is_integer() else d for d in days]
        f_batch = f1.selectbox("Lote (batch_id)", batches, key="home_lote")
        f_formula = f2.selectbox("Formulação (formulation)", formulations, key="home_formula")
        f_cond = f3.selectbox("Condição de armazenamento", conditions, key="home_cond")
        f_day = f4.selectbox("Dia (dias)", day_options, key="home_day")

    filtered = stability.copy()
    if f_batch != "Todos" and "batch_id" in filtered.columns:
        filtered = filtered[filtered["batch_id"].astype(str) == f_batch]
    if f_formula != "Todas" and "formulation" in filtered.columns:
        filtered = filtered[filtered["formulation"].astype(str) == f_formula]
    if f_cond != "Todas" and "storage_condition" in filtered.columns:
        filtered = filtered[filtered["storage_condition"].astype(str) == f_cond]
    if f_day != "Todos" and "day" in filtered.columns:
        filtered = filtered[filtered["day"] == float(f_day)]

    tab_ret, tab_ph, tab_color = st.tabs(["Retenção de antocianinas", "pH de armazenamento", "Cor e diferença visual"])
    with tab_ret:
        if filtered.empty:
            st.info("Não há medições de estabilidade que correspondam aos filtros selecionados.")
        else:
            try:
                derived = lab.calculate_tac(filtered)
                derived = derived.dropna(subset=["day", "retention_pct"])
                if derived.empty:
                    st.info("Ainda não há pontos suficientes para calcular retenção com os campos atuais.")
                else:
                    if "storage_condition" in derived.columns:
                        chart = derived.groupby(["day", "storage_condition"], dropna=False)["retention_pct"].mean().unstack("storage_condition")
                    else:
                        chart = derived.groupby("day")["retention_pct"].mean().to_frame("retention_pct")
                    st.line_chart(chart, use_container_width=True)
                    st.caption("Retenção derivada pelo módulo científico a partir das absorbâncias disponíveis. Confira os avisos de qualidade e a definição do tempo basal antes de interpretar.")
            except (KeyError, ValueError) as exc:
                st.warning(f"A análise de retenção não pôde ser calculada com esses registros: {exc}")
    with tab_ph:
        if filtered.empty or "pH_storage" not in filtered.columns:
            st.info("Nenhuma medição de pH disponível para os filtros atuais.")
        else:
            ph = filtered.dropna(subset=["day", "pH_storage"])
            if ph.empty:
                st.info("O pH ainda não foi preenchido nos registros selecionados.")
            else:
                if "storage_condition" in ph.columns:
                    chart = ph.groupby(["day", "storage_condition"], dropna=False)["pH_storage"].mean().unstack("storage_condition")
                else:
                    chart = ph.groupby("day")["pH_storage"].mean().to_frame("pH_storage")
                st.line_chart(chart, use_container_width=True)
                st.caption("Valores médios por tempo e condição, sem substituir réplicas, dispersão ou análise estatística.")
    with tab_color:
        if color.empty:
            st.info("Ainda não há registros de cor. Eles podem ser cadastrados na seção ‘Cadastro de cor’.")
        else:
            try:
                color_view = lab.add_hsv_and_delta_e(color)
                hue = color_view.dropna(subset=["day", "hue_deg"]) if {"day", "hue_deg"}.issubset(color_view.columns) else pd.DataFrame()
                delta = color_view.dropna(subset=["day", "delta_e_cie76_vs_day0"]) if {"day", "delta_e_cie76_vs_day0"}.issubset(color_view.columns) else pd.DataFrame()
                left, right = st.columns(2)
                with left:
                    st.markdown("**Ângulo de matiz (HSV)**")
                    if hue.empty:
                        st.info("Matiz indisponível nos registros atuais.")
                    else:
                        st.line_chart(hue.groupby("day")["hue_deg"].mean(), use_container_width=True)
                with right:
                    st.markdown("**ΔE CIE76 vs. dia 0**")
                    if delta.empty:
                        st.info("ΔE requer valores CIELAB fornecidos por um método de medição adequado; não é inferido a partir do RGB.")
                    else:
                        st.line_chart(delta.groupby("day")["delta_e_cie76_vs_day0"].mean(), use_container_width=True)
                st.caption("HSV é derivado dos canais RGB. ΔE CIE76 só é apresentado quando L*, a* e b* estiverem disponíveis; diferenças visuais não comprovam estabilidade química nem segurança microbiológica.")
            except (KeyError, ValueError) as exc:
                st.warning(f"A análise de cor não pôde ser apresentada: {exc}")

    st.divider()
    st.caption("Importante: resultados calculados, simulados e bibliográficos devem continuar identificados pela sua origem. Estabilidade química/colorimétrica não equivale a segurança microbiológica nem estabelece, por si só, prazo de validade.")

def _row_stab() -> dict:
    """Campos do método diferencial de pH, com orientação no próprio formulário."""
    return {
        "batch_id": st.text_input("Lote independente (batch_id)", placeholder="ex.: B01", help="Identifique uma extração independente de repolho roxo. Use o mesmo código em todas as medições derivadas dessa extração; extrações feitas em dias/preparos distintos recebem códigos distintos."),
        "formulation": st.text_input("Formulação (formulation)", placeholder="ex.: F_NATIVE ou F_PH3", help="Descreva a formulação de modo padronizado. Ex.: F_NATIVE = extrato no pH natural; F_PH3 = alíquota ajustada para pH 3,0. Use o protocolo real adotado e não altere o significado do código durante o estudo."),
        "storage_condition": st.text_input("Condição de armazenamento", placeholder="ex.: BASELINE, C4_DARK, C25_DARK", help="Use BASELINE para a medição basal do dia 0 feita antes da distribuição; C4_DARK para 4 °C no escuro; C25_DARK para 25 °C no escuro. Registre desvios no campo de observações."),
        "day": st.text_input("Tempo de armazenamento (dias)", placeholder="ex.: 0, 3, 7, 10, 14 ou 28", help="Número de dias desde o início do armazenamento. Dia 0 é a referência basal da mesma combinação lote + formulação."),
        "vial_id": st.text_input("Código do frasco/amostra (vial_id)", placeholder="ex.: B01_PH3_D07_C4_R1", help="Código único da unidade física analisada. O protocolo recomenda abrir cada frasco uma única vez; não conte leituras repetidas do mesmo frasco como lotes independentes."),
        "replicate": st.text_input("Número da réplica técnica", placeholder="ex.: 1", help="Número inteiro positivo que identifica uma réplica dentro do mesmo lote/condição/tempo. Réplicas técnicas ajudam a estimar variação de medição, mas não substituem extrações independentes."),
        "pH_storage": st.text_input("pH do extrato no armazenamento", placeholder="ex.: 3.02", help="pH realmente medido no extrato no momento da coleta/análise, obtido com pHmetro calibrado. Não substitua pela meta de pH sem medir."),
        "a520_ph1": st.text_input("Absorbância a 520 nm — tampão pH 1,0", help="Leitura UV-Vis da alíquota diluída em tampão pH 1,0, a 520 nm. Valor adimensional do equipamento; use o branco/SOP do laboratório."),
        "a700_ph1": st.text_input("Absorbância a 700 nm — tampão pH 1,0", help="Leitura UV-Vis da mesma preparação em tampão pH 1,0, a 700 nm, usada como correção de turbidez no método diferencial de pH."),
        "a520_ph45": st.text_input("Absorbância a 520 nm — tampão pH 4,5", help="Leitura UV-Vis da alíquota preparada em tampão pH 4,5, a 520 nm, seguindo o mesmo SOP adotado para todas as amostras."),
        "a700_ph45": st.text_input("Absorbância a 700 nm — tampão pH 4,5", help="Leitura UV-Vis da mesma preparação em tampão pH 4,5, a 700 nm, usada como correção de turbidez."),
        "dilution_factor": st.text_input("Fator de diluição (DF)", placeholder="ex.: 10", help="Fator total aplicado antes da leitura, definido pelo protocolo de preparo. Ex.: uma diluição 1:10 corresponde a DF=10 se essa for a convenção do SOP. Não estime: calcule a partir dos volumes utilizados."),
        "path_length_cm": st.text_input("Caminho óptico da cubeta (cm)", placeholder="ex.: 1.0", help="Comprimento do caminho óptico em centímetros, conforme a cubeta e o equipamento. Use 1,0 somente se a cubeta tiver caminho óptico de 1 cm."),
        "notes": st.text_area("Observações / desvios do protocolo", height=70, placeholder="ex.: precipitado observado; leitura repetida após conferir o branco", help="Registre condições reais relevantes, ocorrências, desvios, identificação do SOP e motivos para repetir/excluir uma leitura. Não coloque aqui valores estimados como se fossem medidos."),
    }

def render_stability_form() -> None:
    st.header("Cadastro de estabilidade")
    st.markdown("Registre as leituras reais do **método diferencial de pH** para acompanhar a concentração de antocianinas ao longo do armazenamento. Esta página não executa o ensaio: ela guarda os valores medidos no UV-Vis e os metadados da amostra.")
    st.info("Preencha com dados obtidos no laboratório e conforme o SOP. O dia 0 é a referência para retenção; use o mesmo lote e a mesma formulação. Para BASELINE compartilhado, cadastre o dia 0 com `storage_condition=BASELINE`. Campos ainda não medidos devem ficar vazios, nunca estimados.")
    st.caption("Arquivo de destino: data/raw/stability_measurements.csv. Os campos abaixo exibem dicas ao passar o cursor sobre o ícone de ajuda.")
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
        submitted = st.form_submit_button("Salvar medição", type="primary")
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
    """Campos de cor; conserva RGB original e só aceita CIELAB quando medido externamente."""
    return {
        "batch_id": st.text_input("Lote independente (batch_id)", placeholder="ex.: B01", help="Use o mesmo ID da extração correspondente na tabela de estabilidade."),
        "formulation": st.text_input("Formulação", placeholder="ex.: F_NATIVE ou F_PH3", help="Código consistente com o cadastro de estabilidade; descreva no protocolo a composição/acidificante de cada código."),
        "storage_condition": st.text_input("Condição de armazenamento", placeholder="ex.: BASELINE, C4_DARK ou C25_DARK", help="Use os mesmos códigos padronizados na tabela de estabilidade. BASELINE representa a medição inicial do dia 0."),
        "day": st.text_input("Tempo de armazenamento (dias)", placeholder="ex.: 0, 14 ou 28", help="Dias desde o início do armazenamento. A cor deve ser comparada com uma referência equivalente do dia 0."),
        "vial_id": st.text_input("Código do frasco/amostra", placeholder="ex.: B01_PH3_D14_C4_R1", help="Identifica a unidade física que foi fotografada/medida. Mantenha a ligação com o registro da amostra correspondente."),
        "replicate": st.text_input("Número da réplica técnica", placeholder="ex.: 1", help="Número inteiro positivo da repetição técnica; não o confunda com o número de lote independente."),
        "target_pH": st.text_input("pH-alvo da solução de desafio", placeholder="ex.: 3.0", help="pH nominal do tampão/solução usada para testar a resposta indicadora. Use vazio quando não se aplicou uma solução de pH conhecido."),
        "measured_pH_final": st.text_input("pH final após misturar com o extrato", placeholder="ex.: 3.14", help="pH medido depois da mistura do extrato indicador com a solução/tampão. É diferente do pH-alvo, pois o extrato pode alterar o pH final."),
        "r": st.text_input("Canal vermelho (R), 0–255", placeholder="ex.: 124", help="Canal vermelho extraído da imagem original, em RGB sRGB de 8 bits. Use iluminação, distância, fundo, recipiente e configurações da câmera padronizados."),
        "g": st.text_input("Canal verde (G), 0–255", placeholder="ex.: 82", help="Canal verde da mesma região de interesse e da mesma imagem que R e B. Não use valores de imagens com filtros ou edição não documentada."),
        "b": st.text_input("Canal azul (B), 0–255", placeholder="ex.: 166", help="Canal azul da mesma região de interesse. A interface deriva HSV de RGB; isso não é equivalente a uma medição CIELAB."),
        "L_star": st.text_input("CIELAB L* (opcional)", placeholder="somente se medido/validado", help="Claridade CIELAB de uma medição instrumental ou método validado. Não é o canal vermelho nem deve ser digitado como estimativa visual."),
        "a_star": st.text_input("CIELAB a* (opcional)", placeholder="somente se medido/validado", help="Coordenada verde–vermelho do espaço CIELAB fornecida por instrumento/método validado."),
        "b_star": st.text_input("CIELAB b* (opcional)", placeholder="somente se medido/validado", help="Coordenada azul–amarelo do espaço CIELAB fornecida por instrumento/método validado. Não é o canal B do RGB."),
        "absorbance_max_nm": st.text_input("Comprimento de onda do pico (nm, opcional)", placeholder="ex.: 530", help="Comprimento de onda em que foi observado o pico de absorbância no espectro UV-Vis. Preencha apenas se realizou a varredura."),
        "absorbance_max": st.text_input("Absorbância no pico (opcional)", placeholder="valor do UV-Vis", help="Absorbância medida no comprimento de onda informado acima; mantenha o branco, diluição e condições do SOP consistentes."),
        "notes": st.text_area("Observações / condições da imagem", height=70, placeholder="ex.: iluminação LED branca, exposição bloqueada", help="Registre iluminação, aparelho, aplicativo/método de extração RGB, recipiente e desvios. Guarde as imagens originais fora do CSV conforme o protocolo de dados."),
    }

def render_color_form() -> None:
    st.header("Cadastro da resposta de cor")
    st.markdown("Registre a cor do extrato e, quando aplicável, sua resposta após contato com uma solução de pH conhecido. O objetivo é avaliar se a função de indicador continua útil com o armazenamento.")
    st.info("R, G e B são obrigatórios e devem vir da imagem original em condições controladas (mesma iluminação, aparelho, recipiente e região de interesse). O sistema calcula HSV a partir de RGB. L*, a*, b* são opcionais e só devem ser preenchidos se obtidos por instrumento ou método CIELAB validado; a interface não converte RGB em CIELAB automaticamente.")
    st.caption("Arquivo de destino: data/raw/color_measurements.csv. Não preencha observações instrumentais que não foram medidas.")
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
        submitted = st.form_submit_button("Salvar medição", type="primary")
    if not submitted:
        return
    df = pd.DataFrame([row])
    result = persist.append_row_safely(COLOR_CSV, df, COLOR_KEY, VAL_FUNCTION["color"])
    st.session_state["color_last"] = result
    st.rerun()

@st.cache_data
def read_color() -> pd.DataFrame:
    return read_raw(COLOR_CSV, COLOR_COLUMNS)


def _filtered_selection(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    """Filtro simples por colunas textuais/numéricas; usado nas tabelas de consulta.

    ``key_prefix`` mantém as chaves dos widgets únicos quando os filtros das
    abas Estabilidade e Cor coexistem na mesma execução da página de consulta.
    """
    if df is None or df.empty:
        return df
    labels = {
        "batch_id": "lote (batch_id)",
        "formulation": "formulação",
        "storage_condition": "condição de armazenamento",
    }
    tmp = df.copy()
    for col in ("batch_id", "formulation", "storage_condition"):
        if col in tmp.columns:
            opts = ["todos"] + sorted(tmp[col].dropna().astype(str).unique().tolist())
            choice = st.selectbox(f"Filtrar por {labels.get(col, col)}", opts, key=f"q_{key_prefix}_{col}")
            if choice != "todos":
                tmp = tmp[tmp[col].astype(str) == choice]
    if "day" in tmp.columns:
        days = sorted(tmp["day"].dropna().unique().tolist())
        choice = st.selectbox("Filtrar por dia", ["todos"] + [int(d) for d in days], key=f"q_{key_prefix}_day")
        if choice != "todos":
            tmp = tmp[tmp["day"] == float(choice)]
    return tmp


def render_query_management() -> None:
    st.header("Consultar e exportar registros")
    st.markdown("Aqui você **visualiza e exporta** registros já salvos; esta página não cadastra nem corrige medições. Para inserir dados novos, use as páginas de cadastro de estabilidade ou cor. Os filtros e arquivos exportados não modificam os CSVs de origem.")

    tab_s, tab_c = st.tabs(["Estabilidade", "Cor"])
    with tab_s:
        st.subheader("Medições de estabilidade")
        st.caption("Cada linha é uma observação de armazenamento usada no método diferencial de pH. Confira batch_id, formulação, condição, dia e unidade física antes de comparar valores.")
        data = read_stability()
        if data.empty:
            st.info("Nenhuma medição de estabilidade gravada ainda.")
        else:
            filtered = _filtered_selection(data, "stab")
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Estabilidade)", csv_bytes, "estabilidade_selecionados.csv", mime="text/csv")

    with tab_c:
        st.subheader("Medições de cor")
        st.caption("RGB deve vir de imagem/medição feita em condições padronizadas. HSV é derivado do RGB; CIELAB/ΔE só são usados quando os campos CIELAB foram obtidos por método válido.")
        data = read_color()
        if data.empty:
            st.info("Nenhuma medição de cor gravada ainda.")
        else:
            filtered = _filtered_selection(data, "color")
            st.dataframe(filtered, use_container_width=True, height=320)
            csv_bytes = filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar selecionados (Cor)", csv_bytes, "cor_selecionados.csv", mime="text/csv")

    with st.expander("Microbiologia — módulo opcional, não necessário para a pergunta principal atual"):
        st.write("O estudo principal está focado na estabilidade química das antocianinas e na resposta colorimétrica ao pH. Você não precisa cadastrar testes microbiológicos para executar essa parte. Esta área fica apenas para eventual consulta de registros antigos ou uso futuro, caso o projeto passe a avaliar estabilidade microbiológica, segurança ou prazo de validade para uma aplicação específica.")
        micro = read_micro()
        if micro.empty:
            st.caption("Nenhum registro microbiológico. Não é necessário preencher este arquivo para seguir com o estudo principal.")
        else:
            st.dataframe(micro, use_container_width=True, height=260)
            st.download_button("Exportar registros microbiológicos", micro.to_csv(index=False).encode("utf-8"), "microbiologia_registros.csv", mime="text/csv")

    st.divider()
    st.subheader("Como a gravação é protegida")
    st.write("- Novos registros são validados antes da gravação.")
    st.write("- Registros duplicados são recusados; nada é sobrescrito silenciosamente.")
    st.write("- Um backup timestampado do CSV é criado antes de acrescentar novos registros.")

def _row_micro() -> dict:
    """Campos microbiológicos com os mesmos rótulos orientados dos demais cadastros."""
    return {
        "batch_id": st.text_input("Lote independente (batch_id)", placeholder="ex.: B01", help="Use o mesmo código da extração correspondente nas demais tabelas do estudo."),
        "formulation": st.text_input("Formulação (formulation)", placeholder="ex.: F_NATIVE ou F_PH3", help="Código consistente com os cadastros de estabilidade e cor."),
        "storage_condition": st.text_input("Condição de armazenamento", placeholder="ex.: C4_DARK ou C25_DARK", help="Use os mesmos códigos padronizados nas demais tabelas."),
        "day": st.text_input("Tempo de armazenamento (dias)", placeholder="ex.: 0, 7 ou 14", help="Dias desde o início do armazenamento; dia 0 é a medição basal."),
        "vial_id": st.text_input("Código do frasco/amostra (vial_id)", placeholder="ex.: B01_D07_R1", help="Código da unidade física analisada, ligado ao registro da amostra."),
        "test_type": st.text_input("Tipo de teste microbiológico", placeholder="ex.: PCR, contagem, enumeração", help="Descreva qual teste foi realizado. Estabilidade química NÃO substitui esse dado."),
        "result_value": st.text_input("Resultado numérico (result_value)", placeholder="ex.: 2.3", help="Valor realmente obtido no teste microbiológico. Deixe vazio se o teste não foi realizado."),
        "result_unit": st.text_input("Unidade do resultado (result_unit)", placeholder="ex.: CFU/g, log CFU/mL", help="Unidade do valor informado acima, conforme o método aplicado."),
        "method": st.text_input("Método (opcional)", placeholder="ex.: protocolo ou norma utilizada", help="Referência do método/protocolo empregado; campo opcional."),
        "notes": st.text_area("Observações", height=60, placeholder="Condições, desvios ou ocorrências relevantes", help="Não inferir segurança microbiológica a partir da estabilidade química."),
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
        submitted = st.form_submit_button("Salvar medição", type="primary")
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
    st.header("Simulador de estabilidade")
    st.markdown("""
    **Para que serve:** explorar como uma curva hipotética de perda de antocianinas mudaria sob temperaturas e fatores de influência diferentes. O modelo usado é de primeira ordem com correção de temperatura por Arrhenius.

    **O que este simulador não faz:** não extrai parâmetros automaticamente das referências, não calcula um pH real a partir do fator de pH e não determina prazo de validade. Os fatores de pH, luz, oxigênio e embalagem são hipóteses explícitas até serem estimados para este extrato por dados apropriados.
    """)
    st.warning("Todos os resultados desta página são SIMULADOS. Não use valores fictícios para preencher lacunas nem apresente a curva como medição, previsão validada ou prova de estabilidade.")

    if not CONFIG_PATH.exists():
        st.info("Arquivo de configuração não encontrado. Execute `python anthocyanin_lab.py init --dir .` na raiz do projeto.")
        return
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        st.error(f"Configuração inválida: {exc}")
        return

    st.subheader("1. Parâmetros de referência do modelo")
    st.caption("Preencha somente quando houver uma fonte ou ajuste experimental compatível. Se ainda não tiver meia-vida e energia de ativação justificáveis, não interprete a saída como estimativa do seu extrato.")
    ref_temp = st.number_input(
        "Temperatura de referência (°C)",
        value=float(cfg.get("reference_temperature_c", 25.0)), format="%.2f",
        help="Temperatura à qual corresponde a meia-vida de referência informada abaixo. As duas entradas precisam descrever a mesma condição e unidade de sistema (matriz/solvente/formulação). Não é necessariamente a temperatura em que pretende guardar o produto.",
    )
    ref_hl = st.number_input(
        "Meia-vida de referência (dias)",
        min_value=0.0,
        value=(float(cfg.get("reference_half_life_days", 0)) if cfg.get("reference_half_life_days") is not None else 0.0), format="%.2f",
        help="Tempo estimado para o modelo de primeira ordem reduzir o valor de referência à metade na temperatura acima. Procure esse parâmetro em artigo com matriz, solvente, pH e condições próximas, ou ajuste-o aos seus dados reais. Registre a fonte/condições no caderno; não copie um número de outra matriz sem justificativa.",
    )
    ea = st.number_input(
        "Energia de ativação aparente (kJ/mol)", min_value=0.0,
        value=(float(cfg.get("activation_energy_kj_mol", 0)) if cfg.get("activation_energy_kj_mol") is not None else 0.0), format="%.2f",
        help="Parâmetro que descreve quanto a taxa de degradação muda com a temperatura no modelo de Arrhenius. Idealmente é estimado com taxas medidas em várias temperaturas ou obtido de estudo compatível. Não é uma energia universal das antocianinas; se não há valor defensável, não invente.",
    )
    init_pct = st.number_input(
        "Retenção inicial normalizada (%)", min_value=0.0,
        value=float(cfg.get("initial_retention_pct", 100.0)), format="%.2f",
        help="Valor do instante inicial da curva. Use 100 para expressar retenção relativa ao dia 0; outro valor só faz sentido se houver razão explícita para normalizar a curva de outra forma. Não representa diretamente concentração em mg/L.",
    )
    days = st.text_input(
        "Dias em que deseja calcular a curva",
        value=",".join(str(d) for d in cfg.get("days", [0, 3, 7, 10, 14, 28])),
        help="Lista de tempos em dias, separada por vírgulas (ex.: 0,3,7,14,28). São pontos da saída matemática, não medições que ocorreram de fato.",
    )

    st.subheader("2. Cenários de armazenamento")
    st.caption("Edite a temperatura de cada cenário. Os quatro fatores seguintes multiplicam a taxa de degradação: 1,0 = sem efeito presumido; acima de 1,0 = degradação mais rápida; abaixo de 1,0 = degradação mais lenta. Esses efeitos precisam de evidência para serem interpretados como reais.")
    scenarios = cfg.get("scenarios", [])
    edited_scenarios = []
    for i, s in enumerate(scenarios):
        with st.container(border=True):
            st.markdown(f"**Cenário {i + 1}**")
            sid = st.text_input(f"Identificador do cenário {i + 1}", value=str(s.get("scenario_id", i)), key=f"sim_sid_{i}", help="Código curto, único e consistente, por exemplo C4_DARK. Serve para identificar a curva na tabela/exportação.")
            label = st.text_input(f"Nome do cenário {i + 1}", value=str(s.get("label", "")), key=f"sim_label_{i}", help="Nome legível com a condição real/hipotética (ex.: 4 °C, escuro). Não substitui a identificação completa no protocolo.")
            temp = st.number_input(f"Temperatura do cenário {i + 1} (°C)", value=float(s.get("temperature_c", 4.0)), format="%.2f", key=f"sim_temp_{i}", help="Temperatura que será usada no fator de Arrhenius para esta curva. Compare apenas com faixas suportadas pela fonte/experimento; extrapolações podem ser pouco confiáveis.")
            c1, c2 = st.columns(2)
            with c1:
                ph_f = st.number_input(f"Fator de pH {i + 1}", min_value=0.0, value=float(s.get("pH_factor", 1.0)), format="%.3f", key=f"sim_ph_{i}", help="Multiplicador hipotético da taxa para representar um efeito do pH. Não é o valor de pH (ex.: 3,0) e não calcula esse efeito a partir do pH. Use 1,0 se ainda não mediu/justificou um efeito.")
                light_f = st.number_input(f"Fator de luz {i + 1}", min_value=0.0, value=float(s.get("light_factor", 1.0)), format="%.3f", key=f"sim_light_{i}", help="Multiplicador hipotético para exposição à luz. 1,0 equivale a não alterar a taxa; valores diferentes exigem resultados/estudo compatível para justificá-los.")
            with c2:
                oxygen_f = st.number_input(f"Fator de oxigênio {i + 1}", min_value=0.0, value=float(s.get("oxygen_factor", 1.0)), format="%.3f", key=f"sim_oxygen_{i}", help="Multiplicador hipotético ligado a disponibilidade de oxigênio/espaço de cabeça. Não mede oxigênio no frasco e não deve variar se o estudo não controla/avalia este fator.")
                pkg_f = st.number_input(f"Fator de embalagem {i + 1}", min_value=0.0, value=float(s.get("packaging_factor", 1.0)), format="%.3f", key=f"sim_pkg_{i}", help="Multiplicador hipotético para efeito da embalagem/barreira. Não é um ranking universal de materiais; só use números diferentes de 1,0 com evidência compatível.")
        edited_scenarios.append({
            "scenario_id": sid, "label": label, "temperature_c": temp,
            "pH_factor": ph_f, "light_factor": light_f, "oxygen_factor": oxygen_f,
            "packaging_factor": pkg_f, "notes": s.get("notes", ""),
        })

    st.info("**Antes de executar:** confirme que a meia-vida e a energia de ativação têm uma fonte identificável e condições compatíveis. As referências são consultadas na página Literatura, mas o simulador não seleciona nem aplica os seus valores automaticamente.")
    if st.button("Executar simulação hipotética", type="primary"):
        if ref_hl <= 0 or ea <= 0:
            st.error("Para executar, meia-vida e energia de ativação precisam ser positivas. Não substitua a falta desses parâmetros por valores aleatórios; localize fontes compatíveis ou aguarde dados experimentais.")
            return
        if not edited_scenarios:
            st.error("Não há cenários definidos no arquivo de configuração.")
            return
        try:
            days_list = [float(d.strip()) for d in days.split(",") if d.strip()]
        except ValueError:
            st.error("Não entendi a lista de dias. Use números separados por vírgula, como 0,3,7,14,28.")
            return
        if not days_list or any(d < 0 for d in days_list):
            st.error("Informe pelo menos um dia não negativo.")
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
        except (ValueError, KeyError) as exc:
            st.error(f"Simulação recusada: {exc}")
            return

        st.success("Cálculo concluído — isso confirma apenas a execução matemática, não a validade científica dos parâmetros.")
        st.subheader("3. Resultados da simulação")
        st.caption(
            f"Contexto do cálculo: temperatura de referência {ref_temp:.2f} °C · meia-vida de referência {ref_hl:.2f} dias · "
            f"energia de ativação {ea:.2f} kJ/mol · retenção inicial {init_pct:.2f}%."
        )
        chart = results.groupby(["day", "scenario_label"], dropna=False)["retention_pct_simulated"].mean().unstack("scenario_label")
        st.line_chart(chart, use_container_width=True)
        st.caption(
            "Retenção simulada (%) por dia, uma curva por cenário (nome do cenário na legenda). "
            "Os pontos são saídas do modelo — nenhuma linha corresponde a uma medição de laboratório."
        )
        st.dataframe(results, use_container_width=True, height=360)
        st.caption(
            "Colunas principais: retention_pct_simulated = retenção simulada (%); k_per_day_simulated = constante cinética simulada (1/dia); "
            "half_life_days_simulated = meia-vida simulada (dias); arrhenius_factor e combined_factor = multiplicadores adimensionais aplicados à taxa. "
            "Origem: SIMULATION_ONLY — os resultados permanecem separados dos dados experimentais e não demonstram prazo de validade, "
            "segurança ou desempenho real do indicador."
        )

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
    st.markdown("Esta página é para **consultar as fontes e entender que tipo de informação cada estudo fornece**; não é um formulário para digitar resultados. Os campos de citação, DOI/URL e localização da fonte permanecem ligados aos registros existentes. A presença de uma referência no catálogo não significa, por si só, que cada valor publicado já foi conferido no texto original.")
    st.info("**Como navegar:** em *Estudos*, consulte a referência bibliográfica, matriz, solvente e limitações; em *Medições*, veja valores publicados e séries no tempo; em *Evidências*, veja resumos cinéticos ou afirmações qualitativas. Mantenha separados valores diretamente reportados e valores calculados a partir deles.")

    tab_st, tab_me, tab_ev = st.tabs(["Estudos e referências", "Medições publicadas", "Evidências e parâmetros"])
    with tab_st:
        st.subheader("Estudos e referências bibliográficas")
        st.caption("Use DOI/URL para abrir a fonte primária e confira se a matriz, o solvente, o pH, a temperatura e o método combinam com o seu estudo.")
        data = read_literature_studies()
        cols = ["study_id", "citation", "doi", "url", "species", "matrix", "solvent", "analysis_unit", "limitations"]
        if not data.empty:
            st.dataframe(data[cols], use_container_width=True, height=360)
        else:
            st.info("Nenhum estudo de literatura carregado.")

    with tab_me:
        st.subheader("Valores e séries temporais publicados")
        st.caption("Cada linha deve manter estudo, tratamento, tempo/unidade, variável/unidade e localização exata da fonte. Valores ausentes na publicação devem continuar vazios; não complete por suposição.")
        data = read_literature_measurements()
        if not data.empty:
            origin = data["data_origin"].fillna("").astype(str)
            reported = data["reported_or_calculated"].fillna("").astype(str)
            st.caption("PUBLISHED_ARTICLE identifica a origem bibliográfica. reported_or_calculated distingue o que foi transcrito da fonte do que foi calculado posteriormente.")
            pub = data[origin == "PUBLISHED_ARTICLE"]
            if not pub.empty:
                pub_cols = ["study_id", "treatment_id", "time_value", "time_unit", "measurement", "value", "value_unit", "standard_deviation", "replicate_count", "source_location", "package_material", "data_origin", "reported_or_calculated"]
                st.dataframe(pub[pub_cols], use_container_width=True, height=360)
            else:
                st.info("Nenhuma medição publicada (PUBLISHED_ARTICLE) encontrada.")
        else:
            st.info("Nenhuma medição de literatura gravada ainda.")

    with tab_ev:
        st.subheader("Evidências narrativas e parâmetros resumidos")
        st.caption("Use a localização da fonte e as condições descritas para rastrear cada informação. Resumos de meia-vida/constante cinética não são equivalentes a uma série temporal completa.")
        data = read_literature_evidence()
        cols = ["study_id", "evidence_type", "evidence_category", "evidence_text", "origin_source", "source_url", "source_location", "conditions", "temperature_c", "pH", "half_life", "k_value", "notes"]
        if not data.empty:
            st.dataframe(data[cols], use_container_width=True, height=360)
        else:
            st.info("Nenhuma evidência de literatura carregada.")

    st.divider()
    st.warning("Antes de usar um valor como parâmetro científico, verifique o texto integral, local exato da tabela/figura, unidade, condição experimental e se é reportado ou calculado. O status de referência não valida automaticamente os números nem autoriza transferi-los para o extrato deste projeto.")

@st.cache_data
def read_ml_observations() -> pd.DataFrame:
    return read_raw(ML_CSV, lab.ml_template_columns())


def render_ml() -> None:
    st.header("Aprendizado de máquina")
    st.caption("Módulo exploratório do ``anthocyanin_lab.train_ml_model``. "
               "Por padrão usa somente ``data_origin=EXPERIMENTAL``; literatura exige mapeamento manual.")
    st.info("Esta página não é o lugar para cadastrar os dados de bancada. Primeiro preencha medições reais nas páginas de estabilidade/cor e, quando houver linhas suficientes, registre-as conscientemente em `data/raw/ml_observations.csv`. Simulação não pode ser misturada aos dados experimentais. O modelo é exploratório e não serve para declarar prazo de validade.")

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
    target = st.selectbox("Variável-alvo", lab.ML_ALLOWED_TARGETS, help="Escolha o resultado que o modelo tentaria estimar: retention_pct = retenção relativa de antocianinas; tac_mg_c3g_L = teor em equivalentes de cianidina-3-glicosídeo por litro; delta_e_cie76_vs_day0 = diferença de cor CIELAB em relação ao dia 0. Só escolha um alvo quando esses valores tiverem sido medidos/calculados por método documentado.")
    include_literature = st.checkbox("Incluir literatura (mapeamento manual)", value=False, help="Deixe desmarcado no fluxo normal. A inclusão requer mapeamento manual e pelo menos cinco estudos distintos; ainda assim, a diferença entre matrizes/métodos limita as conclusões.")
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
    """Monta a aplicação e preserva a navegação já existente."""
    apply_theme()
    st.markdown(
        """<div class="lab-topbar">
          <div class="lab-brand">
            <div class="lab-logo">🧪</div>
            <div><div class="lab-brand-name">ANTOCIANINAS LAB</div>
            <div class="lab-brand-sub">Pesquisa · estabilidade de extrato líquido de repolho roxo</div></div>
          </div>
          <div class="lab-local-pill">● AMBIENTE LOCAL</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """<div style="padding:.5rem .25rem 1.1rem">
          <div class="lab-side-name">ANTOCIANINAS LAB</div>
          <div class="lab-side-sub">Bancada digital de pesquisa<br>Registros locais · proveniência explícita</div>
        </div><div class="lab-side-label">NAVEGAÇÃO</div>""",
        unsafe_allow_html=True,
    )
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
    current = st.session_state.get("active_page", "Painel inicial")
    if current not in pages:
        current = "Painel inicial"
    page = st.sidebar.radio(
        "Seção", pages, index=pages.index(current), key="active_page", label_visibility="collapsed"
    )
    st.sidebar.markdown(
        """<div style="margin-top:1.2rem;padding:.8rem .65rem;border:1px solid rgba(255,255,255,.15);border-radius:12px;background:rgba(255,255,255,.045)">
          <div style="font-size:.72rem;font-weight:800;color:#e6d6f7;margin-bottom:.3rem">NOTA DE INTEGRIDADE</div>
          <div style="font-size:.76rem;line-height:1.5;color:#d5ccdf">Literatura, simulação e medições experimentais são mantidas separadas. Nenhum valor de laboratório é criado automaticamente.</div>
        </div>""",
        unsafe_allow_html=True,
    )

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

