"""Ponto de entrada da interface gráfica Streamlit.

Execução local:

    python -m streamlit run app.py

A aplicação fica restrita ao navegador do host; nenhum dado do laboratório
é enviado à rede.
"""

from pathlib import Path

import streamlit as st

# Garante que o diretório do projeto esteja na busca de módulos.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in st.session_state:
    st.session_state[str(ROOT)] = str(ROOT)

from anthocyanin_ui import main  # noqa: E402

if __name__ == "__main__":
    main()
