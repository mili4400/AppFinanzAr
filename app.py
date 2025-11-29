# app.py
import streamlit as st
from core.auth import init_session
from ui.login_ui import login_screen
from ui.dashboard_ui import show_dashboard

st.set_page_config(page_title="AppFinanzAr", layout="wide", initial_sidebar_state="expanded")

init_session()

# Sidebar usuario/logout
st.sidebar.title("AppFinanzAr")
if st.session_state.get("logged_in"):
    st.sidebar.write(f"Usuario: **{st.session_state['username']}**")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()

# Login o dashboard
if not st.session_state.get("logged_in"):
    login_screen()
    st.stop()
else:
    show_dashboard()
