# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta

# Core functions (existentes en tu proyecto)
from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news
from core.overview import build_overview
from core.etf_finder import etf_screener
from core.favorites import load_favorites, add_favorite
from core.compare_pro import compare_indicators, compare_sentiment
from core.utils import sma, ema, rsi

# Sentiment model: usar si está, si no -> fallback simple
try:
    from core.sentiment_model import sentiment_score
    SENT_MODEL_AVAILABLE = True
except Exception:
    SENT_MODEL_AVAILABLE = False

# -------------------------
# Helpers: Yahoo autocomplete
# -------------------------
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

def search_yahoo(query, limit=12):
    """
    Busca sugerencias de tickers en Yahoo Finance.
    Devuelve lista de strings tipo "AAPL" o "GGAL.BA" (intentar mapear exchanges simples).
    """
    try:
        params = {"q": query, "quotesCount": limit, "newsCount": 0}
        resp = requests.get(YAHOO_SEARCH_URL, params=params, timeout=6)
        resp.raise_for_status()
        j = resp.json()
        res = []
        for q in j.get("quotes", []) + j.get("news", []):
            # preferir quotes entries; news entries included just in case
            if not isinstance(q, dict):
                continue
            sym = q.get("symbol")
            exch = q.get("exchange") or q.get("exchDisp") or q.get("exchangeName")
            if not sym:
                continue
            # Map simple exchanges to suffixes (EOD style). Ajustá si necesitás más mapeos.
            suffix = ""
            if exch:
                exch = exch.upper()
                if exch in ("NMS", "NASDAQ", "NYSE", "NYQ", "AMEX"):
                    suffix = ".US"
                # argentinos: Yahoo usa "BCBA" or "Buenos Aires", símbolo a veces con .BA
                if exch in ("BCBA", "BUENOS AIRES", "BUE", "ARG"):
                    suffix = ".BA"
                # brasil
                if "B3" in exch or exch in ("SAO", "SÃO PAULO", "BVMF"):
                    suffix = ".SA"
            # Evitar duplicados
            label = f"{sym}{suffix}"
            if label not in res:
                res.append(label)
            if len(res) >= limit:
                break
        return res
    except Exception:
        return []

# -------------------------
# Helpers: sentiment fallback
# -------------------------
POS_WORDS = {"good","great","positive","up","beats","beat","gain","bull","strong","growth","growths","profit"}
NEG_WORDS = {"bad","poor","negative","down","miss","missed","loss","bear","weak","decline","drop","fall"}

def simple_sentiment(text):
    t = (text or "").lower()
    score = 0.0
    for w in POS_WORDS:
        if w in t:
            score += 0.6
    for w in NEG_WORDS:
        if w in t:
            score -= 0.6
    # normalize
    if score > 0:
        return min(score, 1.0)
    if score < 0:
        return max(score, -1.0)
    return 0.0

def analyze_sentiment_textblob(text: str):
    """
    Retrocompat ilustrativa: devuelve (score, label)
    Intenta usar model real; si no, usa fallback.
    """
    try:
        if SENT_MODEL_AVAILABLE:
            s = sentiment_score(text)
        else:
            s = simple_sentiment(text)
    except Exception:
        s = simple_sentiment(text)

    if s > 0.1:
        label = "positive"
    elif s < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return s, label

# -------------------------
# UI: Show dashboard
# -------------------------
def show_dashboard():
    st.title("📊 AppFinanzAr – Dashboard Completo")

    # idioma
    lang = st.sidebar.selectbox("Idioma / Language", ["Español", "English"])
    lang_code = "es" if lang == "Español" else "en"

    # Ticker input + empresa search + autocomplete Yahoo
    st.markdown("#### 🔎 Buscar activo")
    ticker_input = st.text_input("Ingrese ticker (ej: MSFT, AAPL, GGAL.BA)", "MSFT")
    company_search = st.text_input("Buscar por nombre de empresa (autocomplete)", "")

    ticker = ticker_input.strip().upper()

    # si el usuario escribe nombre, buscar sugerencias y mostrar selectbox
    if company_search:
        with st.spinner("Buscando tickers..."):
            suggestions = search_yahoo(company_search, limit=20)
        if suggestions:
            choice = st.selectbox("Sugerencias", suggestions, index=0)
            ticker = choice
        else:
            st.info("No se encontraron sugerencias (intenta otra palabra)")

    # botón para forzar autocomplete directo por ticker_input parcial
    if not company_search:
        # si escribiste parcialmente el ticker, ofrecer autocompletar por símbolo/nombre
        if ticker_input and len(ticker_input.strip()) >= 2:
            suggestions2 = search_yahoo(ticker_input.strip(), limit=8)
            if suggestions2:
                chosen = st.selectbox("Autocompletar", ["(mantener) "+ticker_input] + suggestions2, index=0)
                if chosen and not chosen.startswith("(mantener)"):
                    ticker = chosen

    st.markdown(f"**Ticker seleccionado:** `{ticker}`")

    # Range/periodo
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

    # FAVORITOS (sidebar)
    st.sidebar.markdown("### ⭐ Favoritos (FREE)")
    st.sidebar.caption("Máximo 5 → Para más: versión PRO")
    username = st.session_state.get("username", "demo")
    favs = load_favorites(username)
    # adaptarse al formato (core.favorites puede devolver lista o dict)
    if isinstance(favs, dict):
        fav_list = favs.get("all", [])
    else:
        fav_list = favs or []

    MAX_FAVS = 5
    if st.sidebar.button("Agregar ticker a Favoritos"):
        tu = ticker.upper()
        if tu in fav_list:
            st.sidebar.warning("El ticker ya está en favoritos.")
        elif len(fav_list) >= MAX_FAVS:
            st.sidebar.error("Límite alcanzado (5). Versión PRO disponible.")
        else:
            # add_favorite espera (username, item) según core/favorites.py anterior
            try:
                add_favorite(username, tu)
                st.sidebar.success(f"{tu} agregado.")
                # reload
                favs = load_favorites(username)
                fav_list = favs if not isinstance(favs, dict) else favs.get("all", [])
            except Exception:
                st.sidebar.error("No se pudo agregar a favoritos (revisar permisos).")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tus favoritos")
    if fav_list:
        for f in fav_list:
            st.sidebar.write(f"• {f}")
    else:
        st.sidebar.info("No tenés favoritos guardados.")

    # -----------------------------
    # Fetch OHLC (core.fetch_ohlc) y fallback demo
    # -----------------------------
    try:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    except Exception:
        df = pd.DataFrame()

    if df is None or (hasattr(df, "empty") and df.empty):
        # fallback demo synthetic series (30 días)
        st.info("No hay datos reales OHLC disponibles — mostrando demo sintético.")
        rng = pd.date_range(end=datetime.today(), periods=60)
        np.random.seed(42)
        base = np.linspace(100, 150, len(rng))
        noise = np.random.normal(0, 3, len(rng))
        close = base + noise
        open_ = close + np.random.normal(0, 1, len(rng))
        high = np.maximum(open_, close) + np.abs(np.random.normal(0, 2, len(rng)))
        low = np.minimum(open_, close) - np.abs(np.random.normal(0, 2, len(rng)))
        vol = np.random.randint(100000, 500000, len(rng))
        df = pd.DataFrame({"date": rng, "open": open_, "high": high, "low": low, "close": close, "volume": vol})
    # ensure date col dtype
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    else:
        df.reset_index(inplace=True)
        df.rename(columns={"index":"date"}, inplace=True)

    # indicadores
    try:
        df["SMA20"] = sma(df["close"], 20)
        df["SMA50"] = sma(df["close"], 50)
        df["EMA20"] = ema(df["close"], 20)
        df["RSI14"] = rsi(df["close"], 14)
    except Exception:
        # funciones utils podrían lanzar si series con NA; ignorar
        df["SMA20"] = df["close"].rolling(20).mean()
        df["SMA50"] = df["close"].rolling(50).mean()
        df["EMA20"] = df["close"].ewm(span=20).mean()
        df["RSI14"] = (df["close"].diff().fillna(0) > 0).rolling(14).mean() * 100

    # Candlestick
    st.subheader("📈 Precio histórico")
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], name=ticker
    )])
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
    fig.update_layout(height=520, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # RSI simple plot
    st.subheader("📊 RSI 14")
    rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
    rsi_fig.update_layout(height=200, template="plotly_dark")
    st.plotly_chart(rsi_fig, use_container_width=True)

    # -----------------------------
    # Overview / Fundamentals / Competitors
    # -----------------------------
    st.subheader("📘 Overview General del Activo")
    # build_overview en core.overview existe (según tu repo anterior) y acepta lang opcional
    try:
        overview = build_overview(ticker, lang=lang_code)
    except TypeError:
        # si build_overview no acepta lang, llamar sin él
        overview = build_overview(ticker)

    # tarjeta visual compacta
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
        st.info("No hay overview estructurado. Mostrando fundamentos crudos abajo.")

    # Fundamentales (tabla)
    st.subheader("📂 Fundamentales Clave")
    fundamentals = overview.get("fundamentals") if isinstance(overview, dict) else None
    if fundamentals:
        try:
            st.dataframe(pd.DataFrame.from_dict(fundamentals, orient="index", columns=["Valor"]))
        except Exception:
            # si fundamentals ya es un dict sencillo
            st.json(fundamentals)
    else:
        st.info("No se encontraron fundamentales válidos.")

    # Competidores
    st.subheader("🏦 Competidores Reales (Industria / Sector / País)")
    competitors = overview.get("competitors") if isinstance(overview, dict) else None
    if competitors:
        # limitar a 5 y mostrar
        if isinstance(competitors, list):
            st.write(", ".join([str(c) for c in competitors[:5]]))
        else:
            st.json(competitors)
    else:
        st.info("No se encontraron competidores.")

    # -----------------------------
    # Noticias + Sentimiento por headline
    # -----------------------------
    st.subheader("📰 Noticias y Sentimiento")
    try:
        news_items = overview.get("news") if isinstance(overview, dict) else fetch_news(ticker)
    except Exception:
        news_items = fetch_news(ticker)

    if news_items:
        sentiment_points = []
        for n in news_items[:10]:
            title = n.get("title", "")
            published = n.get("published_at", n.get("pubDate",""))
            score, label = analyze_sentiment_textblob(title + " " + n.get("content","")[:500])
            sentiment_points.append({"date": published, "sentiment": score, "label": label, "title": title})
            # mostrar línea con idioma
            if lang_code == "es":
                st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
            else:
                st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")

        # gráfico de barras simplificado
        sdf = pd.DataFrame(sentiment_points)
        if not sdf.empty:
            colors = sdf['sentiment'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
            fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['sentiment'], marker_color=colors))
            fig_s.update_layout(title="Sentimiento de noticias", template="plotly_dark", xaxis_tickangle=-45, height=320)
            st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("No hay noticias disponibles.")

    # -----------------------------
    # ETF Finder
    # -----------------------------
    st.subheader("📈 ETF Finder (Temático)")
    tema = st.text_input("Tema (ej: AI, Energy, Metals)")
    if tema:
        try:
            etfs = etf_screener(tema)
            if etfs:
                st.write(etfs)
            else:
                st.info("No se encontraron ETFs temáticos.")
        except Exception:
            st.info("ETF Finder no disponible en esta instalación.")

    # -----------------------------
    # Comparación PRO (2 tickers)
    # -----------------------------
    st.subheader("⚔️ Comparación entre dos tickers (FREE)")
    t2 = st.text_input("Ticker a comparar", "AAPL")
    if t2:
        try:
            st.json(compare_indicators(ticker, t2))
            st.json(compare_sentiment(ticker, t2))
        except Exception as e:
            st.info("Comparación no disponible (revisar logs).")

    # Fin de show_dashboard


