# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news
from core.overview import build_overview
from core.compare import get_competitors
from core.etf_finder import etf_screener
from core.favorites import load_favorites, add_favorite
from core.compare_pro import compare_indicators, compare_sentiment
from core.utils import sma, ema, rsi
from core.sentiment_model import sentiment_score

# ---------------------------
# Demo universe + helpers
# ---------------------------
def load_demo_universe():
    """
    Carga un universo demo desde data/demo_universe.json si existe,
    si no, usa un fallback embebido (muestra ~40 global + ~10 BYMA para demo).
    Formato: [{"symbol":"MSFT.US","name":"Microsoft Corp"}, ...]
    """
    path = os.path.join(os.path.dirname(__file__), "..", "data", "demo_universe.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fallback compacto (puedes ampliarlo hasta 100+)
        return [
            {"symbol": "MSFT.US", "name": "Microsoft Corp"},
            {"symbol": "AAPL.US", "name": "Apple Inc"},
            {"symbol": "GOOGL.US", "name": "Alphabet Inc"},
            {"symbol": "AMZN.US", "name": "Amazon.com Inc"},
            {"symbol": "NVDA.US", "name": "NVIDIA Corp"},
            {"symbol": "TSLA.US", "name": "Tesla Inc"},
            {"symbol": "META.US", "name": "Meta Platforms"},
            {"symbol": "NFLX.US", "name": "Netflix Inc"},
            {"symbol": "BABA.US", "name": "Alibaba Group"},
            {"symbol": "MELI.US", "name": "MercadoLibre"},
            # BYMA sample (argentina) — ajústalos a tu convención (.BA/.AR etc.)
            {"symbol": "GGAL.BA", "name": "Grupo Financiero Galicia"},
            {"symbol": "YPFD.BA", "name": "YPF SA"},
            {"symbol": "PAMP.BA", "name": "Pampa Energia"},
            {"symbol": "BMA.BA", "name": "Banco Macro"},
            {"symbol": "SUPV.BA", "name": "Grupo Supervielle"},
            # Más globales / diversificados
            {"symbol": "XLF.US", "name": "Financial Select Sector SPDR Fund"},
            {"symbol": "XLE.US", "name": "Energy Select Sector SPDR Fund"},
            {"symbol": "GLD.US", "name": "SPDR Gold Trust"},
            {"symbol": "TLT.US", "name": "iShares 20+ Year Treasury Bond ETF"},
            {"symbol": "QQQ.US", "name": "Invesco QQQ Trust"},
            # (Puedes añadir más hasta 100 si querés)
        ]


DEMO_UNIVERSE = load_demo_universe()


def search_tickers_local(q, max_results=10):
    """
    Búsqueda simple por nombre o símbolo en el universo demo.
    Prioriza coincidencia en símbolo, luego en nombre (case-insensitive).
    """
    if not q:
        return []
    ql = q.strip().lower()
    matches = []
    # match symbol startswith
    for item in DEMO_UNIVERSE:
        sym = item.get("symbol", "")
        if sym.lower().startswith(ql):
            matches.append(sym)
            if len(matches) >= max_results:
                return matches
    # match name contains
    for item in DEMO_UNIVERSE:
        name = item.get("name", "").lower()
        sym = item.get("symbol", "")
        if ql in name and sym not in matches:
            matches.append(sym)
            if len(matches) >= max_results:
                break
    return matches


# ---------------------------
# Utilities: demo OHLC generator (fallback)
# ---------------------------
def generate_demo_ohlc(symbol, days=180):
    """
    Genera una serie OHLC demo para visualizar cuando la API falla o se agotaron consultas.
    """
    np.random.seed(abs(hash(symbol)) % (2**32))
    end = datetime.today().date()
    dates = pd.date_range(end=end - timedelta(days=0), periods=days).to_pydatetime().tolist()
    # simple random walk
    price = 100.0 + (abs(hash(symbol)) % 50)
    closes = []
    for i in range(days):
        change = np.random.normal(0, 1.2)
        price = max(0.1, price * (1 + change / 100))
        closes.append(round(price, 2))
    df = pd.DataFrame({
        "date": [d.date() for d in dates],
        "open": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes],
        "close": closes,
        "volume": [int(1e6 * (0.5 + np.random.rand())) for _ in closes]
    })
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------
# Sentiment wrapper (retrocompat)
# ---------------------------
def analyze_sentiment_textblob(text: str):
    """
    Retrocompatibilidad: dashboard_ui espera esta función.
    Usa el modelo transformer real (sentiment_score) y mapea a etiquetas textblob-like.
    """
    try:
        score = sentiment_score(text)
    except Exception:
        # fallback very simple polarity
        score = 0.0
        if isinstance(text, str):
            t = text.lower()
            if "rise" in t or "sube" in t or "positivo" in t:
                score = 0.5
            if "fall" in t or "cae" in t or "negativo" in t:
                score = -0.5

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return float(score), label


# ---------------------------
# DASHBOARD MAIN
# ---------------------------
def show_dashboard():
    st.title("📊 AppFinanzAr – Dashboard (Demo-friendly)")

    # LANGUAGE SELECTOR
    lang = st.sidebar.selectbox("Idioma / Language", ["Español", "English"])
    lang_code = "es" if lang == "Español" else "en"

    # SEARCH / AUTOCOMPLETE area
    st.markdown("### Buscar activo")
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US) o parte del nombre", value="", key="dash_ticker_input")
    with col2:
        if st.button("Usar demo"):
            # preseleccionar primer demo para verificar visualización
            if DEMO_UNIVERSE:
                st.session_state["dash_ticker_input"] = DEMO_UNIVERSE[0]["symbol"]

    # oferta de autocompletado local
    suggestions = search_tickers_local(ticker_input, max_results=12) if ticker_input else []
    if suggestions:
        # si hay sugerencias, mostrarlas en selectbox para elegir
        ticker = st.selectbox("Coincidencias", options=["-- seleccionar --"] + suggestions, index=0)
        if ticker == "-- seleccionar --":
            ticker = ""
    else:
        ticker = ticker_input.strip()

    if not ticker:
        st.info("Escribí un ticker o nombre (ej: 'Galicia' o 'MSFT') para ver demo.")
        return

    # DATE RANGE
    st.markdown("### Rango de fechas")
    range_days = st.selectbox("Rango rápido", ["1m", "3m", "6m", "1y", "5y", "max"], index=0)
    custom_range = st.checkbox("Usar rango personalizado")
    if custom_range:
        start_date = st.date_input("Inicio", datetime.today() - timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        today = datetime.today().date()
        mapping = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "5y": 365 * 5, "max": 365 * 10}
        days = mapping.get(range_days, 365)
        start_date = today - timedelta(days=days)
        end_date = today

    # FAVORITOS (sidebar)
    st.sidebar.markdown("### ⭐ Favoritos (FREE)")
    st.sidebar.caption("Máx 5 — Demo")
    username = st.session_state.get("username", "demo")
    favs = load_favorites(username)
    if not isinstance(favs, dict):
        favs = {"all": favs, "categories": {}}
    favs.setdefault("all", [])
    favs.setdefault("categories", {})

    if st.sidebar.button("Agregar ticker a Favoritos"):
        # guardamos el ticker literal (string) como favorito
        tu = ticker.upper()
        if tu in favs["all"]:
            st.sidebar.warning("Ya está en favoritos.")
        elif len(favs["all"]) >= 5:
            st.sidebar.error("Límite alcanzado (5).")
        else:
            add_favorite(username, tu)
            st.sidebar.success(f"{tu} agregado.")
            favs = load_favorites(username)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tus Favoritos")
    for f in favs.get("all", [])[:10]:
        st.sidebar.write(f"• {f}")
    st.sidebar.markdown("---")

    # FETCH DATA (try real -> fallback demo)
    df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    used_demo_prices = False
    if df is None or (hasattr(df, "empty") and df.empty):
        # fallback demo OHLC
        df = generate_demo_ohlc(ticker, days= max(60, (end_date - start_date).days + 1))
        used_demo_prices = True

    # Ensure there are expected columns
    for c in ["date", "open", "high", "low", "close", "volume"]:
        if c not in df.columns:
            df[c] = pd.NA
    # Ensure date typed
    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception:
        df["date"] = pd.date_range(end=datetime.today(), periods=len(df))

    # Basic indicators
    df = df.sort_values("date").reset_index(drop=True)
    df["SMA20"] = sma(df["close"], 20) if "close" in df else None
    df["SMA50"] = sma(df["close"], 50) if "close" in df else None
    df["EMA20"] = ema(df["close"], 20) if "close" in df else None
    df["RSI14"] = rsi(df["close"], 14) if "close" in df else None

    # PRICE CHART (candlestick) - simplified
    st.subheader(f"Gráfico de precio — {ticker} {'(demo)' if used_demo_prices else ''}")
    fig = go.Figure()
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]
        )])
    except Exception:
        # fallback simple line
        fig = go.Figure(go.Scatter(x=df["date"], y=df["close"], mode="lines"))
    # add moving averages if present
    if "SMA20" in df:
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
    if "SMA50" in df:
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
    if "EMA20" in df:
        fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
    fig.update_layout(height=520, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # RSI strip
    if "RSI14" in df:
        rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
        rsi_fig.update_layout(height=200, template="plotly_dark")
        st.plotly_chart(rsi_fig, use_container_width=True)

    # OVERVIEW CARD (uses build_overview but we keep fallback if empty)
    try:
        overview = build_overview(ticker, lang=lang_code)
    except Exception:
        # fallback minimal overview using fetch_fundamentals
        fundamentals, competitors_list = fetch_fundamentals(ticker)
        overview = {
            "fundamentals": fundamentals or {},
            "competitors": (competitors_list or [])[:5],
            "price": df,
            "news": fetch_news(ticker) or [],
            "sentiment_value": 0,
            "sentiment_label": "Sin datos",
            "fundamentals_summary": fundamentals.get("Description","")[:300] if fundamentals else "",
            "executive_summary": {
                "name": fundamentals.get("Name","N/A") if isinstance(fundamentals, dict) else "N/A",
                "sector": fundamentals.get("Sector","N/A") if isinstance(fundamentals, dict) else "N/A",
                "industry": fundamentals.get("Industry","N/A") if isinstance(fundamentals, dict) else "N/A",
                "country": fundamentals.get("Country","N/A") if isinstance(fundamentals, dict) else "N/A",
                "valuation": {
                    "pe_ratio": fundamentals.get("PERatio","N/A") if isinstance(fundamentals, dict) else "N/A",
                    "market_cap": fundamentals.get("MarketCapitalization","N/A") if isinstance(fundamentals, dict) else "N/A",
                    "eps": fundamentals.get("EPS","N/A") if isinstance(fundamentals, dict) else "N/A",
                },
                "price_trend_30d": None
            }
        }

    st.subheader("Overview")
    exec_sum = overview.get("executive_summary", {})
    card_md = f"""
**{exec_sum.get('name','N/A')}**  
Sector: {exec_sum.get('sector','N/A')} · Industria: {exec_sum.get('industry','N/A')} · País: {exec_sum.get('country','N/A')}  

**Valoración** — P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')} · Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')} · EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}  

**Tendencia 30d:** {exec_sum.get('price_trend_30d','N/A')} · **Sentimiento:** {overview.get('sentiment_label','Sin datos')}  

**Resumen:** {overview.get('fundamentals_summary','(sin resumen)')}
"""
    st.markdown(card_md)

    # FUNDAMENTALS TABLE (compact)
    st.subheader("Fundamentales clave")
    fundamentals = overview.get("fundamentals", {}) or {}
    if isinstance(fundamentals, dict) and fundamentals:
        df_f = pd.DataFrame.from_dict(fundamentals, orient="index", columns=["Valor"])
        # show only first 12 rows to avoid long dumps
        st.dataframe(df_f.head(12))
    else:
        st.info("No se encontraron fundamentales válidos.")

    # COMPETITORS
    st.subheader("Competidores (máx 5)")
    competitors = overview.get("competitors", []) or []
    if competitors:
        st.write(", ".join(competitors[:5]))
        # quick competitor stats (if possible)
        comp_stats = get_competitors(ticker)
        if comp_stats:
            st.write("Competitors (quick):", ", ".join(comp_stats))
    else:
        st.info("No se encontraron competidores.")

    # NEWS + SENTIMENT (simplified)
    st.subheader("Noticias recientes y sentimiento")
    news_items = overview.get("news", []) or []
    if news_items:
        sentiment_points = []
        for n in news_items[:10]:
            title = n.get("title", "") or n.get("headline", "")
            published = n.get("published_at", "") or n.get("datetime", "")
            score, label = analyze_sentiment_textblob(title)
            sentiment_points.append({"date": published, "sentiment": score, "label": label, "title": title})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")

        # Bar chart of sentiments (compact)
        sdf = pd.DataFrame(sentiment_points)
        if not sdf.empty:
            colors = sdf["sentiment"].apply(lambda x: "green" if x > 0 else "red" if x < 0 else "gray")
            fig_s = go.Figure(go.Bar(x=sdf["title"], y=sdf["sentiment"], marker_color=colors))
            fig_s.update_layout(title="Sentimiento (noticias)", template="plotly_dark",
                                xaxis_tickangle=-45, height=300)
            st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("No hay noticias disponibles para este ticker.")

    # ETF FINDER (uses etf_screener wrapper)
    st.subheader("ETF Finder (temático)")
    tema = st.text_input("Tema (ej: AI, Energy, Metals)", key="etf_tema")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema) if tema else etf_screener()
        if etfs:
            # show concise table
            df_etf = pd.DataFrame(etfs)
            st.dataframe(df_etf.head(12))
        else:
            st.info("No se encontraron ETFs para ese tema.")

    # COMPARACIÓN (2 tickers)
    st.subheader("Comparación entre 2 tickers (FREE)")
    c1 = ticker
    c2 = st.text_input("Ticker a comparar", value=(DEMO_UNIVERSE[1]["symbol"] if len(DEMO_UNIVERSE) > 1 else "AAPL.US"))
    if st.button("Comparar"):
        try:
            res = compare_indicators(c1, c2)
            sent = compare_sentiment(c1, c2)
            st.write("Indicadores:", res if res else "No hay datos para comparar")
            st.write("Sentimiento:", sent)
        except Exception as e:
            st.error(f"Error al comparar: {e}")

    # FOOTER / status
    st.markdown("---")
    st.caption("Modo demo: la app usa datos reales si están disponibles; si no, muestra datos demo para que puedas visualizar la UI.")

