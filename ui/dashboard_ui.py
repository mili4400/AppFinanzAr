# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news
from core.utils import sma, ema, rsi, load_json, save_json
import os
import pandas as pd
from datetime import datetime, timedelta

FAV_PATH = os.path.join("data", "favorites.json")

def show_dashboard():
    # Logo arriba
    st.image("assets/logo_finanzapp.svg", width=150)
    st.title("AppFinanzAr - Dashboard")
    
    # Ticker input
    ticker = st.text_input("Ingrese ticker (ej: MELI.US)", "MELI.US", key="dash_ticker")

    # Rango de fechas rápido
    range_days = st.selectbox("Rango rápido", options=["1m","3m","6m","1y","5y","max"], index=0, key="dash_range")
    custom_range = st.checkbox("Usar rango personalizado", key="dash_custom_range")

    if custom_range:
        start_date = st.date_input("Fecha inicio", value=(datetime.today() - timedelta(days=30)), key="dash_start")
        end_date = st.date_input("Fecha fin", value=datetime.today(), key="dash_end")
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

    # Sidebar favoritos
    if not os.path.exists(FAV_PATH):
        save_json(FAV_PATH, [])
    favorites = load_json(FAV_PATH, [])
    if st.sidebar.button("Agregar a Favoritos") and ticker.upper() not in favorites:
        favorites.append(ticker.upper())
        save_json(FAV_PATH, favorites)
        st.success(f"{ticker.upper()} agregado a Favoritos")
    st.sidebar.write("### Favoritos")
    for f in favorites:
        st.sidebar.write(f"- {f}")

    # SMA/EMA/RSI
    sma_short = st.sidebar.number_input("SMA corto", value=20)
    sma_long = st.sidebar.number_input("SMA largo", value=50)
    ema_span = st.sidebar.number_input("EMA", value=20)
    rsi_period = st.sidebar.number_input("RSI periodo", value=14)

    if ticker:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
        if df.empty:
            st.error("No se encontraron datos históricos.")
            return

        # Cálculos técnicos
        df["SMA_short"] = sma(df["close"], sma_short)
        df["SMA_long"] = sma(df["close"], sma_long)
        df["EMA"] = ema(df["close"], ema_span)
        df["RSI"] = rsi(df["close"], rsi_period)

        # Candlestick
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]
        )])
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_short"], mode="lines", name=f"SMA {sma_short}"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_long"], mode="lines", name=f"SMA {sma_long}"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["EMA"], mode="lines", name=f"EMA {ema_span}"))
        fig.update_layout(template="plotly_dark", height=600)
        st.plotly_chart(fig, use_container_width=True)

        # RSI
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(x=df["date"], y=df["RSI"], name="RSI"))
        rsi_fig.update_layout(template="plotly_dark", height=200)
        st.plotly_chart(rsi_fig, use_container_width=True)

        # Fundamentales
        fundamentals, competitors = fetch_fundamentals(ticker)
        st.subheader("Fundamentales clave")
        if fundamentals:
            df_f = pd.DataFrame.from_dict(fundamentals, orient="index", columns=["Valor"])
            st.dataframe(df_f)
        else:
            st.info("No se encontraron fundamentales.")

        # Competidores
        st.subheader("Competidores")
        if competitors:
            st.write(", ".join(competitors))
        else:
            st.info("No se encontraron competidores.")

        # Noticias
        st.subheader("Noticias recientes")
        news_items = fetch_news(ticker)
        if news_items:
            for n in news_items[:10]:
                st.write(f"- {n.get('title')} ({n.get('published_at')})")
        else:
            st.info("No se encontraron noticias.")
