import streamlit as st
from core.data_fetch import fetch_fundamentals, fetch_news, fetch_eod_ohlc, fetch_realtime
from core.utils import sma, ema, rsi
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def show_dashboard():
    st.title("AppFinanzAr — Dashboard")

    # -------------------------
    # Sidebar inputs
    # -------------------------
    sidebar = st.sidebar
    sidebar.markdown("### Configuración del Dashboard")
    
    ticker = sidebar.text_input("Ticker (ej: MELI.US, AAPL)", "MELI.US", key="dashboard_ticker")
    range_days = sidebar.selectbox("Rango rápido", options=["1m","3m","6m","1y","5y","max"], index=0)
    custom_range = sidebar.checkbox("Usar rango personalizado")
    if custom_range:
        start_date = sidebar.date_input("Fecha inicio", value=(datetime.today() - timedelta(days=30)))
        end_date = sidebar.date_input("Fecha fin", value=datetime.today())
    else:
        today = datetime.today().date()
        if range_days == "1m":
            start_date = today - timedelta(days=30)
        elif range_days == "3m":
            start_date = today - timedelta(days=90)
        elif range_days == "6m":
            start_date = today - timedelta(days=180)
        elif range_days == "1y":
            start_date = today - timedelta(days=365)
        elif range_days == "5y":
            start_date = today - timedelta(days=365*5)
        else:
            start_date = today - timedelta(days=365*10)
        end_date = today

    # -------------------------
    # Technical overlays settings
    # -------------------------
    sidebar.markdown("---")
    st.sidebar.write("### Indicadores técnicos")
    sma_short = sidebar.number_input("SMA corto (días)", value=20, min_value=1)
    sma_long = sidebar.number_input("SMA largo (días)", value=50, min_value=1)
    ema_span = sidebar.number_input("EMA (días)", value=20, min_value=1)
    rsi_period = sidebar.number_input("RSI periodo", value=14, min_value=1)

    # -------------------------
    # Data fetch
    # -------------------------
    from_str = start_date.strftime("%Y-%m-%d")
    to_str = end_date.strftime("%Y-%m-%d")

    with st.spinner("Consultando datos históricos y real-time..."):
        df = fetch_eod_ohlc(ticker, from_date=from_str, to_date=to_str)
        realtime = fetch_realtime(ticker)

    if df is None or df.empty:
        st.error("No se encontraron datos históricos para este ticker.")
        return

    # -------------------------
    # Technical indicators
    # -------------------------
    df["SMA_short"] = sma(df["close"], sma_short)
    df["SMA_long"] = sma(df["close"], sma_long)
    df["EMA"] = ema(df["close"], ema_span)
    df["RSI"] = rsi(df["close"], period=rsi_period)

    # -------------------------
    # Candlestick chart
    # -------------------------
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]
    )])
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_short"], mode="lines", name=f"SMA {sma_short}"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_long"], mode="lines", name=f"SMA {sma_long}"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["EMA"], mode="lines", name=f"EMA {ema_span}"))
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # RSI chart
    # -------------------------
    st.subheader("RSI")
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df["date"], y=df["RSI"], name="RSI"))
    rsi_fig.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(rsi_fig, use_container_width=True)

    # -------------------------
    # Executive summary
    # -------------------------
    st.subheader("Executive Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Último cierre", f"{df['close'].iloc[-1]:.2f}")
        st.write(f"Volumen (último): {int(df['volume'].dropna().iloc[-1]) if 'volume' in df and not df['volume'].dropna().empty else 'N/A'}")
    with col2:
        if realtime:
            st.write("Real-time snapshot")
            st.json(realtime)
        else:
            st.info("Sin snapshot real-time (depende del plan de EODHD)")

    # -------------------------
    # Fundamentals & Competitors
    # -------------------------
    st.subheader("Fundamentales clave y competidores")
    fundamentals, competitors = fetch_fundamentals(ticker)
    if fundamentals:
        st.json(fundamentals)
    else:
        st.info("No se encontraron datos fundamentales.")

    if competitors:
        st.write("Competidores:", ", ".join(competitors))
    else:
        st.info("No se encontraron competidores.")

    # -------------------------
    # News
    # -------------------------
    st.subheader("Noticias recientes")
    news_items = fetch_news(ticker, days_back=60)
    if news_items:
        for n in news_items[:10]:
            st.write(f"- {n.get('title')} ({n.get('published_at')})")
    else:
        st.info("No se encontraron noticias recientes.")
