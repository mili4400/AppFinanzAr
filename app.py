import streamlit as st
from datetime import datetime, timedelta
from core.auth import init_session
from ui.login_ui import login_screen
from ui.dashboard_ui import show_dashboard
from core.config import API_KEY
from core.data_fetch import fetch_fundamentals, fetch_news

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="AppFinanzAr", layout="wide", initial_sidebar_state="expanded")

# -------------------------
# Init session
# -------------------------
init_session()

# -------------------------
# Login control
# -------------------------
if not st.session_state["logged_in"]:
    login_screen()
else:
    show_dashboard()

# -------------------------
# Sidebar & session helpers
# -------------------------
sidebar = st.sidebar
sidebar.title("AppFinanzAr")
sidebar.write(f"Usuario: **{st.session_state.get('username')}**")
sidebar.markdown("---")

if sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.experimental_rerun()

# -------------------------
# Favorites
# -------------------------
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

symbol = sidebar.text_input("Buscar ticker (ej: AAPL, TSLA)", value="AAPL", key="sidebar_symbol")
if sidebar.button("Agregar a Favoritos"):
    if symbol and symbol.upper() not in st.session_state["favorites"]:
        st.session_state["favorites"].append(symbol.upper())
        st.success(f"{symbol.upper()} agregado a Favoritos")

sidebar.write("### Favoritos")
for f in st.session_state["favorites"]:
    sidebar.write(f"- {f}")

# -------------------------
# Fetch fundamentals, competitors, news
# -------------------------
st.subheader("Fundamentales y competidores")
fundamentals, competitors = fetch_fundamentals(symbol)
st.write("Competidores:", competitors)
st.json(fundamentals)

st.subheader("Noticias")
news_items = fetch_news(symbol)
if news_items:
    for n in news_items:
        st.write(f"- {n.get('title')} ({n.get('date')})")
else:
    st.info("No hay noticias disponibles.")

