# app.py
import streamlit as st
from core.auth import init_session
from ui.login_ui import login_screen
from ui.dashboard_ui import show_dashboard
from core.fundamentals import fetch_fundamentals


st.set_page_config(page_title="AppFinanzAr", layout="wide")
init_session()

# Sidebar: cerrar sesión
if st.session_state.get("logged_in", False):
    with st.sidebar:
        if st.button("🔒 Cerrar sesión"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""

# Mostrar pantalla según login
if not st.session_state["logged_in"]:
    login_screen()
else:
    show_dashboard()
