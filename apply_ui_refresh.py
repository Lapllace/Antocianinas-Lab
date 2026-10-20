from __future__ import annotations

"""Aplica uma atualização visual conservadora à interface Streamlit do Antocianinas Lab.

Execute na raiz do repositório: python apply_ui_refresh.py
Cria backup automático de anthocyanin_ui.py e não altera os dados científicos.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

UI_THEME_CONTENT = r'''"""Tema visual da interface Antocianinas Lab (camada de apresentação apenas)."""

import streamlit as st


_CSS = r"""
<style>
:root {
  --anthocyanin-950: #211b35;
  --anthocyanin-800: #38265e;
  --anthocyanin-700: #522d87;
  --anthocyanin-600: #6b35a4;
  --anthocyanin-100: #f0e8fa;
  --rose-500: #dd5579;
  --ink-900: #252239;
  --ink-600: #716d82;
  --surface: #ffffff;
  --canvas: #f7f6fb;
  --line: #e9e6f0;
}

.stApp { background: var(--canvas); color: var(--ink-900); }
.block-container { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 3rem; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: rgba(247,246,251,.88); }

/* Sidebar com identidade de laboratório e navegação mais evidente. */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--anthocyanin-950) 0%, #302447 100%);
  border-right: 1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  color: #f5f1fb !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border-radius: 10px;
  padding: .38rem .5rem;
  transition: background .15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,.09); }
[data-testid="stSidebar"] [data-testid="stRadio"] p { font-size: .92rem; }

/* Barra superior e identidade. */
.lab-topbar {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  margin: 0 0 1.45rem; padding: 1rem 1.25rem; background: var(--surface);
  border: 1px solid var(--line); border-radius: 18px;
  box-shadow: 0 6px 22px rgba(42, 27, 68, .035);
}
.lab-brand { display: flex; align-items: center; gap: .85rem; min-width: 0; }
.lab-logo {
  display: grid; place-items: center; width: 44px; height: 44px; flex: 0 0 44px;
  border-radius: 14px; color: white; font-size: 1.25rem;
  background: linear-gradient(140deg, var(--anthocyanin-600), var(--rose-500));
  box-shadow: 0 5px 12px rgba(107,53,164,.2);
}
.lab-brand-name { color: var(--ink-900); font-size: 1rem; line-height: 1.25; font-weight: 800; letter-spacing: .015em; }
.lab-brand-sub { color: var(--ink-600); font-size: .78rem; margin-top: .2rem; }
.lab-local-pill {
  color: var(--anthocyanin-700); background: var(--anthocyanin-100); border: 1px solid #e4d6f5;
  border-radius: 999px; padding: .4rem .7rem; font-weight: 700; font-size: .72rem;
  letter-spacing: .045em; white-space: nowrap;
}
.lab-hero {
  position: relative; overflow: hidden; margin: .2rem 0 1.25rem; padding: 1.8rem 1.8rem 1.7rem;
  color: white; border-radius: 22px;
  background: radial-gradient(circle at 94% 4%, rgba(255,255,255,.20), transparent 30%),
              linear-gradient(115deg, #382257 0%, #63369a 55%, #9850a8 100%);
  box-shadow: 0 12px 30px rgba(73, 43, 111, .14);
}
.lab-hero-kicker { color: #e8d8fa; font-size: .72rem; text-transform: uppercase; letter-spacing: .14em; font-weight: 800; }
.lab-hero h2 { color: white !important; margin: .55rem 0 .5rem; font-size: clamp(1.5rem, 2.6vw, 2.2rem); line-height: 1.15; }
.lab-hero p { color: #f0e9f8; margin: 0; max-width: 760px; font-size: .96rem; line-height: 1.6; }
.lab-hero-foot { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1rem; }
.lab-hero-chip { border: 1px solid rgba(255,255,255,.24); background: rgba(255,255,255,.10); color: white; border-radius: 999px; padding: .3rem .65rem; font-size: .72rem; }

h1, h2, h3 { color: var(--ink-900); letter-spacing: -.025em; }
h1 { font-weight: 800; }
h2 { font-weight: 750; }
h3 { font-weight: 700; }
[data-testid="stMetric"] {
  background: white; border: 1px solid var(--line); border-radius: 16px;
  padding: 1rem 1.1rem; box-shadow: 0 5px 18px rgba(35,25,57,.035);
}
[data-testid="stMetricLabel"] { color: var(--ink-600); font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--anthocyanin-800); font-weight: 800; }
[data-testid="stMetricDelta"] { font-size: .75rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--line) !important; border-radius: 16px !important; }
[data-testid="stAlert"] { border-radius: 13px; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 11px; font-weight: 700; border: 1px solid #d9c9eb;
  transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
  color: white; background: linear-gradient(110deg, var(--anthocyanin-700), var(--anthocyanin-600)); border: 0;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-1px); box-shadow: 0 5px 14px rgba(82,45,135,.12); }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  border-radius: 10px;
}
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .3rem; }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 10px 10px 0 0; padding: .55rem .9rem; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--anthocyanin-700); }
hr { border-color: var(--line); }
.lab-section-caption { margin: -.45rem 0 1rem; color: var(--ink-600); font-size: .9rem; }
.lab-empty-card { background: white; border: 1px dashed #d8cde7; border-radius: 16px; padding: 1.2rem 1.3rem; color: var(--ink-600); }
.lab-empty-card strong { display: block; color: var(--ink-900); font-size: 1rem; margin-bottom: .3rem; }
.lab-side-label { margin: 1rem 0 .3rem; font-size: .67rem; letter-spacing: .14em; color: #c8b8e2; font-weight: 800; }
.lab-side-name { color: white; font-weight: 800; font-size: 1.05rem; letter-spacing: .01em; }
.lab-side-sub { color: #cfc5df; font-size: .78rem; margin-top: .3rem; line-height: 1.45; }
@media (max-width: 680px) {
  .block-container { padding-top: .7rem; }
  .lab-topbar { padding: .8rem; }
  .lab-local-pill { font-size: .63rem; }
  .lab-hero { padding: 1.25rem; border-radius: 17px; }
}
</style>
"""


def apply_theme() -> None:
    """Injeta estilos de apresentação; não lê nem modifica dados do projeto."""
    st.markdown(_CSS, unsafe_allow_html=True)
'''

NEW_RENDER_HOME = r'''def render_home(stability: pd.DataFrame, color: pd.DataFrame) -> None:
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
        f_batch = f1.selectbox("Lote", batches, key="home_lote")
        f_formula = f2.selectbox("Formulação", formulations, key="home_formula")
        f_cond = f3.selectbox("Condição de armazenamento", conditions, key="home_cond")
        f_day = f4.selectbox("Dia", ["Todos"] + days, key="home_day")

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
'''

NEW_MAIN = r'''def main() -> None:
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
'''


def _replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, lambda _match: replacement + "\n\n", text, count=1, flags=re.M | re.S)
    if count != 1:
        raise RuntimeError(f"Não consegui localizar com segurança o trecho '{label}'. O arquivo não foi modificado.")
    return updated


def patch_ui_text(original: str) -> str:
    import_anchor = "import anthocyanin_persistence as persist\n"
    import_replacement = import_anchor + "from ui_theme import apply_theme\n"
    if "from ui_theme import apply_theme" in original:
        raise RuntimeError("A interface já importa ui_theme; nada foi alterado para evitar duplicação.")
    if original.count(import_anchor) != 1:
        raise RuntimeError("Não encontrei o ponto de importação esperado. O arquivo não foi modificado.")
    updated = original.replace(import_anchor, import_replacement, 1)
    updated = _replace_once(
        updated,
        r"^def render_home\(stability: pd\.DataFrame, color: pd\.DataFrame\) -> None:\n.*?(?=^def _row_stab\(\) -> dict:)",
        NEW_RENDER_HOME.rstrip(),
        "render_home",
    )
    updated = _replace_once(
        updated,
        r"^def main\(\) -> None:\n.*?(?=^if __name__ == \"__main__\":)",
        NEW_MAIN.rstrip(),
        "main",
    )
    compile(updated, "anthocyanin_ui.py", "exec")
    compile(UI_THEME_CONTENT, "ui_theme.py", "exec")
    return updated


def main() -> int:
    root = Path.cwd()
    ui_path = root / "anthocyanin_ui.py"
    theme_path = root / "ui_theme.py"
    if not ui_path.is_file():
        print("ERRO: execute este script na raiz do projeto, onde existe anthocyanin_ui.py.", file=sys.stderr)
        return 2
    if theme_path.exists() and theme_path.read_text(encoding="utf-8") != UI_THEME_CONTENT:
        print("ERRO: ui_theme.py já existe e é diferente. Nada foi sobrescrito.", file=sys.stderr)
        return 2
    original = ui_path.read_text(encoding="utf-8")
    try:
        updated = patch_ui_text(original)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2

    backup = ui_path.with_name(f"anthocyanin_ui.py.before_ui_refresh_{datetime.now():%Y%m%d_%H%M%S}.bak")
    if backup.exists():
        print("ERRO: o arquivo de backup já existe; nada foi gravado.", file=sys.stderr)
        return 2
    backup.write_text(original, encoding="utf-8")
    ui_path.write_text(updated, encoding="utf-8", newline="\n")
    if not theme_path.exists():
        theme_path.write_text(UI_THEME_CONTENT, encoding="utf-8", newline="\n")
    print("Atualização visual aplicada com sucesso.")
    print(f"Backup original: {backup.name}")
    print("Arquivos alterados: anthocyanin_ui.py; ui_theme.py")
    print("Dados CSV, cálculos científicos, modelos de simulação e critérios de ML não foram alterados.")
    print("Próximo passo: python -m streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
