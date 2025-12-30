# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, time, date

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
def market_status(t):
    now = datetime.now().time()
    if t.endswith(".CRYPTO"):
        return "🟣 Cripto 24/7"
    if t.endswith(".BA"):
        return "🟢 BYMA abierto" if time(11, 0) <= now <= time(17, 0) else "🔴 BYMA cerrado"
    return "🟢 Wall Street abierto" if time(9, 30) <= now <= time(16, 0) else "🔴 Wall Street cerrado"


def demo_ohlc(start, end):
    days = max((end - start).days, 30)
    dates = pd.date_range(start=start, periods=days)
    price = 100 + np.cumsum(np.random.randn(days))
    df = pd.DataFrame({
        "date": dates,
        "open": price + np.random.randn(days),
        "close": price,
    })
    df["high"] = df[["open", "close"]].max(axis=1) + abs(np.random.randn(days))
    df["low"] = df[["open", "close"]].min(axis=1) - abs(np.random.randn(days))
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
            "Score Global": round(np.random.uniform(40, 90), 2)
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


# ======================================================
# STATE INIT
# ======================================================
def init_state():
    if "username" not in st.session_state:
        st.session_state.username = "demo_user"

    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = None

    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites(st.session_state.username)

    if "scores" not in st.session_state:
        st.session_state.scores = {}

    if "preferences" not in st.session_state:
        st.session_state.preferences = {
            "time_range": "3M",
            "max_risk": 100,
            "order_by": "Score"
        }

    if "confirm_delete_one" not in st.session_state:
        st.session_state.confirm_delete_one = None

    if "confirm_delete_all" not in st.session_state:
        st.session_state.confirm_delete_all = False


# ======================================================
# DASHBOARD
# ======================================================
def show_dashboard():
    init_state()
    st.title("📊 AppFinanzAr")

    # ================= SIDEBAR =================
    with st.sidebar:
        st.subheader("🕒 Estado del mercado")
        if st.session_state.selected_ticker:
            st.write(market_status(st.session_state.selected_ticker))
        else:
            st.caption("Seleccioná un activo")

        st.divider()

        # ---------- FAVORITOS ----------
        st.subheader("⭐ Favoritos")

        if st.session_state.favorites:
            for f in st.session_state.favorites:
                c1, c2 = st.columns([8, 1])
                if c1.button(f, key=f"sel_{f}"):
                    st.session_state.selected_ticker = f
                if c2.button("❌", key=f"del_{f}"):
                    st.session_state.confirm_delete_one = f
        else:
            st.caption("Sin favoritos")

        if st.session_state.confirm_delete_one:
            st.warning(f"¿Eliminar {st.session_state.confirm_delete_one}?")
            c1, c2 = st.columns(2)
            if c1.button("Sí"):
                persist_remove_favorite(
                    st.session_state.username,
                    st.session_state.confirm_delete_one
                )
                st.session_state.favorites.remove(
                    st.session_state.confirm_delete_one
                )
                st.session_state.confirm_delete_one = None
                st.rerun()
            if c2.button("Cancelar"):
                st.session_state.confirm_delete_one = None

        if st.button("🧹 Eliminar todos"):
            persist_clear_favorites(st.session_state.username)
            st.session_state.favorites = []
            st.session_state.selected_ticker = None
            st.rerun()

        st.divider()

        # ---------- BUSCAR EMPRESA ----------
        st.subheader("🔍 Buscar empresa")
        company = st.selectbox("Empresa", [""] + list(STOCK_TICKERS.keys()))
        if company:
            if st.button("Ver"):
                st.session_state.selected_ticker = STOCK_TICKERS[company]

        st.divider()

        # ---------- BUSCAR CRIPTO ----------
        st.subheader("🟣 Buscar cripto")
        crypto = st.selectbox("Cripto", [""] + list(CRYPTO_TICKERS.keys()))
        if crypto:
            if st.button("Ver cripto"):
                st.session_state.selected_ticker = CRYPTO_TICKERS[crypto]

    # ================= MAIN =================
    if not st.session_state.selected_ticker:
        st.info("👈 Seleccioná un activo")
        return

    ticker = st.session_state.selected_ticker

    # ---------- FLAGS ----------
    for f in ASSET_FLAGS.get(ticker, []):
        st.warning(f)

    # ---------- RANGO TEMPORAL ----------
    st.subheader("📅 Rango temporal")
    today = date.today()

    if "start_date" not in st.session_state:
        st.session_state.start_date = today - timedelta(days=90)
    if "end_date" not in st.session_state:
        st.session_state.end_date = today

    ranges = {
        "1M": 30, "3M": 90, "6M": 180, "1Y": 365
    }

    cols = st.columns(len(ranges) + 1)
    for i, (label, days) in enumerate(ranges.items()):
        if cols[i].button(label):
            st.session_state.start_date = today - timedelta(days=days)
            st.session_state.end_date = today

    if cols[-1].button("📅"):
        c1, c2 = st.columns(2)
        st.session_state.start_date = c1.date_input(
            "Desde", st.session_state.start_date
        )
        st.session_state.end_date = c2.date_input(
            "Hasta", st.session_state.end_date
        )

    df = demo_ohlc(st.session_state.start_date, st.session_state.end_date)

    fig = go.Figure()
    fig.add_candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )
    fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA 20")
    fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA 20")
    st.plotly_chart(fig, use_container_width=True)

    # ---------- FAVORITO ----------
    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            persist_add_favorite(st.session_state.username, ticker)
            st.session_state.favorites.append(ticker)

        if ticker not in st.session_state.scores:
            st.session_state.scores[ticker] = round(
                np.random.uniform(40, 90), 2
            )

    # ---------- OVERVIEW ----------
    ov = demo_overview(ticker)
    st.subheader("📋 Resumen ejecutivo")
    st.json(ov["executive"])

    st.subheader("📰 Noticias & Sentimiento")
    for n in ov["news"]:
        s = n["sentiment"]
        if s > 0.2:
            st.success(n["title"])
        elif s < -0.2:
            st.error(n["title"])
        else:
            st.info(n["title"])

    # ================= RANKING =================
    st.subheader("🏆 Ranking personalizado")

    if st.session_state.favorites:
        rows = []
        for f in st.session_state.favorites:
            if f not in st.session_state.scores:
                st.session_state.scores[f] = round(
                    np.random.uniform(40, 90), 2
                )
            rows.append({
                "Ticker": f,
                "Riesgo": risk_score(f),
                "Score": st.session_state.scores[f]
            })

        df_rank = pd.DataFrame(rows)
        df_rank["Balance"] = df_rank["Score"] - df_rank["Riesgo"] * 0.5
        df_rank = df_rank.sort_values("Balance", ascending=False)

        edited = st.data_editor(
            df_rank,
            hide_index=True,
            disabled=True,
            key="ranking_editor"
        )

        sel = st.session_state.get("ranking_editor", {}).get("selected_rows")
        if sel:
            st.session_state.selected_ticker = df_rank.iloc[sel[0]]["Ticker"]
            st.rerun()

        # ---------- COMPARACIÓN ----------
        st.subheader("🔀 Comparación rápida")
        tickers = df_rank["Ticker"].tolist()
        t1, t2 = st.selectbox("A", tickers), st.selectbox("B", tickers, index=1)
        if st.button("Comparar"):
            st.bar_chart({
                t1: st.session_state.scores[t1],
                t2: st.session_state.scores[t2]
            })

        # ---------- RECOMENDADO ----------
        best = df_rank.iloc[0]["Ticker"]
        st.subheader("🧠 Recomendado para vos")
        if st.button(f"👉 Ver {best}"):
            st.session_state.selected_ticker = best
            st.rerun()

    else:
        st.caption("Agregá favoritos para ver ranking")

    st.caption("Modo DEMO — arquitectura lista para datos reales")


    
