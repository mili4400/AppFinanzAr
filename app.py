# app.py
import streamlit as st
from core.auth import init_session
from ui.login_ui import login_screen
from ui.dashboard_ui import show_dashboard

st.set_page_config(page_title="AppFinanzAr", layout="wide")

init_session()

# Si no está logueado → mostrar login
if not st.session_state["logged_in"]:
    login_screen()
else:
    show_dashboard()

