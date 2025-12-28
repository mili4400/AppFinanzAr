# ======================================================
# AppFinanzAr — Dashboard Final (DEMO / READY FOR REAL)
# ======================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
import io

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="AppFinanzAr",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_MODE = "demo"  # demo | real (EODHD futuro)

# ======================================================
# DEMO ASSETS
# ======================================================
STOCK_TICKERS = {
    "Microsoft": "MSFT.US",
    "Apple": "AAPL.US",
    "Google": "GOOGL.US",
    "Amazon": "AMZN.US",
    "Galicia": "GGAL.BA"
}

CRYPTO_TICKERS = {
    "Bitcoin": "BTC.CRYPTO",
    "Ethereum": "ETH.CRYPTO",
    "Solana": "SOL.CRYPTO"
}

ALL_ASSETS = {**STOCK_TICKERS, **CRYPTO_TICKERS}

ETF_THEMES = [
    "Technology", "Energy", "Healthcare",
    "Artificial Intelligence", "Fintech", "Space"
]

# ======================================================
# DEMO ALERTS / FLAGS
# ======================================================
PRICE_ALERTS = {
    "MSFT.US": ("Precio excesivamente alto", "#00ff99"),
    "GGAL.BA": ("Precio muy bajo", "#ff4d4d")
}

SMART_ALERTS = {
    "BTC.CRYPTO": {
        "pump": True,
        "volatility": 18,
        "rapid_move": True,
        "dormant": False
    },
    "ETH.CRYPTO": {
        "volatility": 9,
        "dormant": False
    }
}

ASSET_FLAGS = {
    "BTC.CRYPTO": ["Alta volatilidad", "Demo data"],
    "GGAL.BA": ["Mercado local", "Demo data"],
}

# ======================================================
# HELPERS
# ======================================================
def asset_type(t):
    if t.endswith(".CRYPTO"):
        return "Cripto"
    if t.endswith(".BA"):
        return "Acción Argentina"
    return "Acción USA"

def market_status(t):
    now = datetime.now().time()
    if t.endswith(".CRYPTO"):
        return "🟣 Cripto 24/7"
    if t.endswith(".BA"):
        return "🟢 BYMA abierto" if time(11,0)<=now<=time(17,0) else "🔴 BYMA cerrado"
    return "🟢 Wall Street abierto" if time(9,30)<=now<=time(16,0) else "🔴 Wall Street cerrado"

def demo_ohlc(start, end):
    days = (end - start).days
    dates = pd.date_range(start=start, periods=days)
    price = 100 + np.cumsum(np.random.randn(days))
    df = pd.DataFrame({
        "date": dates,
        "open": price + np.random.randn(days),
        "close": price,
    })
    df["high"] = df[["open","close"]].max(axis=1) + abs(np.random.randn(days))
    df["low"] = df[["open","close"]].min(axis=1) - abs(np.random.randn(days))
    df["SMA20"] = df["close"].rolling(20).mean()
    df["EMA20"] = df["close"].ewm(span=20).mean()
    return df

def risk_score(t):
    score = 20 if t.endswith(".CRYPTO") else 10
    alerts = SMART_ALERTS.get(t, {})
    if alerts.get("pump"):
        score += 30
    if alerts.get("volatility", 0) > 15:
        score += 20
    return min(score, 100)

def demo_overview(t):
    return {
        "executive": {
            "Ticker": t,
            "Sector": "Technology",
            "Score Global": round(np.random.uniform(40,90),2)
        },
        "fundamentals": {
            "Revenue": "1200M",
            "Profit": "260M",
            "Debt": "Low",
            "ROE": "18%"
        },
        "competitors": ["AAPL", "GOOGL", "AMZN"],
        "news": [
            {"title": "Strong growth outlook", "sentiment": 0.7},
            {"title": "Analysts cautious short term", "sentiment": -0.3}
        ]
    }

def recommend_for_user(favs):
    if not favs:
        return None
    safe = [f for f in favs if risk_score(f) < 60]
    return safe[0] if safe else favs[0]

# ======================================================
# SESSION
# ======================================================
if "favorites" not in st.session_state:
    st.session_state.favorites = []

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = ""

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.subheader("🔍 Buscar activo")

    query = st.text_input("Empresa o ticker (2 letras)")
    matches = []

    if len(query) >= 2:
        for name, ticker in ALL_ASSETS.items():
            if query.lower() in name.lower() or query.lower() in ticker.lower():
                matches.append(f"{name} ({ticker})")

    sel = st.selectbox("Resultados", [""] + matches)

    if sel:
        st.session_state.selected_ticker = sel.split("(")[1].replace(")", "")

    st.markdown("---")
    st.subheader("🌍 Estado del mercado")

    if st.session_state.selected_ticker:
        st.write(market_status(st.session_state.selected_ticker))
    else:
        st.caption("Sin selección")

    st.markdown("---")
    st.subheader("⭐ Favoritos")

    stocks = [f for f in st.session_state.favorites if not f.endswith(".CRYPTO")]
    cryptos = [f for f in st.session_state.favorites if f.endswith(".CRYPTO")]

    st.caption("Acciones")
    for f in stocks:
        st.write("•", f)

    st.caption("Cripto")
    for f in cryptos:
        st.write("•", f)

    if st.session_state.favorites:
        csv = pd.DataFrame({"Ticker": st.session_state.favorites}).to_csv(index=False)
        st.download_button("⬇ Exportar CSV", csv, "favoritos.csv")

# ======================================================
# MAIN
# ======================================================
st.title("📊 AppFinanzAr — Dashboard Profesional")

# HOME
if not st.session_state.selected_ticker:
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Acciones demo")
        for n,t in STOCK_TICKERS.items():
            st.write(f"• {n} ({t})")
    with c2:
        st.subheader("Criptos demo")
        for n,t in CRYPTO_TICKERS.items():
            st.write(f"• {n} ({t})")
    st.info("Buscá o seleccioná un activo para comenzar")
    st.stop()

ticker = st.session_state.selected_ticker

# ======================================================
# HEADER
# ======================================================
st.subheader(f"{ticker} — {asset_type(ticker)}")
st.caption(market_status(ticker))

# FLAGS
st.markdown("### 🚩 Flags")
st.write("Demo data")
for f in ASSET_FLAGS.get(ticker, []):
    st.write(f)

# ALERTAS CLÁSICAS
if ticker in PRICE_ALERTS:
    msg, color = PRICE_ALERTS[ticker]
    st.warning(msg)

# ALERTAS INTELIGENTES
alerts = SMART_ALERTS.get(ticker, {})
if alerts.get("pump"):
    st.error("🔥 Pump detectado")
if alerts.get("rapid_move"):
    st.warning("⏱️ Movimiento brusco")
if alerts.get("dormant"):
    st.info("🧊 Activo dormido")
if alerts.get("volatility",0)>10:
    st.warning(f"🌪️ Volatilidad {alerts['volatility']}%")

# ======================================================
# TIMEFRAME
# ======================================================
c1,c2 = st.columns(2)
with c1:
    range_opt = st.selectbox("Rango rápido", ["1M","3M","6M","1Y"])
with c2:
    start = st.date_input("Desde", datetime.today()-timedelta(days=180))
    end = st.date_input("Hasta", datetime.today())

days_map = {"1M":30,"3M":90,"6M":180,"1Y":365}
if range_opt:
    start = datetime.today()-timedelta(days=days_map[range_opt])
    end = datetime.today()

df = demo_ohlc(start, end)

# ======================================================
# GRAPH
# ======================================================
fig = go.Figure()
fig.add_candlestick(
    x=df["date"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
)
fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA20")
fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA20")
st.plotly_chart(fig, use_container_width=True)

# FAVORITOS
if st.button("⭐ Agregar a favoritos"):
    if ticker not in st.session_state.favorites:
        st.session_state.favorites.append(ticker)

# ======================================================
# OVERVIEW
# ======================================================
ov = demo_overview(ticker)

st.subheader("📋 Resumen Ejecutivo")
st.json(ov["executive"])

st.subheader("📊 Fundamentales")
st.table(pd.DataFrame.from_dict(ov["fundamentals"], orient="index", columns=["Valor"]))

st.subheader("🏭 Competidores")
st.write(", ".join(ov["competitors"]))

st.metric("⚠️ Riesgo", f"{risk_score(ticker)}/100")

# ======================================================
# NOTICIAS
# ======================================================
st.subheader("📰 Noticias & Sentimiento")
for n in ov["news"]:
    label = "📈 Positivo" if n["sentiment"] > 0 else "📉 Negativo"
    st.write(f"- {n['title']} — {label}")

# ======================================================
# ETF FINDER
# ======================================================
st.subheader("🧭 ETF Finder")
tema = st.selectbox("Tema", ETF_THEMES)
if st.button("Buscar ETFs"):
    st.table(pd.DataFrame([
        {"ETF": "DEMO-ETF-1", "Tema": tema},
        {"ETF": "DEMO-ETF-2", "Tema": tema}
    ]))

# ======================================================
# COMPARACIÓN
# ======================================================
st.subheader("🔀 Comparación rápida")
c1,c2 = st.columns(2)
t1 = c1.selectbox("Ticker A", list(ALL_ASSETS.values()))
t2 = c2.selectbox("Ticker B", list(ALL_ASSETS.values()))

if st.button("Comparar"):
    st.bar_chart({
        t1: np.random.uniform(40,80),
        t2: np.random.uniform(40,80)
    })

# ======================================================
# RANKING
# ======================================================
st.subheader("🏆 Ranking personalizado")
rows = []
for f in st.session_state.favorites:
    rows.append({
        "Ticker": f,
        "Riesgo": risk_score(f),
        "Score": np.random.uniform(40,90)
    })

if rows:
    st.table(pd.DataFrame(rows).sort_values("Score", ascending=False))
else:
    st.caption("Agregá favoritos para generar ranking")

# ======================================================
# RECOMENDADO
# ======================================================
st.subheader("🧠 Recomendado para vos")
rec = recommend_for_user(st.session_state.favorites)
if rec:
    st.success(f"Podría interesarte: {rec}")
else:
    st.caption("Agregá favoritos para recibir recomendaciones")

st.caption("Modo DEMO — arquitectura lista para EODHD + SQL")
