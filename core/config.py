# core/config.py
import streamlit as st

# 🔑 Clave de API para EODHD desde Streamlit Secrets
API_KEY = st.secrets["EODHD_API_KEY"]

# 📅 Parámetros generales
NEWS_DAYS_BACK = 60  # cantidad de días atrás para buscar noticias
