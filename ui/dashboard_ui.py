# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, time

from core.favorites import (
    load_favorites,
    add_favorite as persist_add_favorite,
    remove_favorite as persist_remove_favorite,
    clear_favorites as persist_clear_favorites
)

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

ETF_THEMES = [
    "Technology", "Energy", "Healthcare",
    "Artificial Intelligence", "Fintech", "Space"
]

PRICE_ALERTS = {
    "MSFT.US": ("Precio excesivamente alto", "#00ff99"),
    "GGAL.BA": ("Precio muy bajo", "#ff4d4d")
}

SMART_ALERTS = {
    "BTC.CRYPTO": {"pump": True, "volatility": 18, "rapid_move": True},
    "ETH.CRYPTO": {"volatility": 9},
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
    days = max((end - start).days, 30)
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
    if alerts.get("volatility",0) > 15:
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
# DASHBOARD
# ======================================================
def show_dashboard():
    st.title("📊 AppFinanzAr — Dashboard")

    user = st.session_state.get("username")

    # -------- session --------
    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites(user)["all"]

    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = ""

    # ==================================================
    # SIDEBAR
    # ==================================================
    with st.sidebar:
        st.subheader("🔍 Acciones")

        q_stock = st.text_input("Buscar empresa o ticker")
        stock_matches = [
            f"{n} ({t})"
            for n,t in STOCK_TICKERS.items()
            if q_stock.lower() in n.lower() or q_stock.lower() in t.lower()
        ]

        sel_stock = st.selectbox("Resultados acciones", [""] + stock_matches)
        if sel_stock:
            st.session_state.selected_ticker = sel_stock.split("(")[1].replace(")","")

        st.divider()
        st.subheader("🟣 Criptomonedas")

        q_crypto = st.text_input("Buscar cripto o ticker")
        crypto_matches = [
            f"{n} ({t})"
            for n,t in CRYPTO_TICKERS.items()
            if q_crypto.lower() in n.lower() or q_crypto.lower() in t.lower()
        ]

        sel_crypto = st.selectbox("Resultados cripto", [""] + crypto_matches)
        if sel_crypto:
            st.session_state.selected_ticker = sel_crypto.split("(")[1].replace(")","")

        st.divider()
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

    # ==================================================
    # MAIN
    # ==================================================
    if not st.session_state.selected_ticker:
        st.info("Seleccioná una acción o cripto desde el sidebar")
        return

    ticker = st.session_state.selected_ticker

    st.subheader(f"{ticker} — {asset_type(ticker)}")
    st.caption(market_status(ticker))

    # FLAGS
    st.markdown("### 🚩 Flags")
    for f in ASSET_FLAGS.get(ticker, []):
        st.write(f)

    # ALERTAS
    if ticker in PRICE_ALERTS:
        st.warning(PRICE_ALERTS[ticker][0])

    alerts = SMART_ALERTS.get(ticker, {})
    if alerts.get("pump"):
        st.error("🔥 Pump detectado")
    if alerts.get("rapid_move"):
        st.warning("⏱️ Movimiento brusco")
    if alerts.get("volatility",0)>10:
        st.warning(f"🌪️ Volatilidad {alerts['volatility']}%")

    # TIMEFRAME
    c1,c2 = st.columns(2)
    with c1:
        tf = st.selectbox("Rango rápido", ["1M","3M","6M","1Y"])
    with c2:
        start = st.date_input("Desde", datetime.today()-timedelta(days=180))
        end = st.date_input("Hasta", datetime.today())

    days = {"1M":30,"3M":90,"6M":180,"1Y":365}[tf]
    start = datetime.today()-timedelta(days=days)
    df = demo_ohlc(start, end)

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

    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            persist_add_favorite(user, ticker)
            st.session_state.favorites.append(ticker)

    # OVERVIEW
    ov = demo_overview(ticker)
    st.subheader("📋 Resumen Ejecutivo")
    st.json(ov["executive"])

    st.subheader("📊 Fundamentales")
    st.table(pd.DataFrame.from_dict(ov["fundamentals"], orient="index", columns=["Valor"]))

    st.subheader("🏭 Competidores")
    st.write(", ".join(ov["competitors"]))

    st.metric("⚠️ Riesgo", f"{risk_score(ticker)}/100")

    # NOTICIAS
    st.subheader("📰 Noticias & Sentimiento")
    for n in ov["news"]:
        st.write(f"- {n['title']}")

    # ETF
    st.subheader("🧭 ETF Finder")
    tema = st.selectbox("Tema", ETF_THEMES)
    if st.button("Buscar ETFs"):
        st.table(pd.DataFrame([
            {"ETF":"DEMO-ETF-1","Tema":tema},
            {"ETF":"DEMO-ETF-2","Tema":tema}
        ]))

    # COMPARACIÓN
    st.subheader("🔀 Comparación rápida")
    c1,c2 = st.columns(2)
    t1 = c1.selectbox("Ticker A", list(STOCK_TICKERS.values())+list(CRYPTO_TICKERS.values()))
    t2 = c2.selectbox("Ticker B", list(STOCK_TICKERS.values())+list(CRYPTO_TICKERS.values()))

    if st.button("Comparar"):
        st.bar_chart({
            t1: np.random.uniform(40,80),
            t2: np.random.uniform(40,80)
        })

    # RANKING
    st.subheader("🏆 Ranking personalizado")
    rows = [{
        "Ticker": f,
        "Riesgo": risk_score(f),
        "Score": np.random.uniform(40,90)
    } for f in st.session_state.favorites]

    if rows:
        st.table(pd.DataFrame(rows).sort_values("Score", ascending=False))

    # RECOMENDADO
    st.subheader("🧠 Recomendado para vos")
    rec = recommend_for_user(st.session_state.favorites)
    if rec:
        st.success(f"Podría interesarte: {rec}")

