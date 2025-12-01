# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io

# -----------------------------
# FALLBACKS / DEMO DATA
# -----------------------------
try:
    from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
except:
    def fetch_ohlc(ticker, from_date=None, to_date=None):
        idx = pd.date_range(end=datetime.today(), periods=60, freq='D')
        prices = 100 + np.cumsum(np.random.randn(len(idx)))
        return pd.DataFrame({"date": idx, "open": prices-1, "high": prices+1, "low": prices-2, "close": prices, "volume": 1000})

    def fetch_fundamentals(ticker):
        return {"Revenue": "$10B", "Net Income": "$2B", "EPS": "5.2"}, []

    def fetch_news(ticker, days_back=30, translate_to_es=True):
        titles = [
            f"{ticker} sube tras resultados positivos",
            f"Análisis del mercado: impacto de {ticker}",
            f"Noticias sobre {ticker} y su competencia",
            f"Actualización financiera de {ticker}",
            f"{ticker} anuncia nueva estrategia"
        ]
        return [{"title": t, "published_at": (datetime.today()-timedelta(days=i)).strftime("%Y-%m-%d")} for i,t in enumerate(titles)]

    def search_ticker_by_name(name, max_results=10):
        mapping = {"Microsoft":"MSFT.US","Apple":"AAPL.US","Google":"GOOGL.US","Amazon":"AMZN.US","Galicia":"GGAL.BA"}
        return [v for k,v in mapping.items() if name.lower() in k.lower()]

try:
    from core.overview import build_overview
except:
    def build_overview(ticker, lang="es"):
        summaries = {
            "MSFT.US": {"sector":"Tech","industry":"Software","country":"USA"},
            "AAPL.US": {"sector":"Tech","industry":"Hardware","country":"USA"},
            "GOOGL.US": {"sector":"Tech","industry":"Internet","country":"USA"},
            "AMZN.US": {"sector":"Tech","industry":"E-commerce","country":"USA"},
            "GGAL.BA": {"sector":"Finance","industry":"Banking","country":"Argentina"}
        }
        base = summaries.get(ticker, {"sector":"N/A","industry":"N/A","country":"N/A"})
        return {
            "fundamentals":{"Revenue":"$10B","Net Income":"$2B","EPS":"5.2"},
            "competitors":["COMP1","COMP2","COMP3"],
            "price": fetch_ohlc(ticker),
            "news": fetch_news(ticker),
            "sentiment_value": 0.3,
            "sentiment_label": "Positivo",
            "fundamentals_summary": f"{ticker} muestra buenos resultados financieros.",
            "executive_summary":{
                "name": ticker,
                "sector": base["sector"],
                "industry": base["industry"],
                "country": base["country"],
                "valuation":{"pe_ratio":"25","market_cap":"$500B","eps":"5.2"},
                "price_trend_30d": np.round(np.random.uniform(-5,5),2)
            }
        }

try:
    from core.etf_finder import etf_screener
except:
    def etf_screener(theme):
        return [{"Ticker":"ETF1","Name":"Demo ETF 1","Category":theme or "Tech"},
                {"Ticker":"ETF2","Name":"Demo ETF 2","Category":theme or "Tech"}]

try:
    from core.favorites import load_favorites, add_favorite
except:
    _demo_favs = {}
    def load_favorites(username):
        return _demo_favs.get(username, {"all":[],"categories":{}})
    def add_favorite(username, items):
        if not isinstance(items, list):
            items = [items]
        _demo_favs[username] = {"all": items, "categories":{}}
        return _demo_favs[username]

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except:
    def compare_indicators(a,b): return {"P/E Ratio": (25,28),"EPS":(5.2,6.0)}
    def compare_sentiment(a,b): return {"Sentimiento":(0.3,0.1)}

try:
    from core.utils import sma, ema, rsi
except:
    def sma(s,n): return s.rolling(n).mean()
    def ema(s,n): return s.ewm(span=n).mean()
    def rsi(s,n):
        delta = s.diff()
        up = delta.clip(lower=0).rolling(n).mean()
        down = -delta.clip(upper=0).rolling(n).mean()
        rs = up/down
        return 100-(100/(1+rs))

# -----------------------------
# Demo tickers
# -----------------------------
DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]

# -----------------------------
# DASHBOARD
# -----------------------------
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr", layout="wide")
    st.title("📊 AppFinanzAr – Dashboard")

    # -----------------------------
    # Sidebar
    # -----------------------------
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")

        favs = load_favorites(username)
        favs.setdefault("all", [])
        favs.setdefault("categories", {})

        st.markdown("### ⭐ Favoritos")
        # Mostrar favoritos con eliminar
        for f in list(favs["all"]):
            col1,col2 = st.columns([4,1])
            with col1: st.write(f)
            with col2:
                if st.button("❌",key=f"del_{f}"):
                    favs["all"].remove(f)
                    add_favorite(username,favs["all"])
                    st.experimental_rerun()

        if st.button("🗑️ Borrar todos"):
            favs["all"] = []
            add_favorite(username,[])
            st.experimental_rerun()

        if favs["all"]:
            csv_buffer = io.StringIO()
            pd.DataFrame({"Ticker":favs["all"]}).to_csv(csv_buffer,index=False)
            st.download_button("💾 Exportar favoritos CSV", csv_buffer.getvalue(),file_name="favoritos.csv",mime="text/csv")

    # -----------------------------
    # Central demo selector
    # -----------------------------
    st.subheader("Selección de ticker demo")
    ticker = st.selectbox("Demo tickers",DEMO_TICKERS,index=0)
    st.session_state["dash_demo_ticker"] = ticker

    # Agregar a favoritos
    if st.button("⭐ Agregar a Favoritos"):
        if ticker not in favs["all"]:
            favs["all"].append(ticker)
            add_favorite(username,favs["all"])
            st.success(f"{ticker} agregado a favoritos")
            st.experimental_rerun()

    # -----------------------------
    # Rango de datos
    # -----------------------------
    st.subheader("Rango de datos")
    today = datetime.today().date()
    mapping = {"1m":30,"3m":90,"6m":180,"1y":365,"5y":365*5,"max":365*10}
    range_days = st.selectbox("Rango rápido",["1m","3m","6m","1y","5y","max"],index=0)
    start_date = today - timedelta(days=mapping[range_days])
    end_date = today

    # -----------------------------
    # Obtener datos
    # -----------------------------
    df = fetch_ohlc(ticker,from_date=start_date,to_date=end_date)
    df["SMA20"] = sma(df["close"],20)
    df["SMA50"] = sma(df["close"],50)
    df["EMA20"] = ema(df["close"],20)
    df["RSI14"] = rsi(df["close"],14)

    # -----------------------------
    # Gráfico OHLC + Indicadores
    # -----------------------------
    st.subheader("Gráfico de precios")
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],
        increasing_line_color="green",decreasing_line_color="red",name="OHLC"
    )])
    for col in ["SMA20","SMA50","EMA20"]:
        if col in df.columns: fig.add_trace(go.Scatter(x=df["date"],y=df[col],mode="lines",name=col))
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("RSI 14")
    rsi_fig = go.Figure(go.Scatter(x=df["date"],y=df["RSI14"],name="RSI14"))
    st.plotly_chart(rsi_fig,use_container_width=True)

    # -----------------------------
    # Overview / Executive Summary
    # -----------------------------
    overview = build_overview(ticker)
    exec_sum = overview.get("executive_summary",{})
    trend = exec_sum.get("price_trend_30d","N/A")
    card = f"""
**{exec_sum.get('name',ticker)}**  
Sector: {exec_sum.get('sector','N/A')}  •  Industria: {exec_sum.get('industry','N/A')}  •  País: {exec_sum.get('country','N/A')}

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')} — Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')} — EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}

**Tendencia 30d (simulada):** {trend}%  
**Sentimiento:** {overview.get('sentiment_label','Sin datos')}

**Resumen:** {overview.get('fundamentals_summary','')}
"""
    st.markdown(card)

    # Fundamentales
    st.subheader("Fundamentales")
    fund = overview.get("fundamentals",{})
    st.dataframe(pd.DataFrame.from_dict(fund,orient="index",columns=["Valor"]))

    # Competidores
    st.subheader("Competidores (máx 5)")
    st.write(", ".join(overview.get("competitors",[])[:5]))

    # Noticias
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news",[])
    simple = []
    for n in news_items:
        title = n.get("title","")
        date = n.get("published_at","")
        # simple sentimiento simulado
        score = np.random.uniform(-1,1)
        label = "Positivo" if score>0 else "Negativo" if score<0 else "Neutral"
        simple.append({"title":title,"date":date,"score":score,"label":label})
        st.write(f"- {title} ({date}) → {label} ({score:.2f})")
    sdf = pd.DataFrame(simple)
    colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
    fig_s = go.Figure(go.Bar(x=sdf['title'],y=sdf['score'],marker_color=colors))
    st.plotly_chart(fig_s,use_container_width=True)

    # -----------------------------
    # ETF Finder
    # -----------------------------
    st.subheader("ETF Finder")
    tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema)
        st.table(pd.DataFrame(etfs))

    # -----------------------------
    # Comparación rápida
    # -----------------------------
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB = st.columns(2)
    with colA:
        t_a = st.text_input("Ticker A",ticker,key="cmp_a")
    with colB:
        t_b = st.text_input("Ticker B","AAPL.US",key="cmp_b")
    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a,t_b)
        sent = compare_sentiment(t_a,t_b)
        st.markdown("**Indicadores:**")
        st.write(cmp)
        st.markdown("**Sentimiento:**")
        st.write(sent)

    st.caption("AppFinanzAr Pro Demo — Datos simulados, funciones completas. Contacto: desarrollador para datos reales / API keys.")


