
import streamlit as st
from core.auth import AuthManager
from core.eodhd_api import EODHDClient
from ui.components import render_header, ticker_search_box
from ui.charts import render_candlestick
from core.utils import load_json, save_json

st.set_page_config(page_title="FinanzApp", layout="wide")

auth=AuthManager()
api=EODHDClient()

if "user" not in st.session_state:
    st.session_state.user=None

if st.session_state.user is None:
    st.title("FinanzApp - Login")
    username=st.text_input("Usuario")
    password=st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if auth.login(username,password):
            st.session_state.user=username
            st.experimental_rerun()
        else:
            st.error("Credenciales inválidas")
    st.stop()

render_header(st.session_state.user)

ticker=ticker_search_box()

if ticker:
    df=api.get_ohlc(ticker)
    if df is not None and not df.empty:
        render_candlestick(df, ticker)
    else:
        st.error("No se encontraron datos para el ticker.")
