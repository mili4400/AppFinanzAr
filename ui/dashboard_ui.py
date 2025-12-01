# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# ================================
# FALLBACKS PARA FUNCIONES CORE
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
        return {}

try:
    from core.etf_finder import etf_screener
except Exception:
    def etf_screener(theme):
        return []

try:
    from core.favorites import load_favorites, add_favorite
except Exception:
    def load_favorites(username):
        return {"all": [], "categories": {}}
    def add_favorite(username, item):
        return []

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a, b): return {}
    def compare_sentiment(a, b): return {}

try:
    from core.utils import sma, ema, rsi
except Exception:
    def sma(s, n): return s
    def ema(s, n): return s
    def rsi(s, n): return s*0

try:
    from core.sentiment_model import sentiment_score
except Exception:
    def sentiment_score(text):
        t = (text or "").lower()
        if "up" in t or "good" in t or "positivo" in t: return 0.6
        if "down" in t or "bad" in t or "negativo" in t: return -0.6
        return 0.0

# ================================
# DEMO MULTI-TICKER
# ================================
DEMO_TICKERS = {
    "MSFT.US": {
        "fundamentals": {"P/E":"35.2","EPS":"9.12","Market Cap":"2.1T","ROE":"28%","Debt/Equity":"0.45"},
        "competitors":["AAPL.US","GOOGL.US","AMZN.US"],
        "news":[
            {"title":"Microsoft lanza producto innovador","date":"2025-01-20"},
            {"title":"Analistas optimistas sobre crecimiento MSFT","date":"2025-01-18"}
        ],
        "executive_summary":{"name":"Microsoft","sector":"Tecnología","industry":"Software","country":"USA","valuation":{"pe_ratio":"35.2","market_cap":"2.1T","eps":"9.12"},"price_trend_30d":"+3.8%"},
        "sentiment_label":"Positivo",
        "fundamentals_summary":"Microsoft muestra crecimiento sostenido y sólido desempeño financiero."
    },
    "AAPL.US": {
        "fundamentals": {"P/E":"28.7","EPS":"6.45","Market Cap":"2.5T","ROE":"27%","Debt/Equity":"0.35"},
        "competitors":["MSFT.US","GOOGL.US","AMZN.US"],
        "news":[
            {"title":"Apple presenta nuevo iPhone","date":"2025-01-22"},
            {"title":"Mercado confía en resultados de Apple","date":"2025-01-19"}
        ],
        "executive_summary":{"name":"Apple","sector":"Tecnología","industry":"Hardware/Software","country":"USA","valuation":{"pe_ratio":"28.7","market_cap":"2.5T","eps":"6.45"},"price_trend_30d":"+4.1%"},
        "sentiment_label":"Positivo",
        "fundamentals_summary":"Apple mantiene liderazgo en innovación y rentabilidad."
    },
    "GGAL.BA": {
        "fundamentals": {"P/E":"12.5","EPS":"3.20","Market Cap":"1.1B","ROE":"18%","Debt/Equity":"0.5"},
        "competitors":["BBAR.BA","BMA.BA","SUPV.BA"],
        "news":[
            {"title":"Galicia anuncia nuevos productos financieros","date":"2025-01-21"},
            {"title":"Banco Galicia mantiene confianza del mercado","date":"2025-01-19"}
        ],
        "executive_summary":{"name":"Banco Galicia","sector":"Finanzas","industry":"Banca","country":"Argentina","valuation":{"pe_ratio":"12.5","market_cap":"1.1B","eps":"3.20"},"price_trend_30d":"+2.6%"},
        "sentiment_label":"Positivo",
        "fundamentals_summary":"Banco Galicia mantiene estabilidad y crecimiento en el mercado local."
    }
}

def build_demo_overview(ticker):
    return DEMO_TICKERS.get(ticker, {
        "fundamentals": {"P/E":"N/A","EPS":"N/A","Market Cap":"N/A"},
        "competitors": [],
        "news": [],
        "executive_summary":{"name":ticker,"sector":"N/A","industry":"N/A","country":"N/A","valuation":{"pe_ratio":"N/A","market_cap":"N/A","eps":"N/A"},"price_trend_30d":"N/A"},
        "sentiment_label":"Sin datos",
        "fundamentals_summary":"Sin datos"
    })

def analyze_sentiment_textblob(text: str):
    score = sentiment_score(text)
    if score > 0.1: label = "positive"
    elif score < -0.1: label = "negative"
    else: label = "neutral"
    return score, label

# ================================
# DASHBOARD PRINCIPAL
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr", layout="wide")
    st.title("📊 AppFinanzAr – Dashboard (Demo friendly)")

    # -------------------
    # SIDEBAR: CONFIG + FAVORITOS
    # -------------------
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español", "English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")

        favs = load_favorites(username)
        if not isinstance(favs, dict): favs={"all":favs or [], "categories":{}}
        favs.setdefault("all",[])
        favs.setdefault("categories",{})

        st.markdown("**Favoritos**")
        if favs["all"]:
            for f in favs["all"]:
                col_f1, col_f2 = st.columns([4,1])
                with col_f1: st.write(f"• {f}")
                with col_f2:
                    if st.button("❌", key=f"del_{f}"):
                        try:
                            favs["all"].remove(f)
                            add_favorite(username, favs["all"])
                            st.success(f"Eliminado {f}")
                            st.rerun()
                        except: st.error("Error al eliminar")
        else:
            st.write("_Sin favoritos_")

        # Botón borrar todos
        if favs["all"]:
            if st.button("🗑️ Borrar todos los favoritos"):
                favs["all"]=[]
                add_favorite(username, [])
                st.rerun()

        st.markdown("---")
        st.markdown("### Demo / Utilities")
        if st.button("Cargar ejemplo demo"):
            st.session_state["dash_demo_ticker"]="MSFT.US"
            st.rerun()

    # -------------------
    # BUSQUEDA DE TICKER
    # -------------------
    st.subheader("Búsqueda de activo")
    col1,col2 = st.columns([2,1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state.get("dash_demo_ticker","MSFT.US"), key="dash_ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa (opcional)","")

    ticker = ticker_input
    if company_search:
        try: results = search_ticker_by_name(company_search)
        except: results=[]
        if results: ticker = st.selectbox(f"Resultados para '{company_search}'", results, index=0)
        else: st.warning("No se encontraron tickers con esa búsqueda; probá con el ticker directamente.")

    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", list(DEMO_TICKERS.keys()))
        if sel: ticker = sel

    # -------------------
    # AGREGAR FAVORITOS (ticker actual)
    # -------------------
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar este ticker a favoritos"):
        try:
            add_favorite(username, ticker)
            st.success(f"{ticker} agregado a favoritos.")
        except Exception as e:
            st.error(f"No se pudo agregar: {e}")
        st.rerun()

    # -------------------
    # RANGO DE DATOS
    # -------------------
    st.markdown("---")
    st.subheader("Rango de datos")
    range_days = st.selectbox("Rango rápido", ["1m","3m","6m","1y","5y","max"], index=0)
    custom_range = st.checkbox("Usar rango personalizado")
    if custom_range:
        start_date = st.date_input("Inicio", datetime.today() - timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        today = datetime.today().date()
        mapping = {"1m":30,"3m":90,"6m":180,"1y":365,"5y":365*5,"max":365*10}
        start_date = today - timedelta(days=mapping[range_days])
        end_date = today

    st.markdown("---")
    st.info(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")

    # -------------------
    # FETCH OHLC / DEMO
    # -------------------
    try: df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    except: df=pd.DataFrame()

    demo_mode=False
    if df is None or df.empty:
        idx = pd.date_range(end=datetime.today(), periods=60, freq='D')
        prices = 100 + np.cumsum(np.random.randn(len(idx)))
        df=pd.DataFrame({"date":idx,"open":prices-1,"high":prices+1,"low":prices-2,"close":prices,"volume":1000})
        demo_mode=True

    # -------------------
    # INDICADORES
    # -------------------
    try:
        df["SMA20"]=sma(df["close"],20)
        df["SMA50"]=sma(df["close"],50)
        df["EMA20"]=ema(df["close"],20)
        df["RSI14"]=rsi(df["close"],14)
    except:
        df["SMA20"]=pd.NA; df["SMA50"]=pd.NA; df["EMA20"]=pd.NA; df["RSI14"]=pd.NA

    # -------------------
    # GRAFICOS
    # -------------------
    st.subheader("Gráfico de precios")
    try:
        fig = go.Figure(data=[go.Candlestick(x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], increasing_line_color="green", decreasing_line_color="red", name="OHLC")])
        if "SMA20" in df.columns and df["SMA20"].notna().any(): fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
        if "SMA50" in df.columns and df["SMA50"].notna().any(): fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
        if "EMA20" in df.columns and df["EMA20"].notna().any(): fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
        fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e: st.error("No se pudo dibujar el gráfico de precios: "+str(e))

    if "RSI14" in df.columns:
        st.subheader("RSI 14")
        try:
            rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
            rsi_fig.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
            st.plotly_chart(rsi_fig, use_container_width=True)
        except: pass

    # -------------------
    # OVERVIEW
    # -------------------
    st.subheader("Overview / Resumen ejecutivo")
    try: overview = build_overview(ticker, lang=lang_code)
    except: overview = build_demo_overview(ticker)
    if not overview: overview = build_demo_overview(ticker)

    exec_sum = overview.get("executive_summary", {})
    card = f"""
**{exec_sum.get('name', ticker)}**  
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
        try: st.dataframe(pd.DataFrame.from_dict(fund, orient="index", columns=["Valor"]))
        except: st.write(fund)
    else: st.info("No se encontraron fundamentales válidos.")

    # Competidores
    st.subheader("Competidores (máx 5)")
    comps = overview.get("competitors",[]) or []
    if comps: st.write(", ".join(comps[:5]))
    else: st.info("No se encontraron competidores.")

    # Noticias
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news",[]) or []
    if not news_items:
        try: news_items = fetch_news(ticker) or []
        except: news_items=[]

    if news_items:
        simple=[]
        for n in news_items[:10]:
            title = n.get("title","")[:200]
            published = n.get("published_at", n.get("date",""))
            score,label = analyze_sentiment_textblob(title)
            simple.append({"title":title,"date":published,"score":score,"label":label})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
        sdf=pd.DataFrame(simple)
        try:
            colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
            fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['score'], marker_color=colors))
            fig_s.update_layout(title="Sentimiento de noticias (bar)", template="plotly_dark", xaxis_tickangle=-45, height=300)
            st.plotly_chart(fig_s, use_container_width=True)
        except: pass
    else: st.info("No hay noticias disponibles.")

    # ETF Finder
    st.subheader("ETF Finder (temas)")
    tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)", key="etf_theme")
    if st.button("Buscar ETFs"):
        try: etfs = etf_screener(tema) if tema else etf_screener(None)
        except: etfs=[]
        if etfs: st.table(pd.DataFrame(etfs))
        else: st.info("No se encontraron ETFs para ese tema (o demo activo).")

    # Comparación rápida
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB=st.columns(2)
    with colA: t_a = st.text_input("Ticker A", ticker, key="cmp_a")
    with colB: t_b = st.text_input("Ticker B", "AAPL.US", key="cmp_b")
    if st.button("Comparar ahora"):
        try:
            cmp=compare_indicators(t_a,t_b)
            sent=compare_sentiment(t_a,t_b)
            st.markdown("**Indicadores (objeto):**"); st.write(cmp)
            st.markdown("**Sentimiento:**"); st.write(sent)
        except Exception as e: st.error("Error comparando: "+str(e))

    # Footer
    st.markdown("---")
    if demo_mode: st.info("Mostrando datos de demo porque no hubo OHLC real disponibles o la API está limitada.")
    st.caption("AppFinanzAr — modo demo-friendly. Contacto: desarrollador para ajustar datos reales / keys.")



