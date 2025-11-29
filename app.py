# app.py
import streamlit as st
from core.auth import init_session
from ui.login_ui import login_screen
from ui.dashboard_ui import show_dashboard

# -------------------------
# Inicializar session_state
# -------------------------
init_session()

# -------------------------
# Page config & style
# -------------------------
st.set_page_config(
    page_title="AppFinanzAr",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema oscuro básico
st.markdown(
    """
    <style>
    .reportview-container { background: #0e1117; color: #dbe6ff; }
    .sidebar .sidebar-content { background: #0b0f14; color: #dbe6ff; }
    .stButton>button { background: #1f2937; color: #fff; border: none; }
    </style>
    """, unsafe_allow_html=True
)

# -------------------------
# Autenticación
# -------------------------
if not st.session_state["logged_in"]:
    login_screen()
    st.stop()  # No continuar hasta login

# -------------------------
# Mostrar dashboard
# -------------------------
show_dashboard()

