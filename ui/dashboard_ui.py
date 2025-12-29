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
    st.title("📊 AppFinanzAr")

    # ================= SESSION SAFE =================
    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = None

    if "favorites" not in st.session_state:
        st.session_state.favorites = []

        # ================= SIDEBAR DERECHA =================
    with st.sidebar:
        st.subheader("🕒 Estado del mercado")
        ticker = st.session_state.get("selected_ticker", "")
        st.write(market_status_by_asset(ticker))

        st.markdown("---")
        st.subheader("⭐ Favoritos")

        if st.session_state.favorites:

            # ---- AGRUPAR FAVORITOS POR TIPO ----
            stocks = []
            cryptos = []

            for f in st.session_state.favorites:
                if asset_type(f) == "crypto":
                    cryptos.append(f)
                else:
                    stocks.append(f)

            # ---- ACCIONES ----
            if stocks:
                st.markdown("📈 **Acciones**")
                for f in stocks:
                    c1, c2 = st.columns([6,1])
                    with c1:
                        st.write(f"• {f}")
                    with c2:
                        if st.button("❌", key=f"del_{f}"):
                            st.session_state.confirm_delete_one = f
                            st.session_state.confirm_delete_all = False

            # ---- CRIPTO ----
            if cryptos:
                st.markdown("🟣 **Cripto**")
                for f in cryptos:
                    c1, c2 = st.columns([6,1])
                    with c1:
                        st.write(f"• {f}")
                    with c2:
                        if st.button("❌", key=f"del_{f}"):
                            st.session_state.confirm_delete_one = f
                            st.session_state.confirm_delete_all = False

            st.divider()

            # ---- ELIMINAR TODOS ----
            if st.button("🧹 Eliminar todos"):
                st.session_state.confirm_delete_all = True
                st.session_state.confirm_delete_one = None
        

            # ---- CONFIRMAR ELIMINAR UNO ----
            if st.session_state.confirm_delete_one:
                st.warning(
                    f"¿Eliminar {st.session_state.confirm_delete_one} de favoritos?"
                )

                c_yes, c_no = st.columns(2)

                if c_yes.button("✅ Sí, eliminar"):
                    user = st.session_state.get("username")
                    ticker = st.session_state.confirm_delete_one

                    persist_remove_favorite(user, ticker)
                    st.session_state.favorites.remove(ticker)

                    st.session_state.confirm_delete_one = None
        

                if c_no.button("↩ Cancelar"):
                    st.session_state.confirm_delete_one = None
        

            # ---- CONFIRMAR ELIMINAR TODOS ----
            if st.session_state.confirm_delete_all:
                st.error("⚠️ ¿Eliminar TODOS los favoritos?")

                c_yes, c_no = st.columns(2)

                if c_yes.button("🔥 Sí, eliminar todo"):
                    user = st.session_state.get("username")
                    persist_clear_favorites(user)
                    st.session_state.favorites = []
                    st.session_state.confirm_delete_all = False
            

                if c_no.button("↩ Cancelar"):
                    st.session_state.confirm_delete_all = False
        

            st.divider()

            # ---- EXPORT CSV ----
            csv = pd.DataFrame(
                st.session_state.favorites,
                columns=["Ticker"]
            ).to_csv(index=False)

            st.download_button(
                "⬇ Exportar favoritos",
                csv,
                "favoritos.csv"
            )

        else:
            st.caption("Sin favoritos aún")
        
        st.markdown("---")
        st.subheader("📈 Acciones")

        company_query = st.text_input(
            "🏢 Buscar empresa",
            placeholder="Ej: Microsoft, Apple"
        )

        matches = [
            name for name in STOCK_TICKERS
            if company_query.lower() in name.lower()
        ]

        company = st.selectbox("Resultados", [""] + matches)

        if len(matches) == 1:
            ticker_found = STOCK_TICKERS[matches[0]]
            st.success(f"Ticker encontrado: {ticker_found}")
            st.session_state.selected_ticker = ticker_found

        elif len(matches) > 1:    
            st.info("Coincidencias encontradas:")    
            company_selected = st.selectbox("Seleccioná una", matches)

            ticker_found = STOCK_TICKERS[company_selected]
            st.session_state.selected_ticker = ticker_found

        else:
            st.warning("Empresa no encontrada (solo tickers demo disponibles)")

        st.subheader("🟣 Criptomonedas")

        crypto_query = st.text_input(
            "Buscar cripto (nombre o símbolo)",
            placeholder="Ej: bitcoin, btc, eth"
        )

        matches = [
            name for name, t in CRYPTO_TICKERS.items()
            if crypto_query.lower() in name.lower()
            or crypto_query.lower() in t.lower()
        ]

        crypto = st.selectbox("Resultados", [""] + matches)

        if crypto:
            st.session_state.selected_ticker = CRYPTO_TICKERS[crypto]
      

    # ================= SELECCIÓN CENTRAL =================
    st.subheader("Selección de activo")

    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = ""

    stocks = [t for t in DEMO_TICKERS if not t.endswith(".CRYPTO")]
    cryptos = [t for t in DEMO_TICKERS if t.endswith(".CRYPTO")]

    SELECTABLE_TICKERS = (
        [""] +
        [f"📈 {v}" for v in STOCK_TICKERS.values()] +
        ["— CRIPTOMONEDAS —"] +
        [f"🟣 {v}" for v in CRYPTO_TICKERS.values()]
    )

    ticker_label = st.selectbox(
        "Elegí un ticker para comenzar",
        SELECTABLE_TICKERS,
        index=SELECTABLE_TICKERS.index(st.session_state.selected_ticker)
        if st.session_state.get("selected_ticker") in SELECTABLE_TICKERS else 0
    )

    if ticker_label in ("", "--- CRIPTOMONEDAS ---"):
        st.info("👆 Seleccioná un activo para ver el dashboard")
        return

    ticker = (
        ticker_label
        .replace("📈 ", "")
        .replace("🟣 ", "")
    )

    st.session_state.selected_ticker = ticker

    # ================= FLAGS =================
    flags = ASSET_FLAGS.get(ticker, [])
    if flags:
        st.markdown("### 🚩 Flags")
        for f in flags:
            st.warning(f)

    # ================= TIMEFRAME (SUTIL) =================
    tf_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}

    c1, c2 = st.columns([2, 1])
    with c1:
        tf = st.radio(
            "Rango",
            tf_map.keys(),
            horizontal=True,
            label_visibility="collapsed"
        )

    with c2:
        with st.expander("Desde / Hasta"):
            start = st.date_input(
                "Desde",
                datetime.today() - timedelta(days=tf_map[tf])
            )
            end = st.date_input("Hasta", datetime.today())

    # ================= DATA SAFE =================
    if end <= start:
        st.error("El rango de fechas no es válido")
        return

    df = demo_ohlc(start, end)

    # ================= GRAPH =================
    fig = go.Figure()
    fig.add_candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Precio"
    )
    fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA 20")
    fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA 20")

    st.plotly_chart(fig, use_container_width=True)

    # ================= ALERTAS =================
    if ticker in PRICE_ALERTS:
        msg, _ = PRICE_ALERTS[ticker]
        st.warning(msg)

    smart = SMART_ALERTS.get(ticker, {})
    if smart:
        st.markdown("### 🧠 Alertas inteligentes")
        if smart.get("pump"):
            st.error("🔥 Pump detectado")
        if smart.get("rapid_move"):
            st.warning("⏱️ Movimiento brusco")
        if smart.get("volatility", 0) > 10:
            st.warning(f"🌪️ Volatilidad {smart['volatility']}%")

    # ================= RIESGO =================
    st.metric("⚠️ Riesgo", f"{risk_score(ticker)}/100")

    # ================= FAVORITOS =================
    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            persist_add_favorite(user, ticker)
            st.session_state.favorites.append(ticker)

    # ================= OVERVIEW =================
    ov = demo_overview(ticker)

    st.subheader("📋 Resumen ejecutivo")
    st.json(ov["executive"])

    st.subheader("📊 Fundamentales")
    st.table(pd.DataFrame.from_dict(
        ov["fundamentals"], orient="index", columns=["Valor"]
    ))
    
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
        
    # ================= RECOMENDADO =================
    st.subheader("🧠 Recomendado para vos")
    rec = recommend_for_user(st.session_state.favorites)
    if rec:
        st.success(f"Podría interesarte: {rec}")
    else:
        st.caption("Agregá favoritos para recomendaciones")

    st.caption("Modo DEMO — arquitectura lista para producción")




    
