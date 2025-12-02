# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta

# ================================
# FALLBACKS (si core no existe)
# ================================
try:
    from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
except Exception:
    def fetch_ohlc(ticker, from_date=None, to_date=None):
        return pd.DataFrame()
    def fetch_fundamentals(ticker):
        return {}, []
    def fetch_news(ticker, days_back=30, translate_to_es=True):
        return []
    def search_ticker_by_name(name, max_results=10):
        return []

try:
    from core.overview import build_overview
except Exception:
    def build_overview(ticker, lang="es"):
        return {
            "fundamentals": {"Revenue":"1000M","Profit":"200M"},
            "competitors":["COMP1","COMP2","COMP3"],
            "price": pd.DataFrame({"date": pd.date_range(end=datetime.today(), periods=30),
                                   "close": np.random.randn(30)*10+100}),
            "news":[{"title":"Demo news positive","published_at":str(datetime.today())}],
            "sentiment_label":"Neutral",
            "fundamentals_summary":"Demo summary",
            "executive_summary":{
                "name": ticker,
                "sector":"Technology",
                "industry":"Software",
                "country":"USA",
                "valuation":{"pe_ratio":25,"market_cap":"1T","eps":5},
                "price_trend_30d": np.random.uniform(-5,5)
            }
        }

try:
    from core.etf_finder import etf_screener
except Exception:
    def etf_screener(theme):
        return [{"ETF":"TECHETF","Theme":theme or "General"}]

try:
    from core.favorites import load_favorites, add_favorite
except Exception:
    def load_favorites(username):
        return {"all":[],"categories":{}}
    def add_favorite(username, favs):
        return favs

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a,b): return {"DemoIndicatorA":1,"DemoIndicatorB":2}
    def compare_sentiment(a,b): return {"sentimentA":0.1,"sentimentB":-0.2}

try:
    from core.utils import sma, ema, rsi
except Exception:
    def sma(s,n): return s.rolling(n).mean()
    def ema(s,n): return s.ewm(span=n).mean()
    def rsi(s,n):
        delta = s.diff()
        up = delta.clip(lower=0).rolling(n).mean()
        down = -delta.clip(upper=0).rolling(n).mean()
        rs = up/down
        return 100-(100/(1+rs))

try:
    from core.sentiment_model import sentiment_score
except Exception:
    def sentiment_score(text):
        t = (text or "").lower()
        if "up" in t or "positivo" in t: return 0.6
        if "down" in t or "negativo" in t: return -0.6
        return 0.0

# ================================
# Demo tickers y alertas
# ================================
DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]
PRICE_ALERTS = {
    "MSFT.US":("Excesivamente alto","green"),
    "GGAL.BA":("Muy bajo","red")
}

# ================================
# Dashboard principal
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr", layout="wide")
    st.title("📊 AppFinanzAr")

    # ================================
    # Sidebar: idioma, usuario, favoritos + export
    # ================================
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español","English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")

        if "favorites" not in st.session_state:
            st.session_state["favorites"] = load_favorites(username)["all"]

        # Favoritos con alertas visuales
        for f in st.session_state["favorites"].copy():
            label, color = PRICE_ALERTS.get(f, ("", None))
            display_text = f"{f} {'⚠️ '+label if label else ''}"
            col1,col2 = st.columns([4,1])
            with col1:
                st.markdown(f"• <span style='color:{color or 'black'}'>{display_text}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("❌", key=f"del_{f}"):
                    st.session_state["favorites"].remove(f)
                    add_favorite(username, st.session_state["favorites"])
                    st.success(f"{f} eliminado de favoritos")

        if st.button("🗑️ Borrar todos los favoritos"):
            st.session_state["favorites"]=[]
            add_favorite(username,[])
            st.success("Todos los favoritos borrados")

        # Exportar favoritos
        if st.session_state["favorites"]:
            csv_buffer = io.StringIO()
            pd.DataFrame(st.session_state["favorites"],columns=["Ticker"]).to_csv(csv_buffer,index=False)
            st.download_button("Exportar CSV", csv_buffer.getvalue(), file_name="favoritos.csv")

        st.markdown("---")
        st.subheader("Buscar ticker por empresa")
        company_search = st.text_input("Nombre empresa", "")
        search_results = []
        if company_search:
            search_results = search_ticker_by_name(company_search)
            if search_results:
                st.selectbox(f"Resultados para '{company_search}'", search_results)

    # ================================
    # Selección ticker central
    # ================================
    st.subheader("Búsqueda de activo / Demo selection")
    col1,col2 = st.columns([2,1])
    if "dash_demo_ticker" not in st.session_state:
        st.session_state["dash_demo_ticker"] = "MSFT.US"

    with col1:
        ticker_input = st.text_input("Ticker", st.session_state.get("dash_demo_ticker"))
    with col2:
        company_search_central = st.text_input("Buscar por empresa (central)")

    # Buscar ticker
    ticker = ticker_input or st.session_state.get("dash_demo_ticker")
    if company_search_central:
        results = search_ticker_by_name(company_search_central)
        if results:
            ticker = st.selectbox(f"Resultados para '{company_search_central}'", results, index=0)
            st.session_state["dash_demo_ticker"] = ticker
        else:
            st.warning("No se encontraron tickers")

    # Demo selector central
    st.markdown("### 🎯 Demo Tickers")
    sel_demo = st.selectbox("Elegir demo ticker", DEMO_TICKERS)
    if sel_demo:
        ticker = sel_demo
        st.session_state["dash_demo_ticker"] = sel_demo

    # ================================
    # Agregar a favoritos en tiempo real
    # ================================
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar a favoritos"):
        if ticker not in st.session_state["favorites"]:
            st.session_state["favorites"].append(ticker)
            add_favorite(username, st.session_state["favorites"])
            st.success(f"{ticker} agregado a favoritos")

    # ================================
    # Simulación de rango de fechas
    # ================================
    st.markdown("---")
    st.subheader("Rango de datos")
    range_days = st.selectbox("Rango rápido", ["1m","3m","6m","1y","5y","max"], index=0)
    today = datetime.today().date()
    mapping = {"1m":30,"3m":90,"6m":180,"1y":365,"5y":365*5,"max":365*10}
    start_date = today - timedelta(days=mapping[range_days])
    end_date = today

    # ================================
    # Fetch OHLC demo
    # ================================
    df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    if df is None or df.empty:
        idx = pd.date_range(end=datetime.today(), periods=60)
        prices = 100 + np.cumsum(np.random.randn(len(idx)))
        df = pd.DataFrame({"date": idx,"open":prices-1,"high":prices+1,"low":prices-2,"close":prices,"volume":1000})

    df["SMA20"]=sma(df["close"],20)
    df["SMA50"]=sma(df["close"],50)
    df["EMA20"]=ema(df["close"],20)
    df["RSI14"]=rsi(df["close"],14)

    # ================================
    # Gráfico OHLC + indicadores
    # ================================
    st.subheader("📈 Gráfico de precios")
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"]
    )])
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
    st.plotly_chart(fig,use_container_width=True)

    # ================================
    # Overview / Resumen ejecutivo
    # ================================
    overview = build_overview(ticker, lang=lang_code)
    exec_sum = overview.get("executive_summary",{})
    trend_30d = exec_sum.get("price_trend_30d",0)
    alert_label,alert_color = PRICE_ALERTS.get(ticker,("",None))

    st.subheader("📋 Overview / Resumen Ejecutivo")
    st.markdown(f"""
**{exec_sum.get('name',ticker)}**  
Sector: {exec_sum.get('sector','N/A')}  •  Industria: {exec_sum.get('industry','N/A')}  •  País: {exec_sum.get('country','N/A')}

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')}  —  Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')}  —  EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}

**Tendencia 30d:** {trend_30d:.2f}%  
**Alerta precio:** {alert_label or 'N/A'}  
**Sentimiento:** {overview.get('sentiment_label','Sin datos')}

**Resumen:** {overview.get('fundamentals_summary','')}
""")

    # Fundamentales
    st.subheader("Fundamentales")
    fund = overview.get("fundamentals",{})
    if fund: st.dataframe(pd.DataFrame.from_dict(fund, orient="index", columns=["Valor"]))
    else: st.info("No se encontraron fundamentales")

    # Competidores
    st.subheader("Competidores")
    comps = overview.get("competitors",[])
    if comps: st.write(", ".join(comps[:5]))
    else: st.info("No se encontraron competidores")

    # Noticias + Sentimiento
    st.subheader("Noticias recientes y Sentimiento")
    news_items = overview.get("news",[])
    if not news_items:
        news_items = fetch_news(ticker) or []
    if news_items:
        simple=[]
        for n in news_items[:10]:
            title = n.get("title","")[:200]
            published = n.get("published_at",str(datetime.today()))
            score = sentiment_score(title)
            label = "positive" if score>0.1 else "negative" if score<-0.1 else "neutral"
            simple.append({"title":title,"date":published,"score":score,"label":label})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
        sdf = pd.DataFrame(simple)
        colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
        fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['score'], marker_color=colors))
        fig_s.update_layout(title="Sentimiento de noticias", template="plotly_dark", xaxis_tickangle=-45, height=300)
        st.plotly_chart(fig_s,use_container_width=True)
    else: st.info("No hay noticias")

    # ETF Finder
    st.subheader("ETF Finder")
    tema = st.text_input("Buscar ETFs por tema", key="etf_theme")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema) if tema else etf_screener(None)
        if etfs: st.table(pd.DataFrame(etfs))
        else: st.info("No se encontraron ETFs")

    # Comparación rápida 2 tickers
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB = st.columns(2)
    t_a = colA.text_input("Ticker A", ticker, key="cmp_a")
    t_b = colB.text_input("Ticker B", "AAPL.US", key="cmp_b")
    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a,t_b)
        sent = compare_sentiment(t_a,t_b)
        st.markdown("**Indicadores:**"); st.write(cmp)
        st.markdown("**Sentimiento:**"); st.write(sent)

    # Footer demo info
    st.markdown("---")
    st.caption("Modo demo: datos simulados / real solo con API key válida")

    




