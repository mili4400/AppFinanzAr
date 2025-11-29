
import streamlit as st

def render_header(user):
    st.sidebar.title("FinanzApp")
    st.sidebar.write(f"Usuario: {user}")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.user=None
        st.experimental_rerun()

def ticker_search_box():
    return st.text_input("Buscar Ticker:", "")
