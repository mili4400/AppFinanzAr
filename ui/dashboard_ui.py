# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from core.data_fetch import (
    fetch_ohlc,
    fetch_fundamentals,
    fetch_news,
    search_ticker_by_name
)

from core.overview import build_overview
from core.etf_finder import etf_screener
from core.favorites import load_favorites, add_favorite
from core.compare_pro import compare_indicators, compare_sentiment
from core.utils import sma, ema, rsi
from core.sentiment_model import sentiment_score


# ----------------------------------------------------
# DEMO TICKERS (sin consumir API)
# ----------------------------------------------------
DEMO_TICKERS = {
    "MSFT": "Microsoft Corp.",
    "AAPL": "Apple Inc.",
    "AMZN": "Amazon.com",
    "TSLA": "Tesla Inc.",
    "MELI": "Mercado Libre",
    "GGAL": "Grupo Galicia",
    "BMA": "Banco Macro"
}

# ----------------------------------------------------
# HELPER: sentimiento traducido
# ----------------------------------------------------
def interpretar_sentimiento(valor):
    if valor is None:
        return "N/A"
    if valor > 0.2:
        return "📈 Positivo"
    if valor < -0.2:
        return "📉 Negativo"
    return "➖ Neutro"

# ----------------------------------------------------
# HELPER: tarjeta overview compacta
# ----------------------------------------------------
def mostrar_overview_card(data):
    st.markdown("### 📄 Resumen Ejecutivo")
    if not data:
        st.info("No hay overview disponible. Usando datos demo.")
        data = {
            "Name": "Empresa Demo",
            "Sector": "Tecnología",
            "Industry": "Software",
            "MarketCapitalization": "1.5T",
            "Description": "Descripción no disponible en la API gratuita."
        }

    st.markdown(
        f"""
        <div style="padding:15px; border-radius:12px; background:#111827; border:1px solid #333;">
            <h3 style="margin-bottom:8px;">{data.get('Name','N/A')}</h3>
            <p><b>Sector:</b> {data.get('Sector','N/A')}</p>
            <p><b>Industria:</b> {data.get('Industry','N/A')}</p>
            <p><b>Market Cap:</b> {data.get('MarketCapitalization','N/A')}</p>
            <p style="opacity:0.8; margin-top:12px;">{data.get('Description','Descripción no disponible.')[:300]}...</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------------------------------------------
# HELPER: gráfico OHLC
# ----------------------------------------------------
def mostrar_grafico(df):
    if df is None or df.empty:
        st.warning("No hay datos OHLC disponibles (API gratuita limita consultas).")
        return

    fig = go.Figure(data=[
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"]
        )
    ])
    fig.update_layout(height=400, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# DASHBOARD PRINCIPAL
# ----------------------------------------------------
def show_dashboard():
    st.title("📊 Dashboard de Análisis Financiero")

    # ------------------------------------------------
    # Selector: Buscar ticker directamente
    # ------------------------------------------------
    st.subheader("🔍 Seleccioná un activo")

    ticker_input = st.text_input("Ingresá el ticker (autocompletado):", "")

    auto = []
    if ticker_input:
        auto = search_tickers(ticker_input) or []

    if auto:
        st.write("Sugerencias:")
        st.write(", ".join(auto[:10]))

    # ------------------------------------------------
    # Botón alternativo: No sé el ticker
    # ------------------------------------------------
    st.subheader("❓ No sé el ticker")
    nombre_empresa = st.text_input("Buscá por nombre de empresa:")

    sugerencias_empresa = []
    if nombre_empresa:
        sugerencias_empresa = search_tickers(nombre_empresa) or []
        if sugerencias_empresa:
            st.write("Coincidencias:")
            st.write(", ".join(sugerencias_empresa[:10]))

    # ------------------------------------------------
    # Selección final
    # ------------------------------------------------
    ticker = None

    if st.button("Buscar empresa por nombre") and sugerencias_empresa:
        ticker = sugerencias_empresa[0]
    elif ticker_input:
        ticker = ticker_input.upper()

    # Si no hay ticker seleccionado → mostrar demo implícito
    if not ticker:
        st.info("Modo DEMO: mostrando MSFT, AAPL, AMZN, TSLA, MELI, GGAL, BMA")
        ticker = "MSFT"

    st.markdown(f"### 📌 Ticker seleccionado: **{ticker}**")

    # ------------------------------------------------
    # Cargar Overview / Fundamentals / Peers / Sentiment / News
    # ------------------------------------------------
    overview = fetch_overview(ticker)
    fundamentals = fetch_fundamentals(ticker)
    peers = fetch_peers(ticker)
    sentiment = fetch_sentiment(ticker)
    news = fetch_news(ticker)

    # ------------------------------------------------
    # Mostrar Overview compacto
    # ------------------------------------------------
    mostrar_overview_card(overview)

    # ------------------------------------------------
    # Mostrar Sentimiento
    # ------------------------------------------------
    st.subheader("🧠 Sentimiento del Mercado")
    st.success(interpretar_sentimiento(sentiment))

    # ------------------------------------------------
    # Gráfico OHLC
    # ------------------------------------------------
    st.subheader("📈 Gráfico Histórico")

    df = fetch_price_history(ticker, period="1M")
    mostrar_grafico(df)

    # ------------------------------------------------
    # Fundamentales
    # ------------------------------------------------
    st.subheader("🏢 Fundamentales")

    if not fundamentals:
        st.info("No hay fundamentales desde la API gratuita. Usando datos demo.")
        fundamentals = {
            "P/E": "N/A",
            "EPS": "N/A",
            "ROE": "N/A",
            "Debt/Equity": "N/A"
        }

    st.json(fundamentals)

    # ------------------------------------------------
    # Competidores
    # ------------------------------------------------
    st.subheader("🏭 Competidores")

    if not peers:
        st.info("La API gratuita no provee competidores. Se usan datos demo.")
        peers = ["AAPL", "MSFT", "GOOGL"]

    st.write(", ".join(peers))

    # ------------------------------------------------
    # Noticias con selector idioma
    # ------------------------------------------------
    st.subheader("📰 Noticias")

    idioma = st.selectbox("Idioma", ["Inglés", "Español"])

    if news:
        for n in news[:5]:
            titulo = n.get("title", "Sin título")
            desc = n.get("description", "")

            if idioma == "Español":
                # traducción básica
                desc = desc.replace("the", "el/la").replace("and", "y")

            st.markdown(f"**{titulo}**")
            st.write(desc)
            st.markdown("---")
    else:
        st.warning("No hay noticias disponibles en la API gratuita.")

