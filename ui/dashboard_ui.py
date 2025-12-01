# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
from core.overview import build_overview
from core.compare import get_competitors
from core.etf_finder import etf_screener
from core.favorites import load_favorites, add_favorite
from core.compare_pro import compare_indicators, compare_sentiment
from core.utils import sma, ema, rsi
from core.sentiment import sentiment_score

# =============================
# FUNCIONES AUXILIARES
# =============================
def analyze_sentiment_textblob(text: str):
    score = sentiment_score(text)
    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return score, label

# =============================
# DASHBOARD PRINCIPAL
# =============================
def show_dashboard():
    st.title("📊 AppFinanzAr – Dashboard Completo")

    # -----------------------------
    # TICKER INPUT (búsqueda simple por nombre)
    # -----------------------------
    ticker_input = st.text_input("Ingrese ticker o empresa (ej: MSFT.US o Galicia)", "MSFT.US", key="dash_ticker")
    
    # Intentar autocomplete simple (fallback)
    tickers_suggestions = search_ticker_by_name(ticker_input) if ticker_input else []
    ticker = tickers_suggestions[0] if tickers_suggestions else ticker_input.upper()

    # -----------------------------
    # RANGO DE FECHAS
    # -----------------------------
    range_days = st.selectbox("Rango rápido", ["1m","3m","6m","1y","5y","max"], index=0)
    custom_range = st.checkbox("Usar rango personalizado")

    if custom_range:
        start_date = st.date_input("Inicio", datetime.today() - timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        today = datetime.today().date()
        mapping = {"1m":30, "3m":90, "6m":180, "1y":365, "5y":365*5, "max":365*10}
        start_date = today - timedelta(days=mapping[range_days])
        end_date = today

    # -----------------------------
    # FAVORITOS
    # -----------------------------
    st.sidebar.markdown("### ⭐ Favoritos (FREE)")
    st.sidebar.caption("Máximo 5 → Para más: versión PRO")
    username = st.session_state.get("username", "demo")
    favs = load_favorites(username)
    favs = favs if isinstance(favs, dict) else {"all": favs, "categories": {}}
    MAX_FAVS = 5

    if st.sidebar.button("Agregar ticker a Favoritos"):
        tu = ticker.upper()
        if tu in favs['all']:
            st.sidebar.warning("El ticker ya está en favoritos.")
        elif len(favs['all']) >= MAX_FAVS:
            st.sidebar.error("Límite alcanzado (5). Versión PRO disponible.")
        else:
            add_favorite(username, tu)
            st.sidebar.success(f"{tu} agregado.")
            favs = load_favorites(username)

    # Mostrar favoritos por categoría
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📂 Categorías")
    for cat, items in favs.get('categories', {}).items():
        if items:
            st.sidebar.markdown(f"**{cat.capitalize()}:**")
            for i in items:
                st.sidebar.write(f"• {i}")
    st.sidebar.markdown("---")

    # -----------------------------
    # CARGA OHLC
    # -----------------------------
    if ticker:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
        if df.empty:
            st.error("No hay datos OHLC disponibles.")
            return

        df["SMA20"] = sma(df["close"], 20)
        df["SMA50"] = sma(df["close"], 50)
        df["EMA20"] = ema(df["close"], 20)
        df["RSI14"] = rsi(df["close"], 14)

        # GRÁFICO VELAS
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]
        )])
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
        fig.update_layout(height=600, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # GRÁFICO RSI
        rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
        rsi_fig.update_layout(height=200, template="plotly_dark")
        st.plotly_chart(rsi_fig, use_container_width=True)

        # -----------------------------
        # OVERVIEW + FUNDAMENTALES
        # -----------------------------
        st.subheader("📘 Overview General del Activo")
        overview = build_overview(ticker)
        st.write(overview.get("fundamentals_summary","Sin datos"))

        st.subheader("📂 Fundamentales Clave")
        fund_df = pd.DataFrame.from_dict(overview.get("fundamentals", {}), orient="index", columns=["Valor"])
        if not fund_df.empty:
            st.dataframe(fund_df)
        else:
            st.info("No se encontraron fundamentales válidos.")

        # -----------------------------
        # COMPETIDORES
        # -----------------------------
        st.subheader("🏦 Competidores Reales")
        competitors = overview.get("competitors", [])
        if competitors:
            st.write(", ".join(competitors))
        else:
            st.info("No se encontraron competidores.")

        # -----------------------------
        # NOTICIAS + SENTIMIENTO
        # -----------------------------
        st.subheader("📰 Noticias y Sentimiento")
        news_items = overview.get("news", [])
        if news_items:
            sentiment_points = []
            for n in news_items[:10]:
                title = n.get("title", "")
                published = n.get("published_at", "")
                polarity, label = analyze_sentiment_textblob(title)
                sentiment_points.append({
                    "date": published,
                    "sentiment": polarity,
                    "label": label,
                    "title": title
                })
                st.write(f"- **{title}** ({published}) → *{label}* ({polarity:.2f})")

            # GRÁFICO DE SENTIMIENTO
            sdf = pd.DataFrame(sentiment_points)
            if not sdf.empty:
                fig_s = go.Figure(go.Scatter(
                    x=sdf['date'], y=sdf['sentiment'], mode="lines+markers",
                    marker=dict(color=sdf['sentiment'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray"))
                ))
                fig_s.update_layout(title="Sentimiento en el tiempo", template="plotly_dark")
                st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("No hay noticias disponibles.")

        # -----------------------------
        # ETF FINDER
        # -----------------------------
        st.subheader("📈 ETF Finder (Temático)")
        tema = st.text_input("Tema (ej: AI, Energy, Metals)")
        if tema:
            etfs = etf_screener(tema)
            if etfs:
                st.write(etfs)
            else:
                st.info("No se encontraron ETFs temáticos.")

        # -----------------------------
        # COMPARACIÓN PRO (2 TICKERS)
        # -----------------------------
        st.subheader("⚔️ Comparación entre dos tickers (FREE)")
        t2 = st.text_input("Ticker a comparar", "AAPL.US")
        if t2:
            st.write(compare_indicators(ticker, t2))
            st.write(compare_sentiment(ticker, t2))
