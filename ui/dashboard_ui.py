# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ================================
# Import core functions with fallback
# ================================
try:
    from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
except:
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
except:
    def build_overview(ticker, lang="es"):
        # Demo realistic data
        pe = round(random.uniform(10, 40), 2)
        market_cap = f"{round(random.uniform(1, 200),2)}B"
        eps = round(random.uniform(0.5, 15),2)
        return {
            "fundamentals": {
                "Revenue": f"${round(random.uniform(1, 100),2)}B",
                "Net Income": f"${round(random.uniform(0.5, 50),2)}B",
                "EPS": eps,
                "P/E Ratio": pe
            },
            "competitors": ["AAA", "BBB", "CCC", "DDD", "EEE"],
            "price": pd.DataFrame(),
            "news": [{"title": f"{ticker} alcanza nuevo máximo", "date": datetime.today().strftime("%Y-%m-%d")},
                     {"title": f"Analistas positivos sobre {ticker}", "date": datetime.today().strftime("%Y-%m-%d")}],
            "sentiment_value": random.uniform(-1,1),
            "sentiment_label": random.choice(["positivo","negativo","neutral"]),
            "fundamentals_summary": "Demo de fundamentales generadas automáticamente.",
            "executive_summary": {
                "name": ticker,
                "sector": random.choice(["Tech","Finance","Energy","Consumer"]),
                "industry": random.choice(["Software","Banking","Oil","Retail"]),
                "country": random.choice(["USA","Argentina","Germany","China"]),
                "valuation": {"pe_ratio": pe, "market_cap": market_cap, "eps": eps},
                "price_trend_30d": round(random.uniform(-10,10),2)
            }
        }

try:
    from core.etf_finder import etf_screener
except:
    def etf_screener(theme):
        return [{"Ticker":"TECHX","Name":"Tech ETF Demo","Theme":theme or "Tech"},
                {"Ticker":"ENERGYX","Name":"Energy ETF Demo","Theme":theme or "Energy"}]

try:
    from core.favorites import load_favorites, add_favorite
except:
    _demo_favs = {}
    def load_favorites(username):
        return _demo_favs.get(username, {"all": [], "categories": {}})
    def add_favorite(username, item):
        if username not in _demo_favs:
            _demo_favs[username] = {"all": [], "categories": {}}
        if isinstance(item, list):
            _demo_favs[username]["all"] = item
        else:
            if item not in _demo_favs[username]["all"]:
                _demo_favs[username]["all"].append(item)
        return _demo_favs[username]["all"]

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except:
    def compare_indicators(a,b):
        return {"DemoMetric1": random.random(), "DemoMetric2": random.random()}
    def compare_sentiment(a,b):
        return {"SentimentA": random.uniform(-1,1), "SentimentB": random.uniform(-1,1)}

try:
    from core.utils import sma, ema, rsi
except:
    def sma(s, n): return s.rolling(n).mean()
    def ema(s, n): return s.ewm(span=n).mean()
    def rsi(s, n):
        delta = s.diff()
        up = delta.clip(lower=0).rolling(n).mean()
        down = -delta.clip(upper=0).rolling(n).mean()
        rs = up / down
        return 100 - (100 / (1 + rs))

try:
    from core.sentiment_model import sentiment_score
except:
    def sentiment_score(text):
        t = (text or "").lower()
        if "up" in t or "positivo" in t:
            return 0.6
        elif "down" in t or "negativo" in t:
            return -0.6
        return 0.0

DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]

def analyze_sentiment_textblob(text: str):
    score = sentiment_score(text)
    if score>0.1: label="positivo"
    elif score<-0.1: label="negativo"
    else: label="neutral"
    return score,label

# ================================
# DASHBOARD PRO
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr PRO", layout="wide")
    st.title("📊 AppFinanzAr – Dashboard PRO (Demo Friendly)")

    # ---------------- Sidebar ----------------
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español","English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Usuario y Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")

        favs = load_favorites(username)
        favs.setdefault("all",[])
        favs.setdefault("categories",{})

        st.markdown("**Favoritos**")
        if favs["all"]:
            for f in favs["all"]:
                col1,col2 = st.columns([4,1])
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
            if st.button("🗑️ Borrar todos los favoritos"):
                favs["all"] = []
                add_favorite(username,[])
                st.experimental_rerun()

        st.markdown("---")
        st.markdown("### Demo / Utilities")
        if st.button("Cargar ejemplo demo"):
            st.session_state["dash_demo_ticker"] = DEMO_TICKERS[0]
            st.experimental_rerun()

    # ---------------- Top Controls ----------------
    st.subheader("Búsqueda de activo")
    col1,col2 = st.columns([2,1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state.get("dash_demo_ticker","MSFT.US"), key="dash_ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa (opcional)","")
    ticker = ticker_input
    if company_search:
        results = search_ticker_by_name(company_search)
        if results:
            ticker = st.selectbox(f"Resultados para '{company_search}'", results, index=0)
        else:
            st.warning("No se encontraron tickers; usa el ticker directamente.")

    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", DEMO_TICKERS)
        if sel: ticker = sel

    # Favoritos
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar este ticker a favoritos"):
        add_favorite(username,ticker)
        st.success(f"{ticker} agregado a favoritos.")
        st.experimental_rerun()

    # ---------------- Date Range ----------------
    st.markdown("---")
    st.subheader("Rango de datos")
    range_days = st.selectbox("Rango rápido", ["1m","3m","6m","1y","5y","max"], index=0)
    custom_range = st.checkbox("Usar rango personalizado")
    if custom_range:
        start_date = st.date_input("Inicio", datetime.today()-timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        today = datetime.today().date()
        mapping = {"1m":30,"3m":90,"6m":180,"1y":365,"5y":365*5,"max":365*10}
        start_date = today - timedelta(days=mapping[range_days])
        end_date = today

    # ---------------- FETCH DATA ----------------
    st.markdown("---")
    st.info(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")
    try:
        df = fetch_ohlc(ticker,from_date=start_date,to_date=end_date)
    except:
        df=pd.DataFrame()
    if df is None or df.empty:
        idx = pd.date_range(end=datetime.today(), periods=60, freq='D')
        prices = 100 + np.cumsum(np.random.randn(len(idx)))
        df = pd.DataFrame({"date":idx,"open":prices-1,"high":prices+1,"low":prices-2,"close":prices,"volume":1000})
        df.reset_index(drop=True,inplace=True)
        demo_mode = True
    else:
        demo_mode=False

    # Indicators
    try:
        df["SMA20"] = sma(df["close"],20)
        df["SMA50"] = sma(df["close"],50)
        df["EMA20"] = ema(df["close"],20)
        df["RSI14"] = rsi(df["close"],14)
    except:
        df["SMA20"]=pd.NA
        df["SMA50"]=pd.NA
        df["EMA20"]=pd.NA
        df["RSI14"]=pd.NA

    # ---------------- Charts ----------------
    st.subheader("Gráfico de precios")
    try:
        fig = go.Figure(data=[go.Candlestick(x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                                             increasing_line_color="green", decreasing_line_color="red", name="OHLC")])
        if df["SMA20"].notna().any(): fig.add_trace(go.Scatter(x=df["date"],y=df["SMA20"],mode="lines",name="SMA20"))
        if df["SMA50"].notna().any(): fig.add_trace(go.Scatter(x=df["date"],y=df["SMA50"],mode="lines",name="SMA50"))
        if df["EMA20"].notna().any(): fig.add_trace(go.Scatter(x=df["date"],y=df["EMA20"],mode="lines",name="EMA20"))
        fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
        st.plotly_chart(fig,use_container_width=True)
    except:
        st.error("No se pudo dibujar el gráfico de precios")

    # RSI Chart
    if "RSI14" in df.columns:
        st.subheader("RSI 14")
        try:
            rsi_fig = go.Figure(go.Scatter(x=df["date"],y=df["RSI14"],name="RSI 14"))
            rsi_fig.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
            st.plotly_chart(rsi_fig,use_container_width=True)
        except: pass

    # ---------------- Overview / Resumen ----------------
    st.subheader("Overview / Resumen ejecutivo")
    overview = build_overview(ticker, lang=("es" if lang=="Español" else "en"))
    exec_sum = overview.get("executive_summary",{})
    card = f"""
**{exec_sum.get('name',ticker)}**  
Sector: {exec_sum.get('sector','N/A')}  •  Industria: {exec_sum.get('industry','N/A')}  •  País: {exec_sum.get('country','N/A')}

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')}  —  Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')}  —  EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}

**Tendencia 30d:** {exec_sum.get('price_trend_30d','N/A')}%  •  **Sentimiento:** {overview.get('sentiment_label','Sin datos')}

**Resumen:** {overview.get('fundamentals_summary','')}
"""
    st.markdown(card)

    # Fundamentales
    st.subheader("Fundamentales (clave)")
    fund = overview.get("fundamentals",{})
    if fund: st.dataframe(pd.DataFrame.from_dict(fund, orient="index", columns=["Valor"]))
    else: st.info("No se encontraron fundamentales válidos.")

    # Competidores
    st.subheader("Competidores (máx 5)")
    comps = overview.get("competitors",[])[:5]
    if comps: st.write(", ".join(comps))
    else: st.info("No se encontraron competidores.")

    # Noticias + Sentimiento
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news",[]) or fetch_news(ticker)
    if news_items:
        simple=[]
        for n in news_items[:10]:
            title=n.get("title","")[:200]
            date=n.get("published_at",n.get("date",""))
            score,label = analyze_sentiment_textblob(title)
            simple.append({"title":title,"date":date,"score":score,"label":label})
            st.write(f"- **{title}** ({date}) → *{label}* ({score:.2f})")
        sdf = pd.DataFrame(simple)
        colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
        fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['score'], marker_color=colors))
        fig_s.update_layout(title="Sentimiento de noticias", template="plotly_dark", xaxis_tickangle=-45, height=300)
        st.plotly_chart(fig_s,use_container_width=True)
    else:
        st.info("No hay noticias disponibles.")

    # ---------------- ETF Finder ----------------
    st.subheader("ETF Finder (temas)")
    tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)", key="etf_theme")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema)
        if etfs: st.table(pd.DataFrame(etfs))
        else: st.info("No se encontraron ETFs para ese tema.")

    # ---------------- Comparación rápida ----------------
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB = st.columns(2)
    with colA: t_a = st.text_input("Ticker A", ticker, key="cmp_a")
    with colB: t_b = st.text_input("Ticker B", "AAPL.US", key="cmp_b")
    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a,t_b)
        sent = compare_sentiment(t_a,t_b)
        st.markdown("**Indicadores:**")
        st.write(cmp)
        st.markdown("**Sentimiento:**")
        st.write(sent)

    # ---------------- Footer ----------------
    st.markdown("---")
    if demo_mode:
        st.info("Mostrando datos de demo porque no hubo OHLC real o la API está limitada.")
    st.caption("AppFinanzAr PRO — modo demo-friendly. Datos reales disponibles con API.")
