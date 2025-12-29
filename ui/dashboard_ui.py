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

DEMO_TICKERS = list(STOCK_TICKERS.values()) + list(CRYPTO_TICKERS.values())

# ======================================================
# HELPERS
# ======================================================
def asset_type(t):
    if t.endswith(".CRYPTO"):
        return "crypto"
    if t.endswith(".BA"):
        return "arg_stock"
    return "us_stock"

def market_status(t):
    now = datetime.now().time()
    if t.endswith(".CRYPTO"):
        return "🟣 Cripto 24/7"
    if t.endswith(".BA"):
        return "🟢 BYMA abierto" if time(11,0) <= now <= time(17,0) else "🔴 BYMA cerrado"
    return "🟢 Wall Street abierto" if time(9,30) <= now <= time(16,0) else "🔴 Wall Street cerrado"

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
# DASHBOARD
# ======================================================
def show_dashboard():
    st.title("📊 AppFinanzAr")

    # ================= SESSION SAFE =================
    if "username" not in st.session_state:
        st.session_state.username = "demo_user"

    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = ""

    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites(st.session_state.username)

    if "confirm_delete_one" not in st.session_state:
        st.session_state.confirm_delete_one = None

    if "confirm_delete_all" not in st.session_state:
        st.session_state.confirm_delete_all = False

    user = st.session_state.username
    ticker = st.session_state.selected_ticker

    # ================= SIDEBAR =================
    with st.sidebar:
        st.subheader("🕒 Estado del mercado")
        if ticker:
            st.write(market_status(ticker))
        else:
            st.caption("Seleccioná un activo")

        st.divider()
        st.subheader("⭐ Favoritos")

        if st.session_state.favorites:
            stocks, cryptos = [], []

            for f in st.session_state.favorites:
                if asset_type(f) == "crypto":
                    cryptos.append(f)
                else:
                    stocks.append(f)

            if stocks:
                st.markdown("📈 **Acciones**")
                for f in stocks:
                    c1, c2 = st.columns([6,1])
                    c1.write(f"• {f}")
                    if c2.button("❌", key=f"del_{f}"):
                        st.session_state.confirm_delete_one = f
                        st.session_state.confirm_delete_all = False

            if cryptos:
                st.markdown("🟣 **Cripto**")
                for f in cryptos:
                    c1, c2 = st.columns([6,1])
                    c1.write(f"• {f}")
                    if c2.button("❌", key=f"del_{f}"):
                        st.session_state.confirm_delete_one = f
                        st.session_state.confirm_delete_all = False

            st.divider()

            if st.button("🧹 Eliminar todos"):
                st.session_state.confirm_delete_all = True
                st.session_state.confirm_delete_one = None

            if st.session_state.confirm_delete_one:
                st.warning(f"¿Eliminar {st.session_state.confirm_delete_one}?")
                c_yes, c_no = st.columns(2)

                if c_yes.button("✅ Sí"):
                    persist_remove_favorite(user, st.session_state.confirm_delete_one)
                    st.session_state.favorites.remove(st.session_state.confirm_delete_one)
                    st.session_state.confirm_delete_one = None

                if c_no.button("↩ Cancelar"):
                    st.session_state.confirm_delete_one = None

            if st.session_state.confirm_delete_all:
                st.error("⚠️ ¿Eliminar TODOS?")
                c_yes, c_no = st.columns(2)

                if c_yes.button("🔥 Sí"):
                    persist_clear_favorites(user)
                    st.session_state.favorites = []
                    st.session_state.confirm_delete_all = False

                if c_no.button("↩ Cancelar"):
                    st.session_state.confirm_delete_all = False

            st.divider()
            csv = pd.DataFrame(st.session_state.favorites, columns=["Ticker"]).to_csv(index=False)
            st.download_button("⬇ Exportar favoritos", csv, "favoritos.csv")

        else:
            st.caption("Sin favoritos aún")

        st.divider()
        st.subheader("🔍 Buscar activo")

        label_map = (
            [""] +
            [f"📈 {v}" for v in STOCK_TICKERS.values()] +
            ["— CRIPTOMONEDAS —"] +
            [f"🟣 {v}" for v in CRYPTO_TICKERS.values()]
        )

        current_label = (
            f"📈 {ticker}" if ticker.endswith((".US",".BA"))
            else f"🟣 {ticker}" if ticker else ""
        )

        selected = st.selectbox(
            "Ticker",
            label_map,
            index=label_map.index(current_label) if current_label in label_map else 0
        )

        if selected not in ("", "— CRIPTOMONEDAS —"):
            st.session_state.selected_ticker = selected.replace("📈 ","").replace("🟣 ","")

    # ================= MAIN =================
    if not st.session_state.selected_ticker:
        st.info("👈 Seleccioná un activo")
        return

    ticker = st.session_state.selected_ticker

    flags = ASSET_FLAGS.get(ticker, [])
    for f in flags:
        st.warning(f)

    tf_map = {"1M":30,"3M":90,"6M":180,"1Y":365}
    tf = st.radio("Rango", tf_map.keys(), horizontal=True)

    start = st.date_input("Desde", datetime.today()-timedelta(days=tf_map[tf]))
    end = st.date_input("Hasta", datetime.today())

    if end <= start:
        st.error("Rango inválido")
        return

    df = demo_ohlc(start, end)

    fig = go.Figure()
    fig.add_candlestick(x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"])
    fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA 20")
    fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA 20")
    st.plotly_chart(fig, use_container_width=True)

    if ticker in PRICE_ALERTS:
        st.warning(PRICE_ALERTS[ticker][0])

    smart = SMART_ALERTS.get(ticker, {})
    if smart:
        st.subheader("🧠 Alertas inteligentes")
        if smart.get("pump"):
            st.error("🔥 Pump detectado")
        if smart.get("rapid_move"):
            st.warning("⏱ Movimiento brusco")
        if smart.get("volatility",0) > 10:
            st.warning(f"🌪 Volatilidad {smart['volatility']}%")

    st.metric("⚠️ Riesgo", f"{risk_score(ticker)}/100")

    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            persist_add_favorite(user, ticker)
            st.session_state.favorites.append(ticker)

    ov = demo_overview(ticker)

    st.subheader("📋 Resumen ejecutivo")
    st.json(ov["executive"])

    st.subheader("📊 Fundamentales")
    st.table(pd.DataFrame.from_dict(ov["fundamentals"], orient="index", columns=["Valor"]))

    st.subheader("🏭 Competidores")
    st.write(", ".join(ov["competitors"]))

    st.subheader("📰 Noticias & Sentimiento")

    sentiments = []

    for n in ov["news"]:
        s = n.get("sentiment", 0)
        sentiments.append(s)

        if s > 0.2:
            st.success(f"🟢 {n['title']}  (sentimiento {s:+.2f})")
        elif s < -0.2:
            st.error(f"🔴 {n['title']}  (sentimiento {s:+.2f})")
        else:
            st.info(f"🟡 {n['title']}  (sentimiento {s:+.2f})")

    if sentiments:
        avg = sum(sentiments) / len(sentiments)
        st.metric("📊 Sentimiento promedio", f"{avg:+.2f}")


    # ================= ETF FINDER =================
    st.subheader("🧭 ETF Finder")

    tema = st.selectbox("Tema de inversión", ETF_THEMES)

    if st.button("Buscar ETFs"):
        st.table(pd.DataFrame([
            {"ETF": "DEMO-ETF-TECH", "Tema": tema},
            {"ETF": "DEMO-ETF-GLOBAL", "Tema": tema},
            {"ETF": "DEMO-ETF-GROWTH", "Tema": tema},
        ]))


    # ================= COMPARACIÓN RÁPIDA =================
    st.subheader("🔀 Comparación rápida")

    c1, c2 = st.columns(2)

    t1 = c1.selectbox(
        "Ticker A",
        DEMO_TICKERS,
        key="compare_a"
    )

    t2 = c2.selectbox(
        "Ticker B",
        DEMO_TICKERS,
        key="compare_b"
    )

    if st.button("Comparar"):
        st.bar_chart({
            t1: np.random.uniform(40, 90),
            t2: np.random.uniform(40, 90)
        })

    # ================= RANKING PERSONALIZADO =================
    st.subheader("🏆 Ranking personalizado")

    if st.session_state.favorites:
        rows = []

        for f in st.session_state.favorites:
            rows.append({
                "Ticker": f,
                "Riesgo": risk_score(f),
                "Score": round(np.random.uniform(40, 90), 2)
            })

        df_rank = (
            pd.DataFrame(rows)
            .sort_values("Score", ascending=False)
            .reset_index(drop=True)
        )

        st.table(df_rank)

    else:
        st.caption("Agregá activos a favoritos para ver tu ranking personalizado")

    
    # ================= RECOMENDADO =================
    st.subheader("🧠 Recomendado para vos")
    rec = recommend_for_user(st.session_state.favorites)
    if rec:
        st.success(f"Podría interesarte: {rec}")
    else:
        st.caption("Agregá favoritos para recomendaciones")

    st.caption("Modo DEMO — arquitectura lista para producción")



    
