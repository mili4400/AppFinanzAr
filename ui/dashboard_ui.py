# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta

# core (no modificamos otros archivos)
from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news
from core.overview import build_overview
from core.etf_finder import etf_screener
from core.favorites import load_favorites, add_favorite
from core.compare_pro import compare_indicators, compare_sentiment
from core.utils import sma, ema, rsi

# sentiment model if available
try:
    from core.sentiment_model import sentiment_score
    SENT_MODEL_AVAILABLE = True
except Exception:
    SENT_MODEL_AVAILABLE = False

# Try to use optional helper search_ticker_by_name if present in core.data_fetch
try:
    from core.data_fetch import search_ticker_by_name
    HAVE_SEARCH_TICKER_BY_NAME = True
except Exception:
    HAVE_SEARCH_TICKER_BY_NAME = False

# -----------------------------
# Yahoo lightweight search fallback (no API key)
# -----------------------------
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

def search_yahoo(query, limit=12):
    try:
        params = {"q": query, "quotesCount": limit, "newsCount": 0}
        r = requests.get(YAHOO_SEARCH_URL, params=params, timeout=6)
        r.raise_for_status()
        j = r.json()
        out = []
        for q in j.get("quotes", []):
            sym = q.get("symbol")
            exch = q.get("exchange") or q.get("exchDisp") or q.get("exchangeName","")
            if not sym:
                continue
            suffix = ""
            ex = (exch or "").upper()
            if ex in ("NMS","NASDAQ","NYSE","NYQ","AMEX"):
                suffix = ".US"
            if "BUENOS" in ex or "BCBA" in ex or "BUE" in ex or "ARG" in ex:
                suffix = ".BA"
            if suffix and not sym.endswith(suffix):
                label = f"{sym}{suffix}"
            else:
                label = sym
            if label not in out:
                out.append(label)
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []

# -----------------------------
# Simple sentiment fallback
# -----------------------------
POS = {"good","great","positive","up","beats","gain","bull","strong","growth","profit"}
NEG = {"bad","poor","negative","down","miss","loss","bear","weak","decline","drop","fall"}

def simple_sentiment(text):
    t = (text or "").lower()
    s = 0
    for w in POS:
        if w in t:
            s += 0.5
    for w in NEG:
        if w in t:
            s -= 0.5
    return max(-1.0, min(1.0, s))

def analyze_sentiment_textblob(text: str):
    try:
        if SENT_MODEL_AVAILABLE:
            score = sentiment_score(text)
        else:
            score = simple_sentiment(text)
    except Exception:
        score = simple_sentiment(text)

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return score, label

# -----------------------------
# Small helpers
# -----------------------------
def ensure_favs_struct(favs_raw):
    if favs_raw is None:
        return {"all": [], "categories": {}}
    if isinstance(favs_raw, dict):
        favs_raw.setdefault("all", [])
        favs_raw.setdefault("categories", {})
        return favs_raw
    # assume list
    return {"all": favs_raw, "categories": {}}

def sentiment_label_from_value(v):
    if v is None:
        return "Sin datos"
    if v > 0.2:
        return "📈 Positivo"
    if v < -0.2:
        return "📉 Negativo"
    return "🔍 Neutral"

# -----------------------------
# Main UI
# -----------------------------
def show_dashboard():
    st.title("📊 AppFinanzAr – Dashboard Completo")

    # language
    lang = st.sidebar.selectbox("Idioma / Language", ["Español", "English"])
    lang_code = "es" if lang == "Español" else "en"

    # ticker entry + company search/autocomplete
    st.markdown("### 🔎 Buscar activo")

    ticker_input = st.text_input("Ingrese ticker (ej: MSFT, AAPL, GGAL.BA)", "MSFT")
    company_search = st.text_input("Si no conoces el ticker, buscá por nombre de empresa", "")

    # determine ticker suggestions
    suggestions = []
    if company_search:
        if HAVE_SEARCH_TICKER_BY_NAME:
            try:
                suggestions = search_ticker_by_name(company_search)
            except Exception:
                suggestions = search_yahoo(company_search)
        else:
            suggestions = search_yahoo(company_search)

    ticker = ticker_input.strip().upper()

    if suggestions:
        sel = st.selectbox("Sugerencias", suggestions, index=0)
        if sel:
            ticker = sel

    # quick range + manual
    range_days = st.selectbox("Rango rápido", ["1m","3m","6m","1y","5y","max"], index=0)
    custom_range = st.checkbox("Usar rango personalizado")
    if custom_range:
        start_date = st.date_input("Inicio", datetime.today() - timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        today = datetime.today().date()
        mapping = {"1m":30, "3m":90, "6m":180, "1y":365, "5y":365*5, "max":365*10}
        start_date = today - timedelta(days=mapping.get(range_days, 365))
        end_date = today

    st.markdown(f"**Ticker seleccionado:** `{ticker}`")

    # -----------------------------
    # Favoritos sidebar
    # -----------------------------
    st.sidebar.markdown("### ⭐ Favoritos (FREE)")
    st.sidebar.caption("Máximo 5 → Para más: versión PRO")
    username = st.session_state.get("username", "demo")
    favs_raw = load_favorites(username)
    favs = ensure_favs_struct(favs_raw)
    MAX_FAVS = 5

    if st.sidebar.button("Agregar ticker a Favoritos"):
        tu = ticker.upper()
        if tu in favs['all']:
            st.sidebar.warning("El ticker ya está en favoritos.")
        elif len(favs['all']) >= MAX_FAVS:
            st.sidebar.error("Límite alcanzado (5). Versión PRO disponible.")
        else:
            try:
                add_favorite(username, tu)
                st.sidebar.success(f"{tu} agregado.")
                # refresh
                favs_raw = load_favorites(username)
                favs = ensure_favs_struct(favs_raw)
            except Exception:
                st.sidebar.error("No se pudo guardar favorito.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tus favoritos")
    if favs['all']:
        for f in favs['all']:
            st.sidebar.write(f"• {f}")
    else:
        st.sidebar.info("No tenés favoritos guardados.")

    # -----------------------------
    # Fetch data (OHLC)
    # -----------------------------
    try:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    except Exception:
        df = pd.DataFrame()

    if df is None or (hasattr(df, "empty") and df.empty):
        # implicit demo behavior: show synthetic demo but keep other functionality visible
        st.info("Modo DEMO: no hay datos reales disponibles — mostrando demo sintético.")
        rng = pd.date_range(end=datetime.today(), periods=90)
        np.random.seed(42)
        base = np.linspace(100, 150, len(rng))
        noise = np.random.normal(0, 3, len(rng))
        close = base + noise
        open_ = close + np.random.normal(0, 1, len(rng))
        high = np.maximum(open_, close) + np.abs(np.random.normal(0, 2, len(rng)))
        low = np.minimum(open_, close) - np.abs(np.random.normal(0, 2, len(rng)))
        vol = np.random.randint(10000, 200000, len(rng))
        df = pd.DataFrame({"date": rng, "open": open_, "high": high, "low": low, "close": close, "volume": vol})

    # ensure date type
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    else:
        df.reset_index(inplace=True)
        df.rename(columns={"index":"date"}, inplace=True)

    # indicators (use core.utils when possible)
    try:
        df["SMA20"] = sma(df["close"], 20)
        df["SMA50"] = sma(df["close"], 50)
        df["EMA20"] = ema(df["close"], 20)
        df["RSI14"] = rsi(df["close"], 14)
    except Exception:
        df["SMA20"] = df["close"].rolling(20).mean()
        df["SMA50"] = df["close"].rolling(50).mean()
        df["EMA20"] = df["close"].ewm(span=20).mean()
        df["RSI14"] = (df["close"].diff().fillna(0) > 0).rolling(14).mean() * 100

    # -----------------------------
    # Price chart (candlestick) + overlay indicators
    # -----------------------------
    st.subheader("📈 Precio histórico")
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]
    )])
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
    fig.update_layout(height=600, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # RSI plot
    st.subheader("📊 RSI 14")
    rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
    rsi_fig.update_layout(height=200, template="plotly_dark")
    st.plotly_chart(rsi_fig, use_container_width=True)

    # -----------------------------
    # Overview + fundamentals + competitors
    # -----------------------------
    st.subheader("📘 Overview General del Activo")
    try:
        overview = build_overview(ticker, lang=lang_code)
    except TypeError:
        overview = build_overview(ticker)

    # render compact card
    exec_sum = overview.get("executive_summary") if isinstance(overview, dict) else None
    if exec_sum:
        st.markdown(
            f"**{exec_sum.get('name','N/A')}**  \n"
            f"Sector: {exec_sum.get('sector','N/A')}  \n"
            f"Industria: {exec_sum.get('industry','N/A')}  \n"
            f"País: {exec_sum.get('country','N/A')}  \n\n"
            f"**Valoración:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')} | "
            f"MarketCap: {exec_sum.get('valuation',{}).get('market_cap','N/A')} | "
            f"EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}  \n\n"
            f"**Tendencia 30d:** {exec_sum.get('price_trend_30d','N/A')}%  \n"
            f"**Sentimiento:** {overview.get('sentiment_label','Sin datos')}  \n\n"
            f"**Resumen:** {overview.get('fundamentals_summary','N/A')}"
        )
    else:
        st.info("No hay overview estructurado. Se muestran fundamentales crudos abajo.")

    st.subheader("📂 Fundamentales Clave")
    fundamentals = overview.get("fundamentals") if isinstance(overview, dict) else None
    if fundamentals:
        try:
            st.dataframe(pd.DataFrame.from_dict(fundamentals, orient="index", columns=["Valor"]))
        except Exception:
            st.json(fundamentals)
    else:
        st.info("No se encontraron fundamentales válidos.")

    st.subheader("🏦 Competidores Reales (Industria / Sector / País)")
    competitors = overview.get("competitors") if isinstance(overview, dict) else None
    if competitors:
        if isinstance(competitors, list):
            st.write(", ".join([str(c) for c in competitors[:8]]))
        else:
            st.json(competitors)
    else:
        st.info("No se encontraron competidores.")

    # -----------------------------
    # Noticias + sentimiento
    # -----------------------------
    st.subheader("📰 Noticias y Sentimiento")
    news_items = overview.get("news") if isinstance(overview, dict) else fetch_news(ticker)
    if news_items:
        sentiment_points = []
        for n in news_items[:10]:
            title = n.get("title","")
            published = n.get("published_at", n.get("pubDate",""))
            score, label = analyze_sentiment_textblob(title + " " + n.get("content","")[:400])
            sentiment_points.append({"date": published, "sentiment": score, "label": label, "title": title})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
        sdf = pd.DataFrame(sentiment_points)
        if not sdf.empty:
            colors = sdf['sentiment'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
            fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['sentiment'], marker_color=colors))
            fig_s.update_layout(title="Sentimiento de noticias", template="plotly_dark", xaxis_tickangle=-45, height=320)
            st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("No hay noticias disponibles.")

    # -----------------------------
    # ETF finder
    # -----------------------------
    st.subheader("📈 ETF Finder (Temático)")
    tema = st.text_input("Tema (ej: AI, Energy, Metals)")
    if tema:
        try:
            etfs = etf_screener(tema)
            if etfs:
                # show up to 8 results
                if isinstance(etfs, list):
                    st.write(", ".join([str(e) for e in etfs[:8]]))
                else:
                    st.write(etfs)
            else:
                st.info("No se encontraron ETFs temáticos.")
        except Exception:
            st.info("ETF Finder no disponible.")

    # -----------------------------
    # Comparación entre 2 tickers
    # -----------------------------
    st.subheader("⚔️ Comparación entre dos tickers (FREE)")
    t2 = st.text_input("Ticker a comparar", "AAPL")
    if t2:
        try:
            ci = compare_indicators(ticker, t2)
            cs = compare_sentiment(ticker, t2)
            st.json({"indicators": ci, "sentiment": cs})
        except Exception:
            st.info("Comparación no disponible (revisar logs).")

# End file


