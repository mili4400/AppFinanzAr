# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ================================
# Demo data
# ================================
DEMO_TICKERS = ["MSFT.US", "AAPL.US", "GOOGL.US", "AMZN.US", "GGAL.BA"]

DEMO_OVERVIEW = {
    "MSFT.US": {
        "executive_summary": {"name":"Microsoft Corp","sector":"Technology","industry":"Software","country":"USA",
                              "valuation":{"pe_ratio":32.5,"market_cap":"2.5T","eps":8.5},"price_trend_30d":4.2},
        "fundamentals":{"Revenue":"168B","Net Income":"61B","ROE":"40%","Debt/Equity":"0.7"},
        "competitors":["AAPL.US","GOOGL.US","ORCL.US","IBM.US","ADBE.US"],
        "news":[{"title":"Microsoft reports strong Q4 earnings","published_at":"2025-11-30"},
                {"title":"Azure revenue grows 35%","published_at":"2025-11-28"}],
        "sentiment_label":"positive",
        "fundamentals_summary":"Microsoft sigue creciendo y dominando el mercado de software y cloud."
    },
    "AAPL.US": {
        "executive_summary":{"name":"Apple Inc","sector":"Technology","industry":"Consumer Electronics","country":"USA",
                             "valuation":{"pe_ratio":28.3,"market_cap":"3.0T","eps":7.2},"price_trend_30d":2.8},
        "fundamentals":{"Revenue":"394B","Net Income":"100B","ROE":"50%","Debt/Equity":"1.2"},
        "competitors":["MSFT.US","GOOGL.US","SAMSUNG.KR","SONY.JP","HPQ.US"],
        "news":[{"title":"Apple launches new MacBook Pro","published_at":"2025-11-29"},
                {"title":"iPhone sales hit record high","published_at":"2025-11-27"}],
        "sentiment_label":"positive",
        "fundamentals_summary":"Apple mantiene fuerte presencia en hardware y servicios digitales."
    },
    # resto de tickers...
}

# ================================
# Utilities
# ================================
def sentiment_score(text):
    t = (text or "").lower()
    if "up" in t or "grow" in t or "strong" in t:
        return 0.6
    if "down" in t or "decline" in t or "weak" in t:
        return -0.6
    return 0.0

def analyze_sentiment_textblob(text):
    score = sentiment_score(text)
    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return score, label

def fetch_demo_ohlc(ticker):
    idx = pd.date_range(end=datetime.today(), periods=60)
    prices = 100 + np.cumsum(np.random.randn(len(idx)))
    df = pd.DataFrame({"date":idx,"open":prices-1,"high":prices+1,"low":prices-2,"close":prices,"volume":1000})
    df["SMA20"] = df["close"].rolling(20).mean()
    df["SMA50"] = df["close"].rolling(50).mean()
    df["EMA20"] = df["close"].ewm(span=20).mean()
    delta = df["close"].diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = -delta.clip(upper=0).rolling(14).mean()
    rs = up / down
    df["RSI14"] = 100 - (100 / (1 + rs))
    return df

def etf_screener_demo(theme=None):
    return [{"ETF":"TECH_ETF","Price":"150"},{"ETF":"CLOUD_ETF","Price":"120"}] if theme else []

def compare_indicators_demo(a,b):
    return {a:{"P/E":30,"ROE":"40%"}, b:{"P/E":28,"ROE":"35%"}}

def compare_sentiment_demo(a,b):
    return {a:"positive",b:"neutral"}

# ================================
# DASHBOARD PRO DEMO
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr PRO Demo", layout="wide")
    st.title("📊 AppFinanzAr – PRO Demo")

    # Session state init
    if "favorites_list" not in st.session_state:
        st.session_state["favorites_list"] = []

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español", "English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username", "demo")
        st.write(f"Usuario: **{username}**")

        st.markdown("**Favoritos**")
        if st.session_state["favorites_list"]:
            for idx,f in enumerate(st.session_state["favorites_list"]):
                col1,col2 = st.columns([4,1])
                with col1: st.write(f"• {f}")
                with col2:
                    if st.button("❌",key=f"del_{idx}"): st.session_state["favorites_list"].pop(idx)
        else:
            st.write("_Sin favoritos_")

        if st.button("🗑️ Borrar todos los favoritos"):
            st.session_state["favorites_list"] = []

        st.markdown("---")
        st.markdown("### Demo / Utilities")
        if st.button("Cargar ejemplo demo"):
            st.session_state["dash_demo_ticker"] = DEMO_TICKERS[0]
            st.session_state["dash_demo_mode"] = True

    # Top controls
    st.subheader("Búsqueda de activo")
    col1,col2 = st.columns([2,1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state.get("dash_demo_ticker","MSFT.US"), key="ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa (opcional)", "")

    ticker = ticker_input
    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", DEMO_TICKERS)
        if sel: ticker = sel

    # Agregar a favoritos
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar este ticker a favoritos"):
        if ticker not in st.session_state["favorites_list"]:
            st.session_state["favorites_list"].append(ticker)
            st.success(f"{ticker} agregado a favoritos.")

    # Date range
    st.markdown("---")
    st.subheader("Rango de datos")
    range_days = st.selectbox("Rango rápido", ["1m","3m","6m","1y","5y","max"], index=0)
    custom_range = st.checkbox("Usar rango personalizado")
    if custom_range:
        start_date = st.date_input("Inicio", datetime.today() - timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        mapping = {"1m":30,"3m":90,"6m":180,"1y":365,"5y":365*5,"max":365*10}
        today = datetime.today().date()
        start_date = today - timedelta(days=mapping[range_days])
        end_date = today

    st.markdown(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")

    # Datos demo
    df = fetch_demo_ohlc(ticker)
    overview = DEMO_OVERVIEW.get(ticker, DEMO_OVERVIEW["MSFT.US"])

    # Gráfico precios
    st.subheader("Gráfico de precios")
    fig = go.Figure(data=[go.Candlestick(x=df["date"],open=df["open"],high=df["high"],low=df["low"],close=df["close"])])
    for col in ["SMA20","SMA50","EMA20"]: 
        if col in df.columns: fig.add_trace(go.Scatter(x=df["date"],y=df[col],mode="lines",name=col))
    fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
    st.plotly_chart(fig,use_container_width=True)

    # RSI
    st.subheader("RSI 14")
    rsi_fig = go.Figure(go.Scatter(x=df["date"],y=df["RSI14"],name="RSI 14"))
    rsi_fig.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
    st.plotly_chart(rsi_fig,use_container_width=True)

    # Executive Summary
    st.subheader("Resumen ejecutivo")
    exec_sum = overview["executive_summary"]
    card = f"""
**{exec_sum['name']}**  
Sector: {exec_sum['sector']} • Industria: {exec_sum['industry']} • País: {exec_sum['country']}
Valuación: P/E {exec_sum['valuation']['pe_ratio']} — Market Cap {exec_sum['valuation']['market_cap']} — EPS {exec_sum['valuation']['eps']}
Tendencia 30d: {exec_sum['price_trend_30d']}% • Sentimiento: {overview['sentiment_label']}
Resumen: {overview['fundamentals_summary']}
"""
    st.markdown(card)

    # Fundamentales
    st.subheader("Fundamentales (clave)")
    st.dataframe(pd.DataFrame.from_dict(overview["fundamentals"],orient="index",columns=["Valor"]))

    # Competidores
    st.subheader("Competidores (máx 5)")
    st.write(", ".join(overview["competitors"][:5]))

    # Noticias
    st.subheader("Noticias recientes (y sentimiento)")
    simple=[]
    for n in overview["news"]:
        title=n["title"]; published=n["published_at"]
        score,label=analyze_sentiment_textblob(title)
        simple.append({"title":title,"date":published,"score":score,"label":label})
        st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
    sdf=pd.DataFrame(simple)
    colors=sdf['score'].apply(lambda x:"green" if x>0 else "red" if x<0 else "gray")
    fig_s=go.Figure(go.Bar(x=sdf['title'],y=sdf['score'],marker_color=colors))
    fig_s.update_layout(title="Sentimiento de noticias",template="plotly_dark",xaxis_tickangle=-45,height=300)
    st.plotly_chart(fig_s,use_container_width=True)

    # -----------------------------
    # ETF Finder demo
    # -----------------------------
    st.subheader("ETF Finder (temas)")
    tema=st.text_input("Buscar ETFs por tema (ej: energy, tech)", key="etf_theme")
    if st.button("Buscar ETFs"):
        etfs=etf_screener_demo(tema)
        if etfs: st.table(pd.DataFrame(etfs))
        else: st.info("No se encontraron ETFs para ese tema.")

    # Comparación rápida
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB = st.columns(2)
    with colA: t_a=st.text_input("Ticker A",ticker,key="cmp_a")
    with colB: t_b=st.text_input("Ticker B","AAPL.US",key="cmp_b")
    if st.button("Comparar ahora"):
        cmp=compare_indicators_demo(t_a,t_b)
        sent=compare_sentiment_demo(t_a,t_b)
        st.markdown("**Indicadores (objeto):**")
        st.write(cmp)
        st.markdown("**Sentimiento:**")
        st.write(sent)

    st.markdown("---")
    st.info("Mostrando datos demo completos. Para datos reales, configurar API key.")
    st.caption("AppFinanzAr PRO Demo — contacto: desarrollador para activar funcionalidades completas.")
