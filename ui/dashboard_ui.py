# ======================================================
# AppFinanzAr — Dashboard FINAL (Auth Safe / Demo → Real)
# ======================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, time

# ======================================================
# 🔐 AUTH GUARD — NO LOGIN, NO DASHBOARD
# ======================================================
if "username" not in st.session_state:
    st.error("Sesión inválida. Ingresá desde el login.")
    st.stop()

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
# DEMO DATA
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

PRICE_ALERTS = {
    "MSFT.US": "Precio excesivamente alto",
    "GGAL.BA": "Precio muy bajo"
}

SMART_ALERTS = {
    "BTC.CRYPTO": {"pump": True, "volatility": 18},
    "ETH.CRYPTO": {"volatility": 9}
}

ASSET_FLAGS = {
    "BTC.CRYPTO": ["Alta volatilidad", "Demo data"],
    "GGAL.BA": ["Mercado local", "Demo data"]
}

# ======================================================
# HELPERS
# ======================================================
def asset_type(t):
    if t.endswith(".CRYPTO"):
        return "Criptomoneda"
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
    days = max((end - start).days, 30)
    dates = pd.date_range(end=end, periods=days)
    price = 100 + np.cumsum(np.random.randn(days))
    df = pd.DataFrame({
        "date": dates,
        "open": price + np.random.randn(days),
        "close": price
    })
    df["high"] = df[["open","close"]].max(axis=1) + abs(np.random.randn(days))
    df["low"] = df[["open","close"]].min(axis=1) - abs(np.random.randn(days))
    df["SMA20"] = df["close"].rolling(20).mean()
    df["EMA20"] = df["close"].ewm(span=20).mean()
    return df

def risk_score(t):
    score = 20 if t.endswith(".CRYPTO") else 10
    a = SMART_ALERTS.get(t, {})
    if a.get("pump"): score += 30
    if a.get("volatility",0) > 15: score += 20
    return min(score,100)

def demo_overview(t):
    return {
        "fundamentals": {
            "Revenue": "1200M",
            "Profit": "260M",
            "Debt": "Low",
            "ROE": "18%"
        },
        "competitors": ["AAPL", "GOOGL", "AMZN"],
        "news": [
            {"title": "Strong growth outlook", "sentiment": 0.6},
            {"title": "Short term volatility expected", "sentiment": -0.3}
        ]
    }

def recommend_for_user(favs):
    safe = [f for f in favs if risk_score(f) < 60]
    return safe[0] if safe else (favs[0] if favs else None)

# ======================================================
# SESSION
# ======================================================
st.session_state.setdefault("favorites", [])
st.session_state.setdefault("selected_ticker", "")

# ======================================================
# SIDEBAR — SEARCH / FAVORITES
# ======================================================
with st.sidebar:
    st.subheader("🔍 Buscar activo")
    q = st.text_input("Empresa o ticker (min 2 letras)")

    matches = []
    if len(q) >= 2:
        for n,t in ALL_ASSETS.items():
            if q.lower() in n.lower() or q.lower() in t.lower():
                matches.append(f"{n} ({t})")

    if matches:
        sel = st.radio("Resultados", matches)
        if sel:
            st.session_state.selected_ticker = sel.split("(")[1][:-1]
            st.rerun()

    st.markdown("---")
    st.subheader("⭐ Favoritos")

    stocks = [f for f in st.session_state.favorites if not f.endswith(".CRYPTO")]
    cryptos = [f for f in st.session_state.favorites if f.endswith(".CRYPTO")]

    st.caption("Acciones")
    for f in stocks: st.write("•", f)

    st.caption("Criptomonedas")
    for f in cryptos: st.write("•", f)

    if st.session_state.favorites:
        csv = pd.DataFrame({"Ticker": st.session_state.favorites}).to_csv(index=False)
        st.download_button("⬇ Exportar CSV", csv, "favoritos.csv")

# ======================================================
# MAIN
# ======================================================
st.title("📊 AppFinanzAr")

# HOME
if not st.session_state.selected_ticker:
    st.subheader("Acciones demo")
    for n,t in STOCK_TICKERS.items():
        if st.button(f"{n} ({t})"):
            st.session_state.selected_ticker = t
            st.rerun()

    st.subheader("Criptomonedas demo")
    for n,t in CRYPTO_TICKERS.items():
        if st.button(f"{n} ({t})"):
            st.session_state.selected_ticker = t
            st.rerun()

    st.info("Seleccioná un activo para comenzar")
    st.stop()

ticker = st.session_state.selected_ticker

# ======================================================
# HEADER
# ======================================================
st.subheader(f"{ticker} — {asset_type(ticker)}")
st.caption(market_status(ticker))

# FLAGS
st.markdown("### 🚩 Flags")
for f in ASSET_FLAGS.get(ticker, ["Demo data"]):
    st.write("•", f)

# ALERTAS
if ticker in PRICE_ALERTS:
    st.warning(PRICE_ALERTS[ticker])

a = SMART_ALERTS.get(ticker, {})
if a.get("pump"): st.error("🔥 Pump detectado")
if a.get("volatility",0)>10: st.warning(f"🌪️ Volatilidad {a['volatility']}%")

# ======================================================
# TIMEFRAME
# ======================================================
c1,c2 = st.columns(2)
with c1:
    r = st.selectbox("Rango rápido", ["1M","3M","6M","1Y"])
with c2:
    d1 = st.date_input("Desde", datetime.today()-timedelta(days=180))
    d2 = st.date_input("Hasta", datetime.today())

days = {"1M":30,"3M":90,"6M":180,"1Y":365}[r]
df = demo_ohlc(datetime.today()-timedelta(days=days), datetime.today())

# ======================================================
# GRAPH
# ======================================================
fig = go.Figure()
fig.add_candlestick(x=df["date"], open=df["open"], high=df["high"],
                    low=df["low"], close=df["close"])
fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA20")
fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA20")
st.plotly_chart(fig, use_container_width=True)

if st.button("⭐ Agregar a favoritos"):
    if ticker not in st.session_state.favorites:
        st.session_state.favorites.append(ticker)
        st.rerun()

# ======================================================
# OVERVIEW
# ======================================================
ov = demo_overview(ticker)

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
    lab = "📈 Positivo" if n["sentiment"]>0 else "📉 Negativo"
    st.write(f"- {n['title']} — {lab}")

# ======================================================
# ETF FINDER
# ======================================================
st.subheader("🧭 ETF Finder")
tema = st.selectbox("Tema", ETF_THEMES)
if st.button("Buscar ETFs"):
    st.table(pd.DataFrame([
        {"ETF":"DEMO-ETF-1","Tema":tema},
        {"ETF":"DEMO-ETF-2","Tema":tema}
    ]))

# ======================================================
# COMPARACIÓN
# ======================================================
st.subheader("🔀 Comparación rápida")
a,b = st.columns(2)
t1 = a.selectbox("Activo A", list(ALL_ASSETS.values()))
t2 = b.selectbox("Activo B", list(ALL_ASSETS.values()))
if st.button("Comparar"):
    st.bar_chart({t1:np.random.rand()*100, t2:np.random.rand()*100})

# ======================================================
# RANKING
# ======================================================
st.subheader("🏆 Ranking personalizado")
if st.session_state.favorites:
    rows = [{"Ticker":f,"Score":np.random.uniform(40,90),"Riesgo":risk_score(f)}
            for f in st.session_state.favorites]
    st.table(pd.DataFrame(rows).sort_values("Score", ascending=False))
else:
    st.caption("Agregá favoritos")

# ======================================================
# RECOMENDADO
# ======================================================
st.subheader("🧠 Recomendado para vos")
rec = recommend_for_user(st.session_state.favorites)
if rec:
    st.success(f"Podría interesarte: {rec}")
else:
    st.caption("Sin datos suficientes")

st.caption("Modo DEMO — listo para EODHD + SQL")

