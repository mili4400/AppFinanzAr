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
# CONFIG GLOBAL
# ======================================================
st.set_page_config(
    page_title="AppFinanzAr",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    body { background-color: #0e1117; color: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# CONSTANTES DEMO
# ======================================================
DEMO_TICKERS = ["MSFT.US", "AAPL.US", "GOOGL.US", "AMZN.US", "GGAL.BA", "BTC.CRYPTO",
    "ETH.CRYPTO"]

STOCK_TICKERS = {
    "Microsoft": "MSFT.US",
    "Apple": "AAPL.US",
    "Google": "GOOGL.US",
    "Amazon": "AMZN.US",
    "Galicia": "GGAL.BA"
}

CRYPTO_TICKERS = {
    "Bitcoin": "BTC.CRYPTO",
    "Ethereum": "ETH.CRYPTO"
}

ETF_THEMES = [
    "Technology", "Energy", "Healthcare", "Lithium",
    "Artificial Intelligence", "Fintech", "Space / NASA"
]

PRICE_ALERTS = {
    "MSFT.US": ("Precio excesivamente alto", "#00ff99"),
    "GGAL.BA": ("Precio muy bajo", "#ff4d4d")
}

SMART_ALERTS = {
    "BTC.CRYPTO": {
        "volatility": 18.4,
        "pump": True,
        "dormant": False,
        "rapid_move": True
    },
    "ETH.CRYPTO": {
        "volatility": 6.1,
        "pump": False,
        "dormant": False
    },
    "MSFT.US": {
        "price": "high"
    }
}

ASSET_FLAGS = {
    "BTC.CRYPTO": [],
    "ETH.CRYPTO": [],
    "DOGE.CRYPTO": ["suspicious"],
}

AUTOCOMPLETE_ASSETS = {
    # Acciones
    "Microsoft": "MSFT.US",
    "Apple": "AAPL.US",
    "Google": "GOOGL.US",
    "Amazon": "AMZN.US",
    "Galicia": "GGAL.BA",

    # Criptos
    "Bitcoin": "BTC.CRYPTO",
    "Ethereum": "ETH.CRYPTO"
}


# ======================================================
# HELPERS DEMO
# ======================================================
def market_status_by_asset(ticker: str):
    now = datetime.now().time()
    asset = asset_type(ticker)

    if asset == "crypto":
        return "🟣 Cripto 24/7 — mercado abierto"

    if asset == "stock argentina":
        if time(11, 0) <= now <= time(17, 0):
            return "🟢 BYMA abierto (AR)"
        return "🔴 BYMA cerrado (AR)"

    if asset == "stock us":
        if time(9, 30) <= now <= time(16, 0):
            return "🟢 Wall Street abierto (US)"
        if now < time(9, 30):
            return "🟡 Pre-market (US)"
        return "🔴 Wall Street cerrado (US)"

    return "⚪ Estado desconocido"

def demo_ohlc(days=180):
    dates = pd.date_range(end=datetime.today(), periods=days)
    price = 100 + np.cumsum(np.random.randn(days))
    return pd.DataFrame({
        "date": dates,
        "open": price - 1,
        "high": price + 1,
        "low": price - 2,
        "close": price
    })

def sma(s, n): return s.rolling(n).mean()
def ema(s, n): return s.ewm(span=n).mean()

def sentiment_score(text):
    return np.random.uniform(-1, 1)

def global_score(trend, sentiment):
    return round(trend * 0.6 + sentiment * 40, 2)

def demo_overview(ticker):
    trend = np.random.uniform(-6, 6)
    sentiment = np.random.uniform(-1, 1)
    return {
        "executive": {
            "name": ticker,
            "sector": "Technology",
            "industry": "Software",
            "country": "USA",
            "trend": trend,
            "score": global_score(trend, sentiment)
        },
        "fundamentals": {
            "Revenue": "1200M",
            "Profit": "260M",
            "Debt": "Low",
            "ROE": "18%"
        },
        "competitors": ["AAPL", "GOOGL", "AMZN"],
        "news": [
            {"title": "Strong growth outlook expected", "sentiment": sentiment_score("")},
            {"title": "Analysts remain cautious short-term", "sentiment": sentiment_score("")}
        ]
    }

def asset_type(ticker: str):
    if not ticker:
        return "unknown"
    if ticker.endswith(".CRYPTO"):
        return "crypto"
    if ticker.endswith(".BA"):
        return "stock argentina"
    if ticker.endswith(".US"):
        return "stock us"
    return "unknown"

def risk_score(ticker):
    score = 0
    alerts = SMART_ALERTS.get(ticker, {})

    if ticker.endswith(".CRYPTO"):
        score += 35

    if alerts.get("pump"):
        score += 25

    if alerts.get("volatility", 0) > 12:
        score += 20

    if alerts.get("rapid_move"):
        score += 10

    if "suspicious" in ASSET_FLAGS.get(ticker, []):
        score += 20

    return min(score, 100)

def recommend_for_user(favorites):
    if not favorites:
        return None

    safe_assets = [
        f for f in favorites
        if risk_score(f) < 60
    ]

    return safe_assets[0] if safe_assets else favorites[0]

# ======================================================
# DASHBOARD
# ======================================================
def show_dashboard():
    st.title("📊 AppFinanzAr — Demo Profesional")

    # ====== GARANTÍAS ABSOLUTAS ======
    if "favorites" not in st.session_state:
        st.session_state.favorites = []

    if "active_user" not in st.session_state:
        st.session_state.active_user = None

    if "confirm_delete_one" not in st.session_state:
        st.session_state.confirm_delete_one = None

    if "confirm_delete_all" not in st.session_state:
        st.session_state.confirm_delete_all = False

    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = ""


    # ====== SESSION STATE CONTROL POR USUARIO ======
    current_user = st.session_state.get("username")

    if "active_user" not in st.session_state:
        st.session_state.active_user = None

    if st.session_state.active_user != current_user:
        fav_struct = load_favorites(current_user)
        st.session_state.favorites = fav_struct["all"]
        st.session_state.confirm_delete_one = None
        st.session_state.confirm_delete_all = False
        st.session_state.active_user = current_user

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

    # ================= ALERTAS =================
    st.subheader("🚨 Alertas")

    ticker = st.session_state.get("selected_ticker", "")

   # ----- ALERTAS CLÁSICAS ----- 
    if ticker and ticker in PRICE_ALERTS:
        msg, color = PRICE_ALERTS[ticker]
        status = asset_type(ticker)  # "crypto" | "stock" | etc

        if status == "crypto":
            st.markdown(
                f"""
                <div style="
                    padding:10px;
                    border-radius:8px;
                    background-color:{color};
                    color:#0e1117;
                    font-weight:bold;
                ">
                🟢 {msg} — alerta activa 24/7
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            market_status = market_status_by_asset(ticker)

            if "abierto" in market_status.lower():
                st.markdown(
                    f"""
                    <div style="
                        padding:10px;
                        border-radius:8px;
                        background-color:{color};
                        color:#0e1117;
                        font-weight:bold;
                    ">
                    ⚠️ {msg} — mercado abierto
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("⏸️ Alerta pausada — mercado cerrado")

    # ----- ALERTAS INTELIGENTES (NUEVAS) -----
    alerts = SMART_ALERTS.get(ticker, {})

    if alerts:
        st.markdown("**🧠 Alertas inteligentes**")

        if alerts.get("pump"):
            st.error("🔥 Pump inusual detectado")

        if alerts.get("rapid_move"):
            st.warning("⏱️ Movimiento brusco en corto plazo")

        if alerts.get("dormant"):
            st.info("🧊 Activo dormido — bajo volumen")

        if alerts.get("volatility", 0) > 10:
            st.warning(f"🌪️ Volatilidad elevada: {alerts['volatility']}%")

    # ================= SCORE DE RIESGO =================
    def risk_score(asset):
        score = 0

        if asset.endswith(".CRYPTO"):
            score += 40  # riesgo base cripto
        if ALERTS.get(asset, {}).get("pump"):
            score += 30
        if ALERTS.get(asset, {}).get("volatility", 0) > 15:
            score += 20

        return min(score, 100)    

    if ticker:
        risk = risk_score(ticker)

        st.metric(
            "⚠️ Score de riesgo",
            f"{risk}/100",
            help="Cuanto mayor, más riesgoso el activo"
        )
    if "suspicious" in ASSET_FLAGS.get(ticker, []):
        st.error("🚫 Activo marcado como sospechoso (riesgo elevado)")
    
    # ================= FAVORITOS =================
    def add_favorite():
        if ticker and ticker not in st.session_state.favorites:
            user = st.session_state.get("username")
            persist_add_favorite(user, ticker)
            st.session_state.favorites.append(ticker)
        

    st.button(
        "⭐ Agregar a favoritos",
        on_click=add_favorite,
        key="add_fav_btn"
    )

    # ================= DATOS & GRÁFICO =================
    df = demo_ohlc()
    df["SMA20"] = sma(df["close"], 20)
    df["EMA20"] = ema(df["close"], 20)

    fig = go.Figure()
    fig.add_candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Precio"
    )
    fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA20")
    fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA20")
    st.plotly_chart(fig, use_container_width=True)

    # ================= OVERVIEW =================
    ov = demo_overview(ticker)

    st.subheader("📋 Resumen Ejecutivo")
    st.metric("Score Global", ov["executive"]["score"])
    st.json(ov["executive"])

    st.subheader("📊 Fundamentales")
    st.table(pd.DataFrame.from_dict(ov["fundamentals"], orient="index", columns=["Valor"]))

    st.subheader("🏭 Competidores")
    st.write(", ".join(ov["competitors"]))

    st.subheader("🧠 Recomendado para vos")

    rec = recommend_for_user(st.session_state.favorites)

    if rec:
        st.success(f"Podría interesarte: {rec}")
    else:
        st.caption("Agregá favoritos para recibir recomendaciones")


    # ================= NOTICIAS =================
    st.subheader("📰 Noticias & Sentimiento")
    for n in ov["news"]:
        label = "📈 Positivo" if n["sentiment"] > 0 else "📉 Negativo"
        st.write(f"- {n['title']} — {label}")

    # ================= ETF FINDER =================
    st.subheader("🧭 ETF Finder")
    tema = st.selectbox("Tema", ETF_THEMES)
    if st.button("Buscar ETFs"):
        st.table(pd.DataFrame([
            {"ETF": "DEMO-ETF-1", "Tema": tema},
            {"ETF": "DEMO-ETF-2", "Tema": tema}
        ]))

    # ================= COMPARACIÓN =================
    st.subheader("🔀 Comparación rápida")
    c1, c2 = st.columns(2)
    t1 = c1.selectbox("Ticker A", DEMO_TICKERS, index=0)
    t2 = c2.selectbox("Ticker B", DEMO_TICKERS, index=1)

    if st.button("Comparar"):
        st.bar_chart({
            t1: np.random.uniform(40, 80),
            t2: np.random.uniform(40, 80)
        })

    # ================= RANKING =================
    st.subheader("🏆 Ranking personalizado")

    ranking = []

    for f in st.session_state.favorites:
        ranking.append({
            "Ticker": f,
            "Riesgo": risk_score(f),
            "Score": global_score(
                np.random.uniform(-3, 6),
                np.random.uniform(-1, 1)
            )
        })

    if ranking:
        df = pd.DataFrame(ranking)
        st.table(df.sort_values("Score", ascending=False))
    else:
        st.info("Agregá favoritos para generar tu ranking")

    st.caption("Modo DEMO 100% — datos simulados con fines demostrativos")
