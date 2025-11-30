# core/config.py
import streamlit as st
import os

"""
Carga segura de API_KEY compatible con Streamlit Cloud.
1) Intenta leer desde st.secrets.
2) Si no existe, usa variable de entorno.
3) Si tampoco existe, usa string vacío (modo limitado).
"""

API_KEY = ""

# 1) Intentar con Streamlit Secrets
try:
    API_KEY = st.secrets["EODHD_API_KEY"]
except Exception:
    pass

# 2) Intentar con variables de entorno si está vacío
if not API_KEY:
    API_KEY = os.getenv("EODHD_API_KEY", "")

# 📅 Parámetros generales
NEWS_DAYS_BACK = 60
