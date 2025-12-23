# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, time

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
DEMO_TICKERS = ["MSFT.US", "AAPL.US", "GOOGL.US", "AMZN.US", "GGAL.BA"]

ETF_THEMES = [
    "Technology", "Energy", "Healthcare", "Lithium",
    "Artificial Intelligence", "Fintech", "Space / NASA"
]

PRICE_ALERTS = {
    "MSFT.US": ("Precio excesivamente alto", "#00ff99"),
    "GGAL.BA": ("Precio muy bajo", "#ff4d4d")
}

# ======================================================
# HELPERS DEMO
# ======================================================
def market_status():
    now = datetime.now().time()
    if time(9,30) <= now <= time(16,0):
        return "🟢 Mercado abierto"
    if now < time(9,30):
        return "🟡 Abre en menos de 1h"
    return "🔴 Mercado cerrado"

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

# ======================================================
# DASHBOARD
# ======================================================
def show_dashboard():
    st.title("📊 AppFinanzAr — Demo Profesional")

    if "favorites" not in st.session_state:
        st.session_state.favorites = []

    # ================= SIDEBAR DERECHA =================
    with st.sidebar:
        st.subheader("🕒 Estado del mercado")
        st.write(market_status())

        st.markdown("---")
        st.subheader("⭐ Favoritos")

        if st.session_state.favorites:
            remove_one = None

            for f in st.session_state.favorites:
                label, color = PRICE_ALERTS.get(f, ("", "#ffffff"))
                c1, c2 = st.columns([5,1])
                with c1:
                    st.markdown(
                        f"<span style='color:{color};font-weight:600'>• {f} {label}</span>",
                        unsafe_allow_html=True
                    )
                with c2:
                    if st.button("❌", key=f"del_{f}"):
                        remove_one = f

            if remove_one:
                if st.confirm(f"¿Eliminar {remove_one} de favoritos?"):
                    st.session_state.favorites.remove(remove_one)

            if st.confirm("🗑️ Eliminar TODOS los favoritos"):
                st.session_state.favorites = []

            csv = pd.DataFrame(st.session_state.favorites, columns=["Ticker"]).to_csv(index=False)
            st.download_button("⬇ Exportar CSV", csv, "favoritos.csv")
        else:
            st.caption("Sin favoritos aún")

        st.markdown("---")
        st.subheader("🏢 Buscar por empresa (demo)")
        st.caption("Ej: Microsoft, Apple, Google")
        st.write(DEMO_TICKERS)

    # ================= SELECCIÓN CENTRAL =================
    st.subheader("Selección de activo")

    ticker = st.selectbox(
        "Elegí un ticker para comenzar",
        [""] + DEMO_TICKERS,
        index=0
    )

    if ticker == "":
        st.info("👆 Seleccioná un activo para ver el dashboard")
        return

    # ================= FAVORITOS =================
    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            st.session_state.favorites.append(ticker)
            st.success("Agregado a favoritos")

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
    st.subheader("🏆 Ranking de oportunidades")
    ranking = []
    for t in DEMO_TICKERS:
        ranking.append({
            "Ticker": t,
            "Score": global_score(
                np.random.uniform(-5,5),
                np.random.uniform(-1,1)
            )
        })
    st.table(pd.DataFrame(ranking).sort_values("Score", ascending=False))

    st.caption("Modo DEMO 100% — datos simulados con fines demostrativos")
