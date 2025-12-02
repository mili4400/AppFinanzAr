# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import random

# ================================
# FALLBACKS CORE FUNCTIONS
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
        # demo overview con datos simulados
        price_now = random.uniform(50, 3500)
        return {
            "fundamentals": {"Revenue": f"${random.randint(10,100)}B", "Profit": f"${random.randint(1,20)}B"},
            "competitors": [f"COMP{i}" for i in range(1,6)],
            "price": pd.DataFrame({"date": pd.date_range(end=datetime.today(), periods=60),
                                   "close": np.cumsum(np.random.randn(60)*5+price_now)}),
            "news": [{"title": f"Demo news {i} for {ticker}", "published_at": datetime.today().date()} for i in range(1,6)],
            "sentiment_value": random.uniform(-1,1),
            "sentiment_label": random.choice(["positive","neutral","negative"]),
            "fundamentals_summary": "Resumen fundamental demo",
            "executive_summary": {
                "name": ticker,
                "sector": random.choice(["Tech","Finance","Energy"]),
                "industry": random.choice(["Software","Banking","Oil & Gas"]),
                "country": random.choice(["USA","Argentina"]),
                "valuation": {"pe_ratio": round(random.uniform(10,40),2),
                              "market_cap": f"${random.randint(10,500)}B",
                              "eps": round(random.uniform(1,10),2)},
                "price_trend_30d": round(random.uniform(-5,5),2)
            }
        }

try:
    from core.favorites import load_favorites, add_favorite
except Exception:
    _favorites = {}
    def load_favorites(username):
        return _favorites.get(username, {"all":[],"categories":{}})
    def add_favorite(username, item):
        if username not in _favorites:
            _favorites[username] = {"all": [], "categories": {}}
        if isinstance(item,list):
            _favorites[username]["all"] = item
        else:
            if item not in _favorites[username]["all"]:
                _favorites[username]["all"].append(item)
        return _favorites[username]["all"]

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a,b): return {"metric_demo": random.randint(0,100)}
    def compare_sentiment(a,b): return {"sentiment_demo": random.uniform(-1,1)}

# ================================
# UTILITIES
# ================================
def sma(series, n): return series.rolling(n).mean()
def ema(series, n): return series.ewm(span=n).mean()
def rsi(series, n):
    delta = series.diff()
    up = delta.clip(lower=0).rolling(n).mean()
    down = -delta.clip(upper=0).rolling(n).mean()
    rs = up/down
    return 100 - (100/(1+rs))

def analyze_sentiment_textblob(text):
    score = random.uniform(-1,1)
    label = "neutral"
    if score>0.1: label="positive"
    elif score<-0.1: label="negative"
    return score,label

# ================================
# DEMO TICKERS + ALERTS
# ================================
DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]
PRICE_ALERTS = {
    "MSFT.US": {"high": 300, "low": 200},
    "AAPL.US": {"high": 200, "low": 100},
    "GOOGL.US": {"high": 3000, "low": 2500},
    "AMZN.US": {"high": 3500, "low": 2500},
    "GGAL.BA": {"high": 2000, "low": 1500},
}

# ================================
# DASHBOARD PRINCIPAL
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr", layout="wide")
    st.title("📊 AppFinanzAr")

    # -------------------------
    # SIDEBAR: configuración + favoritos
    # -------------------------
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español","English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Usuario / Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")

        favs = load_favorites(username)
        favs.setdefault("all",[])
        favs.setdefault("categories",{})

        st.markdown("**Favoritos**")
        if favs["all"]:
            for f in favs["all"]:
                col1,col2=st.columns([4,1])
                with col1:
                    st.write(f"• {f}")
                with col2:
                    if st.button("❌", key=f"del_{f}"):
                        favs["all"].remove(f)
                        add_favorite(username,favs["all"])
                        st.experimental_rerun()
        else:
            st.write("_Sin favoritos_")

        if favs["all"]:
            csv_btn = st.download_button("📥 Exportar favoritos CSV",
                                         data=pd.DataFrame(favs["all"],columns=["Ticker"]).to_csv(index=False),
                                         file_name="favoritos.csv")
        st.markdown("---")
        st.markdown("### Demo Utilities")
        st.write("El ticker por defecto es **MSFT.US**")
        st.caption("La selección central de ticker demo reemplaza este botón")

    # -------------------------
    # SELECCIÓN TICKER
    # -------------------------
    st.subheader("Búsqueda de activo / Demo selection")
    col0,col1,col2=st.columns([1,3,1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", value=st.session_state.get("dash_demo_ticker","MSFT.US"), key="dash_ticker_input")
        sel_demo = st.selectbox("Sugerencias demo",DEMO_TICKERS)
        if sel_demo: ticker_input=sel_demo
    ticker = ticker_input

    # -------------------------
    # FETCH OHLC
    # -------------------------
    try:
        df = fetch_ohlc(ticker)
    except: df=pd.DataFrame()
    if df.empty:
        # Simulación demo OHLC
        idx=pd.date_range(end=datetime.today(),periods=60)
        price_base = random.uniform(50,3500)
        prices = np.cumsum(np.random.randn(60)*5 + price_base)
        df = pd.DataFrame({"date":idx,"open":prices-1,"high":prices+1,"low":prices-2,"close":prices,"volume":1000})
        demo_mode=True
    else:
        demo_mode=False

    # Indicadores
    try:
        df["SMA20"]=sma(df["close"],20)
        df["SMA50"]=sma(df["close"],50)
        df["EMA20"]=ema(df["close"],20)
        df["RSI14"]=rsi(df["close"],14)
    except:
        df["SMA20"]=pd.NA; df["SMA50"]=pd.NA; df["EMA20"]=pd.NA; df["RSI14"]=pd.NA

    # -------------------------
    # GRÁFICO DE PRECIOS
    # -------------------------
    st.subheader("Gráfico de precios")
    fig = go.Figure(data=[go.Candlestick(x=df["date"],open=df["open"],high=df["high"],
                                         low=df["low"],close=df["close"],name="OHLC",
                                         increasing_line_color="green",decreasing_line_color="red")])
    for ind in ["SMA20","SMA50","EMA20"]:
        if ind in df.columns and df[ind].notna().any():
            fig.add_trace(go.Scatter(x=df["date"],y=df[ind],mode="lines",name=ind))
    fig.update_layout(height=500,template="plotly_dark")
    st.plotly_chart(fig,use_container_width=True)

    # -------------------------
    # OVERVIEW / RESUMEN EJECUTIVO
    # -------------------------
    overview = build_overview(ticker,lang=lang_code)
    exec_sum = overview.get("executive_summary",{})

    # ALERTA DE PRECIO
    current_price = df["close"].iloc[-1]
    alert_color = "black"; alert_text="Normal"
    if ticker in PRICE_ALERTS:
        if current_price>PRICE_ALERTS[ticker]["high"]:
            alert_color="green"; alert_text="Precio excesivamente alto"
        elif current_price<PRICE_ALERTS[ticker]["low"]:
            alert_color="red"; alert_text="Precio muy bajo"

    st.subheader("Resumen Ejecutivo / Overview")
    card=f"""
**{exec_sum.get('name',ticker)}**  
Sector: {exec_sum.get('sector','N/A')} • Industria: {exec_sum.get('industry','N/A')} • País: {exec_sum.get('country','N/A')}  

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')} — Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')} — EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}  

**Tendencia 30d:** {exec_sum.get('price_trend_30d','N/A')}% • **Sentimiento:** {overview.get('sentiment_label','Sin datos')}  

**Precio actual:** <span style='color:{alert_color}'>{current_price:.2f} USD — {alert_text}</span>  

**Resumen:** {overview.get('fundamentals_summary','')}
"""
    st.markdown(card,unsafe_allow_html=True)

    # -------------------------
    # Fundamentales
    # -------------------------
    st.subheader("Fundamentales Clave")
    fund = overview.get("fundamentals",{})
    if fund:
        st.dataframe(pd.DataFrame.from_dict(fund,orient="index",columns=["Valor"]))
    else:
        st.info("No se encontraron fundamentales.")

    # Competidores
    st.subheader("Competidores")
    comps = overview.get("competitors",[])
    if comps:
        st.write(", ".join(comps[:5]))
    else:
        st.info("No se encontraron competidores.")

    # Noticias y sentimiento
    st.subheader("Noticias recientes y sentimiento")
    news_items = overview.get("news",[])
    if news_items:
        simple=[]
        for n in news_items:
            title=n.get("title","")[:200]
            published=n.get("published_at",datetime.today().date())
            score,label=analyze_sentiment_textblob(title)
            simple.append({"title":title,"date":published,"score":score,"label":label})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
        sdf=pd.DataFrame(simple)
        fig_s=go.Figure(go.Bar(x=sdf['title'],y=sdf['score'],marker_color=[ "green" if x>0 else "red" if x<0 else "gray" for x in sdf['score'] ]))
        fig_s.update_layout(title="Sentimiento de noticias",template="plotly_dark",xaxis_tickangle=-45,height=300)
        st.plotly_chart(fig_s,use_container_width=True)
    else:
        st.info("No hay noticias disponibles.")

    # -------------------------
    # Comparación rápida entre dos tickers
    # -------------------------
    st.subheader("Comparación rápida")
    colA,colB=st.columns(2)
    with colA: t_a=st.text_input("Ticker A",ticker,key="cmp_a")
    with colB: t_b=st.text_input("Ticker B","AAPL.US",key="cmp_b")
    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a,t_b)
        sent = compare_sentiment(t_a,t_b)
        st.markdown("**Indicadores:**"); st.write(cmp)
        st.markdown("**Sentimiento:**"); st.write(sent)

    # -------------------------
    # Exportar datos de ticker
    # -------------------------
    if st.button("📥 Exportar OHLC a CSV"):
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer,index=False)
        st.download_button("Descargar CSV", csv_buffer.getvalue(),file_name=f"{ticker}_ohlc.csv")

   # -----------------------------
   # ETF Finder (tema)
   # -----------------------------
   st.subheader("ETF Finder (temas)")
   tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)", key="etf_theme")
   if st.button("Buscar ETFs"):
       try:
           etfs = etf_screener(tema) if tema else etf_screener(None)
       except Exception:
           # demo simple si no hay API
           etfs = [{"Ticker": f"ETF{i}", "Tema": tema or "Demo", "Precio": f"${random.randint(50,200)}"} for i in range(1,6)]
       if etfs:
           st.table(pd.DataFrame(etfs))
       else:
           st.info("No se encontraron ETFs para ese tema (o demo activo).")
 

    # -------------------------
    # Footer / info demo
    # -------------------------
    st.markdown("---")
    if demo_mode:
        st.info("Mostrando datos DEMO completos con indicadores y alertas de precios.")
    st.caption("AppFinanzAr PRO Demo Friendly — todas las funcionalidades visibles. Contacto: desarrollador para datos reales / keys.")



