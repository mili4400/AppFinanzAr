import streamlit as st

# Core – sesión / auth
from core.auth import init_session

# UI Screens
from ui.login_ui import login_screen
from ui.dashboard_ui import show_dashboard

# Configuración general
st.set_page_config(page_title="AppFinanzAr", layout="wide")

# Inicializar estado de sesión
init_session()

# -----------------------------------
# BARRA LATERAL: Cerrar sesión
# -----------------------------------
if st.session_state.get("logged_in", False):
    with st.sidebar:
        st.markdown("### 👤 Usuario")
        st.write(f"Bienvenido, **{st.session_state.get('username','')}**")

        if st.button("🔒 Cerrar sesión"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state.clear()
            st.experimental_rerun()

# -----------------------------------
# PANTALLA SEGÚN LOGIN
# -----------------------------------
if not st.session_state.get("logged_in", False):
    login_screen()
else:
    show_dashboard()
