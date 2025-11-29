# app.py
import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# local import (login.py must exist)
from login import login_screen

# -------------------------
# Page config & style
# -------------------------
st.set_page_config(page_title="FinanzApp PRO", layout="wide", initial_sidebar_state="expanded")
# Dark theme tweaks (some inline CSS)
st.markdown(
    """
    <style>
    .reportview-container { background: #0e1117; color: #dbe6ff; }
    .sidebar .sidebar-content { background: #0b0f14; color: #dbe6ff; }
    .stButton>button { background: #1f2937; color: #fff; border: none; }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# Authentication
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# -------------------------
# Globals
# -------------------------
API_KEY = st.secrets.get("EODHD_API_KEY", None)
if not API_KEY:
    st.error("EODHD_API_KEY no encontrado en secrets. Agregalo en Settings → Secrets.")
    st.stop()

# Simple favorites stored in session (note: not persistent across redeploys)
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

# -------------------------
# Utilities & caching
# -------------------------
@st.cache_data(ttl=300)
def fetch_eod_ohlc(ticker: str, from_date: str = None, to_date: str = None):
    """Fetch daily OHLC data from EODHD (adjust endpoint if needed)."""
    try:
        # using EODHD 'eod' endpoint (example). Adjust parameters to your plan.
        url = f"https://eodhd.com/api/eod/{ticker}?api_token={API_KEY}&fmt=json"
        if from_date and to_date:
            url += f"&from={from_date}&to={to_date}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        df = pd.DataFrame(data)
        # Normalize expected columns
        for col in ["date", "open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = np.nan
        df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error al consultar EODHD: {e}")
        return None

def sma(series: pd.Series, window: int):
    return series.rolling(window=window).mean()

def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi

@st.cache_data(ttl=300)
def fetch_realtime(ticker: str):
    """Fetch a small real-time snapshot from EODHD (if available)."""
    try:
        url = f"https://eodhd.com/api/real-time/{ticker}?api_token={API_KEY}&fmt=json"
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_news(ticker: str, from_date: str = None):
    """Simplified news fetch. EODHD has news endpoints in some plans. This uses a placeholder approach."""
    # If your EODHD plan supports news endpoint, replace this accordingly.
    # As fallback, return empty list to avoid crashes.
    return []

# -------------------------
# UI Layout
# -------------------------
sidebar = st.sidebar
sidebar.title("FinanzApp PRO")
sidebar.write(f"Usuario: **{st.session_state.get('username')}**")
sidebar.markdown("---")

# Search / Inputs
symbol = sidebar.text_input("Buscar ticker (ej: AAPL, TSLA)", value="AAPL")
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

sidebar.markdown("---")
if sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.experimental_rerun()

# Add to favorites
if sidebar.button("Agregar a Favoritos"):
    if symbol and symbol not in st.session_state["favorites"]:
        st.session_state["favorites"].append(symbol.upper())
        st.success(f"{symbol.upper()} agregado a Favoritos")

# Favorites list
sidebar.write("### Favoritos")
for f in st.session_state["favorites"]:
    sidebar.write(f"- {f}")

sidebar.markdown("---")
sidebar.write("Advanced")
sma_short = sidebar.number_input("SMA corto (días)", value=20, min_value=1)
sma_long = sidebar.number_input("SMA largo (días)", value=50, min_value=1)
ema_span = sidebar.number_input("EMA (días)", value=20, min_value=1)
rsi_period = sidebar.number_input("RSI periodo", value=14, min_value=1)

# -------------------------
# Main area - Header
# -------------------------
st.title("📈 FinanzApp PRO — Dashboard")
st.markdown(f"**Ticker:** {symbol.upper()}  •  **Rango:** {start_date} → {end_date}")

# -------------------------
# Data fetch
# -------------------------
from_str = start_date.strftime("%Y-%m-%d")
to_str = end_date.strftime("%Y-%m-%d")

with st.spinner("Consultando datos..."):
    df = fetch_eod_ohlc(symbol, from_date=from_str, to_date=to_str)
    realtime = fetch_realtime(symbol)

if df is None or df.empty:
    st.error("No se encontraron datos históricos para este ticker.")
else:
    # Technical overlays
    df["SMA_short"] = sma(df["close"], sma_short)
    df["SMA_long"] = sma(df["close"], sma_long)
    df["EMA"] = ema(df["close"], ema_span)
    df["RSI"] = rsi(df["close"], period=rsi_period)

    # Candlestick
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Candles"
    )])

    # Overlays
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_short"], mode="lines", name=f"SMA {sma_short}", line=dict(width=1.5)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA_long"], mode="lines", name=f"SMA {sma_long}", line=dict(width=1.5)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["EMA"], mode="lines", name=f"EMA {ema_span}", line=dict(width=1)))

    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)

    # RSI panel
    st.subheader("RSI")
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df["date"], y=df["RSI"], name="RSI"))
    rsi_fig.update_layout(template="plotly_dark", height=200)
    st.plotly_chart(rsi_fig, use_container_width=True)

    # Executive summary (basic)
    st.subheader("Executive summary")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Último cierre:")
        st.metric("Precio", f"{df['close'].iloc[-1]:.2f}")
        st.write(f"Volumen (último): {int(df['volume'].dropna().iloc[-1]) if 'volume' in df and not df['volume'].dropna().empty else 'N/A'}")
    with col2:
        if realtime and isinstance(realtime, dict):
            st.write("Real-time snapshot")
            st.json(realtime)
        else:
            st.info("Sin snapshot real-time (depende del plan de EODHD)")

    # Fundamentals and competitors (basic)
    st.subheader("Fundamentales clave y competidores")
    competitors_input = st.text_input("Competidores (coma-separados, ej: MSFT,GOOG)", value="")
    comps = [c.strip().upper() for c in competitors_input.split(",") if c.strip()] if competitors_input else []
    fundamentals = {}
    if comps:
        for c in comps:
            # Placeholder: try to fetch a quick profile (adjust to EODHD endpoint if available)
            # Try 'fundamentals' or fallback to realtime
            try:
                url = f"https://eodhd.com/api/fundamentals/{c}?api_token={API_KEY}&fmt=json"
                r = requests.get(url, timeout=8)
                if r.status_code == 200:
                    fundamentals[c] = r.json()
                else:
                    fundamentals[c] = {"error": f"status {r.status_code}"}
            except Exception as e:
                fundamentals[c] = {"error": str(e)}

        st.write("Competidores (resumen):")
        for k, v in fundamentals.items():
            st.write(f"**{k}** — {('Error: ' + str(v)) if isinstance(v, dict) and 'error' in v else 'Datos obtenidos'}")
            if isinstance(v, dict):
                st.json(v)

    # News (placeholder)
    st.subheader("Noticias")
    news_items = fetch_news(symbol, from_date=from_str)
    if news_items:
        for n in news_items:
            st.write(f"- {n.get('title')} ({n.get('date')})")
    else:
        st.info("No hay noticias (o tu plan no incluye endpoint de noticias).")

# -------------------------
# Footer helpers
# -------------------------
st.markdown("---")
st.caption("FinanzApp PRO — demo | Datos provistos por EODHD")

