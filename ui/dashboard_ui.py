# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import random

# ================================
# FALLBACKS si core no está disponible
# ================================
try:
    from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
except Exception:
    def fetch_ohlc(ticker, from_date=None, to_date=None):
        return pd.DataFrame()

    def fetch_fundamentals(ticker):
        return {}, []

    def fetch_news(ticker, days_back=30, translate_to_es=True):
        # Generar noticias demo variadas
        sample_titles = [
            f"{ticker} reporta resultados trimestrales positivos",
            f"{ticker} anuncia nueva estrategia de crecimiento",
            f"{ticker} enfrenta problemas regulatorios",
            f"Mercado reacciona ante movimientos de {ticker}",
            f"{ticker} recibe calificación favorable de analistas",
            f"Acciones de {ticker} suben tras acuerdo estratégico",
            f"Analistas bajan la proyección de {ticker}"
        ]
        news = []
        today = datetime.today()
        for i in range(random.randint(3, 7)):
            news.append({
                "title": random.choice(sample_titles),
                "published_at": (today - timedelta(days=random.randint(0,30))).strftime("%Y-%m-%d")
            })
        return news

    def search_ticker_by_name(name, max_results=10):
        mapping = {"galicia": ["GGAL.BA"], "apple": ["AAPL.US"], "microsoft": ["MSFT.US"], "amazon": ["AMZN.US"]}
        return mapping.get(name.lower(), [])

try:
    from core.overview import build_overview
except Exception:
    def build_overview(ticker, lang="es"):
        # Demo overview con datos más realistas
        sectors = {"MSFT.US":"Technology","AAPL.US":"Technology","GOOGL.US":"Technology","AMZN.US":"Consumer","GGAL.BA":"Finance"}
        industries = {"MSFT.US":"Software","AAPL.US":"Electronics","GOOGL.US":"Internet","AMZN.US":"E-commerce","GGAL.BA":"Banking"}
        countries = {"MSFT.US":"USA","AAPL.US":"USA","GOOGL.US":"USA","AMZN.US":"USA","GGAL.BA":"Argentina"}
        pe = {"MSFT.US":30,"AAPL.US":28,"GOOGL.US":32,"AMZN.US":70,"GGAL.BA":12}
        mc = {"MSFT.US":"2.1T","AAPL.US":"2.5T","GOOGL.US":"1.8T","AMZN.US":"1.7T","GGAL.BA":"12B"}
        eps = {"MSFT.US":8.5,"AAPL.US":6.1,"GOOGL.US":5.2,"AMZN.US":2.4,"GGAL.BA":1.2}

        fundamentals = {
            "P/E": pe.get(ticker,"N/A"),
            "Market Cap": mc.get(ticker,"N/A"),
            "EPS": eps.get(ticker,"N/A"),
            "Sector": sectors.get(ticker,"N/A"),
            "Industry": industries.get(ticker,"N/A"),
            "Country": countries.get(ticker,"N/A")
        }

        competitors = random.sample([t for t in ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"] if t!=ticker],3)

        # Generar predicción de tendencia 30d
        trend_30d = round(random.uniform(-5,10),2)

        # Noticias demo
        news = fetch_news(ticker)

        return {
            "fundamentals": fundamentals,
            "competitors": competitors,
            "price": pd.DataFrame(),
            "news": news,
            "sentiment_value": round(random.uniform(-1,1),2),
            "sentiment_label": random.choice(["Positive","Neutral","Negative"]),
            "fundamentals_summary": f"{ticker} muestra un desempeño estable en su sector.",
            "executive_summary":{
                "name": ticker,
                "sector": sectors.get(ticker,"N/A"),
                "industry": industries.get(ticker,"N/A"),
                "country": countries.get(ticker,"N/A"),
                "valuation":{"pe_ratio": pe.get(ticker,"N/A"), "market_cap": mc.get(ticker,"N/A"), "eps": eps.get(ticker,"N/A")},
                "price_trend_30d": trend_30d
            }
        }

try:
    from core.etf_finder import etf_screener
except Exception:
    def etf_screener(theme):
        return [{"ETF":"DemoETF1","Theme":theme or "General","Price":100},{"ETF":"DemoETF2","Theme":theme or "General","Price":105}]

try:
    from core.favorites import load_favorites, add_favorite
except Exception:
    _fake_store = {}
    def load_favorites(username):
        return _fake_store.get(username, {"all": [], "categories": {}})
    def add_favorite(username, item):
        # soporta agregar lista o un solo ticker
        if username not in _fake_store:
            _fake_store[username] = {"all": [], "categories": {}}
        if isinstance(item,list):
            _fake_store[username]["all"] = item
        else:
            if item not in _fake_store[username]["all"]:
                _fake_store[username]["all"].append(item)
        return _fake_store[username]

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a,b): return {"demo":"indicators"}
    def compare_sentiment(a,b): return {"demo":"sentiment"}

try:
    from core.utils import sma, ema, rsi
except Exception:
    def sma(s,n): return s.rolling(n).mean()
    def ema(s,n): return s.ewm(span=n).mean()
    def rsi(s,n):
        delta = s.diff()
        up = delta.clip(lower=0).rolling(n).mean()
        down = -delta.clip(upper=0).rolling(n).mean()
        rs = up / down
        return 100-(100/(1+rs))

try:
    from core.sentiment_model import sentiment_score
except Exception:
    def sentiment_score(text):
        t = (text or "").lower()
        if "up" in t or "good" in t: return 0.6
        if "down" in t or "bad" in t: return -0.6
        return 0.0

DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]

# ================================
# FUNCIONES AUXILIARES
# ================================
def analyze_sentiment_textblob(text:str):
    score = sentiment_score(text)
    if score>0.1: label="Positive"
    elif score<-0.1: label="Negative"
    else: label="Neutral"
    return score,label

def generate_demo_ohlc(ticker):
    idx = pd.date_range(end=datetime.today(), periods=60)
    prices = 100 + np.cumsum(np.random.randn(len(idx)))
    df = pd.DataFrame({
        "date": idx,
        "open": prices-1,
        "high": prices+1,
        "low": prices-2,
        "close": prices,
        "volume": 1000 + np.random.randint(-100,100,len(idx))
    })
    # indicadores
    df["SMA20"]=sma(df["close"],20)
    df["SMA50"]=sma(df["close"],50)
    df["EMA20"]=ema(df["close"],20)
    df["RSI14"]=rsi(df["close"],14)
    return df

# ================================
# DASHBOARD COMPLETO
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr PRO", layout="wide")
    st.title("📊 AppFinanzAr PRO – Demo completo y realista")

    # -----------------------------
    # SIDEBAR: Config + Usuario + Export
    # -----------------------------
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español","English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")
        favs = load_favorites(username)
        favs.setdefault("all",[])
        favs.setdefault("categories",{})

        # Mostrar favoritos con botones de eliminar
        st.markdown("**Favoritos**")
        for f in list(favs["all"]):
            col1,col2 = st.columns([4,1])
            with col1: st.write(f"• {f}")
            with col2:
                if st.button("❌", key=f"del_{f}"):
                    favs["all"].remove(f)
                    add_favorite(username,favs["all"])
                    st.experimental_rerun()
        if not favs["all"]: st.write("_Sin favoritos_")

        # Exportar favoritos
        if favs["all"]:
            csv_buffer = io.StringIO()
            pd.DataFrame(favs["all"],columns=["Ticker"]).to_csv(csv_buffer,index=False)
            st.download_button("💾 Exportar favoritos CSV", csv_buffer.getvalue(), file_name="favoritos.csv")

        st.markdown("---")
        st.markdown("### Demo Utilities")
        if st.button("Cargar ejemplo demo (MSFT)"):
            st.session_state["dash_demo_ticker"] = "MSFT.US"
            st.experimental_rerun()

    # -----------------------------
    # CONTROLES CENTRALES
    # -----------------------------
    st.subheader("Búsqueda de activo")
    col1,col2 = st.columns([2,1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state.get("dash_demo_ticker","MSFT.US"), key="dash_ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa", "")

    ticker = ticker_input
    if company_search:
        results = search_ticker_by_name(company_search)
        if results:
            ticker = st.selectbox("Resultados", results, index=0)
        else:
            st.warning("No se encontraron tickers con esa búsqueda.")

    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", DEMO_TICKERS)
        if sel: ticker = sel

    # Botón agregar a favoritos
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar ticker a favoritos"):
        add_favorite(username,ticker)
        st.success(f"{ticker} agregado a favoritos.")
        st.experimental_rerun()

    # -----------------------------
    # Rango de datos
    # -----------------------------
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

    st.info(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")

    # -----------------------------
    # FETCH / DEMO DATA
    # -----------------------------
    try:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
        if df is None or df.empty:
            df = generate_demo_ohlc(ticker)
            demo_mode=True
        else:
            demo_mode=False
    except:
        df = generate_demo_ohlc(ticker)
        demo_mode=True

    # -----------------------------
    # GRÁFICOS DE PRECIO
    # -----------------------------
    st.subheader("Gráfico de precios")
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        increasing_line_color="green", decreasing_line_color="red", name="OHLC"
    )])
    for col_name in ["SMA20","SMA50","EMA20"]:
        if col_name in df.columns and df[col_name].notna().any():
            fig.add_trace(go.Scatter(x=df["date"], y=df[col_name], mode="lines", name=col_name))
    fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
    st.plotly_chart(fig,use_container_width=True)

    # RSI
    st.subheader("RSI 14")
    if "RSI14" in df.columns:
        fig_rsi = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
        fig_rsi.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
        st.plotly_chart(fig_rsi,use_container_width=True)

    # -----------------------------
    # OVERVIEW / RESUMEN EJECUTIVO
    # -----------------------------
    st.subheader("Overview / Resumen ejecutivo")
    overview = build_overview(ticker, lang_code)
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
    if fund:
        st.dataframe(pd.DataFrame.from_dict(fund, orient="index", columns=["Valor"]))
    else:
        st.info("No se encontraron fundamentales.")

    # Competidores
    st.subheader("Competidores (máx 5)")
    comps = overview.get("competitors",[])
    if comps: st.write(", ".join(comps[:5]))
    else: st.info("No se encontraron competidores.")

    # Noticias
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news",[])
    simple=[]
    for n in news_items[:10]:
        title=n.get("title","")
        published=n.get("published_at","")
        score,label = analyze_sentiment_textblob(title)
        simple.append({"title":title,"date":published,"score":score,"label":label})
        st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
    if simple:
        sdf = pd.DataFrame(simple)
        colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
        fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['score'], marker_color=colors))
        fig_s.update_layout(title="Sentimiento de noticias", template="plotly_dark", xaxis_tickangle=-45,height=300)
        st.plotly_chart(fig_s,use_container_width=True)

    # -----------------------------
    # ETF Finder
    # -----------------------------
    st.subheader("ETF Finder (temas)")
    tema = st.text_input("Buscar ETFs por tema", key="etf_theme")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema) if tema else etf_screener(None)
        if etfs:
            st.table(pd.DataFrame(etfs))
        else:
            st.info("No se encontraron ETFs para ese tema.")

    # -----------------------------
    # Comparación rápida
    # -----------------------------
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

    # Footer
    st.markdown("---")
    if demo_mode:
        st.info("Modo demo activo: datos simulados y completos.")
    st.caption("AppFinanzAr PRO — modo demo-friendly. Contacto: desarrollador para ajustar datos reales / keys.")
