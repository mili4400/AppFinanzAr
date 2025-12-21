# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta, time

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="AppFinanzAr", layout="wide")

# =========================================================
# SAFE IMPORTS + FALLBACKS
# =========================================================
try:
    from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
except Exception:
    def fetch_ohlc(*args, **kwargs): return pd.DataFrame()
    def fetch_fundamentals(t): return {}, []
    def fetch_news(t, *a, **k): return []
    def search_ticker_by_name(name): return []

try:
    from core.overview import build_overview
except Exception:
    def build_overview(ticker, lang="es"):
        prices = 100 + np.cumsum(np.random.randn(120))
        df = pd.DataFrame({
            "date": pd.date_range(end=datetime.today(), periods=len(prices)),
            "close": prices
        })
        return {
            "executive_summary": {
                "name": ticker,
                "sector": "Technology",
                "industry": "Software",
                "country": "USA",
                "valuation": {"pe_ratio": 25, "market_cap": "1T", "eps": 5},
                "price_trend_30d": np.random.uniform(-6, 6)
            },
            "fundamentals": {"Revenue": "1000M", "Profit": "200M", "Debt": "Low"},
            "competitors": ["AAPL", "GOOGL", "AMZN"],
            "news": [{"title": "Demo news positive outlook", "published_at": str(datetime.today())}],
            "sentiment_label": "Neutral",
            "fundamentals_summary": "Empresa sólida con crecimiento estable."
        }

try:
    from core.etf_finder import etf_screener
except Exception:
    def etf_screener(theme=None):
        return [{"ETF": "TECHETF", "Theme": theme or "General"}]

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a, b): return {"Momentum": 0.6, "Volatility": 0.3}
    def compare_sentiment(a, b): return {"A": 0.2, "B": -0.1}

try:
    from core.utils import sma, ema, rsi
except Exception:
    def sma(s, n): return s.rolling(n).mean()
    def ema(s, n): return s.ewm(span=n).mean()
    def rsi(s, n):
        delta = s.diff()
        gain = delta.clip(lower=0).rolling(n).mean()
        loss = -delta.clip(upper=0).rolling(n).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

try:
    from core.sentiment_model import sentiment_score
except Exception:
    def sentiment_score(t):
        t = (t or "").lower()
        if "positive" in t or "up" in t: return 0.6
        if "negative" in t or "down" in t: return -0.6
        return 0.0

# =========================================================
# CONSTANTES DEMO
# =========================================================
DEMO_TICKERS = ["MSFT.US", "AAPL.US", "GOOGL.US", "AMZN.US", "GGAL.BA"]

PRICE_ALERTS = {
    "MSFT.US": ("Precio muy alto", "green"),
    "GGAL.BA": ("Precio muy bajo", "red")
}

# =========================================================
# HELPERS
# =========================================================
def market_status():
    now = datetime.now().time()
    open_time = time(9, 30)
    close_time = time(16, 0)
    if open_time <= now <= close_time:
        return "🟢 Mercado abierto"
    if now < open_time:
        return "🟡 Abre en menos de 1h"
    return "🔴 Mercado cerrado"

def global_score(trend, sentiment):
    return round((trend * 0.6 + sentiment * 40), 2)

# =========================================================
# DASHBOARD
# =========================================================
def show_dashboard():
    st.title("📊 AppFinanzAr")

    if "favorites" not in st.session_state:
        st.session_state.favorites = []

    # =====================================================
    # SIDEBAR
    # =====================================================
    with st.sidebar:
        st.subheader("🕒 Mercado")
        st.write(market_status())

        st.subheader("⭐ Favoritos")

        to_remove = None

        for f in st.session_state.favorites:
            label, color = PRICE_ALERTS.get(f, ("", "#FFFFFF"))
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"<span style='color:{color}; font-weight:600'>• {f} {label}</span>",
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("❌", key=f"fav_del_{f}"):
                    to_remove = f

        if to_remove:
            st.session_state.favorites.remove(to_remove)
            st.success(f"{to_remove} eliminado de favoritos")


        if st.session_state.favorites:
            csv = pd.DataFrame(st.session_state.favorites, columns=["Ticker"]).to_csv(index=False)
            st.download_button("⬇ Exportar favoritos", csv, "favoritos.csv")

        st.markdown("---")
        st.subheader("Buscar empresa")
        company = st.text_input("Nombre empresa")
        if company:
            res = search_ticker_by_name(company)
            if res:
                st.write(res)

    # =====================================================
    # SELECCIÓN TICKER
    # =====================================================
    st.subheader("Selección de activo")
    ticker = st.selectbox("Ticker (demo incluido)", DEMO_TICKERS)

    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            st.session_state.favorites.append(ticker)
            st.success("Agregado correctamente")

    # =====================================================
    # RANGO DE FECHAS
    # =====================================================
    st.subheader("Rango de análisis")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Desde", datetime.today() - timedelta(days=90))
    with col2:
        end_date = st.date_input("Hasta", datetime.today())

    # =====================================================
    # DATA OHLC
    # =====================================================
    df = fetch_ohlc(ticker, start_date, end_date)
    if df.empty:
        idx = pd.date_range(start=start_date, end=end_date)
        price = 100 + np.cumsum(np.random.randn(len(idx)))
        df = pd.DataFrame({
            "date": idx,
            "open": price - 1,
            "high": price + 1,
            "low": price - 2,
            "close": price
        })

    df["SMA20"] = sma(df["close"], 20)
    df["EMA20"] = ema(df["close"], 20)
    df["RSI14"] = rsi(df["close"], 14)

    # =====================================================
    # GRÁFICO
    # =====================================================
    st.subheader("📈 Precio e indicadores")
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

    # =====================================================
    # OVERVIEW
    # =====================================================
    ov = build_overview(ticker)
    es = ov["executive_summary"]

    sentiment = sentiment_score(ov["news"][0]["title"])
    score = global_score(es["price_trend_30d"], sentiment)

    st.subheader("📋 Resumen Ejecutivo")
    st.metric("Score Global", score)
    st.write(es)

    st.subheader("Fundamentales")
    st.table(pd.DataFrame.from_dict(ov["fundamentals"], orient="index", columns=["Valor"]))

    st.subheader("Competidores")
    st.write(", ".join(ov["competitors"]))

    # =====================================================
    # NOTICIAS
    # =====================================================
    st.subheader("📰 Noticias & Sentimiento")
    for n in ov["news"]:
        news_list = ov.get("news", [])
        if news_list:
            sentiment = sentiment_score(news_list[0].get("title", ""))
        else:
            sentiment = 0.0
        st.write(f"- {n['title']} ({s:+.2f})")

    # =====================================================
    # ETF FINDER
    # =====================================================
    st.subheader("🧭 ETF Finder")

    st.caption("Explorá ETFs por temática o escribí tu propio criterio")

    tema_sel = st.selectbox(
        "Temas sugeridos",
        ["— Elegir tema —"] + ETF_THEMES
    )

    tema_custom = st.text_input(
        "O buscar por palabra clave (ej: space, lithium, oil, nasa)"
    )

    buscar = st.button("Buscar ETFs")

    if buscar:
        tema_final = None

        if tema_custom:
            tema_final = tema_custom
        elif tema_sel != "— Elegir tema —":
            tema_final = tema_sel

        if tema_final:
            etfs = etf_screener(tema_final)
            if etfs:
                st.table(pd.DataFrame(etfs))
            else:
                st.info("No se encontraron ETFs para este tema.")
        else:
            st.warning("Seleccioná o escribí un tema para buscar.")

    # =====================================================
    # COMPARACIÓN
    # =====================================================
    st.subheader("🔀 Comparación rápida (2 tickers)")

    colA, colB = st.columns(2)
    t_a = colA.text_input("Ticker A", ticker, key="cmp_a")
    t_b = colB.text_input("Ticker B", "AAPL.US", key="cmp_b")

    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a, t_b) or {}
        sent = compare_sentiment(t_a, t_b) or {}

        # Fallback demo si viene vacío
        if not cmp:
            cmp = {
                "Score técnico": np.random.uniform(40, 80),
                "Score fundamental": np.random.uniform(40, 80),
                "Volatilidad": np.random.uniform(10, 30),
            }

        if not sent:
            sent = {
                t_a: np.random.uniform(-1, 1),
                t_b: np.random.uniform(-1, 1),
            }

        st.markdown("### 📊 Indicadores comparados")
        st.dataframe(
            pd.DataFrame.from_dict(cmp, orient="index", columns=["Valor"])
        )

        st.markdown("### 🧠 Sentimiento comparado")
        st.bar_chart(pd.Series(sent))

    # =====================================================
    # RANKING
    # =====================================================
    st.subheader("🏆 Ranking de oportunidades")
    ranking = []
    for t in DEMO_TICKERS:
        tr = np.random.uniform(-5, 5)
        se = np.random.uniform(-0.5, 0.5)
        ranking.append({"Ticker": t, "Score": global_score(tr, se)})
    st.table(pd.DataFrame(ranking).sort_values("Score", ascending=False))

    st.caption("Modo demo – datos simulados y educativos")
