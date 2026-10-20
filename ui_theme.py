"""Tema visual da interface Antocianinas Lab (camada de apresentação apenas).

Tema escuro como preferência definitiva da interface. A paleta preserva a
identidade visual em tons de roxo (antocianina) com acentos em rosa, mas
todas as superfícies e textos foram revisados para garantir contraste
legível sobre fundo escuro.
"""

import streamlit as st


_CSS = r"""
<style>
:root {
  /* Paleta escura baseada em antocianinas (roxo profundo). */
  --anthocyanin-950: #0f0a1e;
  --anthocyanin-800: #1e1436;
  --anthocyanin-700: #3b2a6b;
  --anthocyanin-600: #5b3ea8;
  --anthocyanin-100: #2a1e44;
  --rose-500: #dd5579;
  /* Textos: alto contraste sobre fundos escuros. */
  --ink-900: #e8e4f0;
  --ink-600: #a9a1b8;
  /* Superfícies e bordas. */
  --surface: #160f26;
  --canvas: #0f0a1e;
  --line: #3d3255;
}

.stApp { background: var(--canvas); color: var(--ink-900); }
.block-container { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 3rem; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: rgba(15, 10, 30, 0.88); }

/* Sidebar com identidade de laboratório e navegação mais evidente. */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--anthocyanin-950) 0%, #160f26 100%);
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
  display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  margin: 0 0 1.45rem; padding: 1rem 1.25rem; background: var(--surface);
  border: 1px solid var(--line); border-radius: 18px;
  box-shadow: 0 6px 22px rgba(42, 27, 68, 0.18);
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
  color: var(--anthocyanin-700); background: var(--anthocyanin-100); border: 1px solid #3d3255;
  border-radius: 999px; padding: .4rem .7rem; font-weight: 700; font-size: .72rem;
  letter-spacing: .045em; white-space: nowrap;
}
.lab-hero {
  position: relative; overflow: hidden; margin: .2rem 0 1.25rem; padding: 1.8rem 1.8rem 1.7rem;
  color: white; border-radius: 22px;
  background: radial-gradient(circle at 94% 4%, rgba(255,255,255,.20), transparent 30%),
              linear-gradient(115deg, #382257 0%, #63369a 55%, #9850a8 100%);
  box-shadow: 0 12px 30px rgba(73, 43, 111, 0.24);
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
  background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
  padding: 1rem 1.1rem; box-shadow: 0 5px 18px rgba(35, 25, 57, 0.25);
}
[data-testid="stMetricLabel"] { color: var(--ink-600); font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--anthocyanin-600); font-weight: 800; }
[data-testid="stMetricDelta"] { font-size: .75rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--line) !important; border-radius: 16px !important; }
[data-testid="stAlert"] { border-radius: 13px; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 11px; font-weight: 700; border: 1px solid #3d3255;
  transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
  color: white; background: linear-gradient(110deg, var(--anthocyanin-700), var(--anthocyanin-600)); border: 0;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-1px); box-shadow: 0 5px 14px rgba(82,45,135,.12); }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  border-radius: 10px;
  background: var(--surface);
  color: var(--ink-900);
  border: 1px solid var(--line);
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
  color: var(--ink-600);
  opacity: 1;
}
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .3rem; }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 10px 10px 0 0; padding: .55rem .9rem; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--anthocyanin-600); }
hr { border-color: var(--line); }
.lab-section-caption { margin: -.45rem 0 1rem; color: var(--ink-600); font-size: .9rem; }
.lab-empty-card { background: var(--surface); border: 1px dashed #3d3255; border-radius: 16px; padding: 1.2rem 1.3rem; color: var(--ink-600); }
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
