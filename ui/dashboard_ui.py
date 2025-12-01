# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io

# ================================
# Fallbacks para core si no existen
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
        # Demo overview completo con tendencias simuladas
        trend = np.round(np.random.uniform(-5, 5), 2)
        fundamentals = {
            "Revenue": f"${np.random.randint(10,200)}B",
            "Net Income": f"${np.random.randint(1,50)}B",
            "EPS": f"{np.round(np.random.uniform(0.5,5),2)}",
            "P/E": np.round(np.random.uniform(10,40),2)
        }
        competitors = ["AAPL.US","GOOGL.US","AMZN.US","TSLA.US","FB.US"]
        news_demo = [
            {"title": f"{ticker} reports strong quarterly results", "published_at": "2025-12-01"},
            {"title": f"Analyst upgrades {ticker} to Buy", "published_at": "2025-11-28"},
            {"title": f"{ticker} launches new product line", "published_at": "2025-11-25"},
            {"title": f"{ticker} stock reacts to market news", "published_at": "2025-11-22"},
            {"title": f"{ticker} CEO interview highlights growth", "published_at": "2025-11-20"},
        ]
        return {
            "fundamentals": fundamentals,
            "competitors": competitors,
            "price": pd.DataFrame(),
            "news": news_demo,
            "sentiment_value": np.random.uniform(-1,1),
            "sentiment_label": "Positive" if trend>0 else "Negative",
            "fundamentals_summary": f"{ticker} shows solid financial performance and growth potential.",
            "executive_summary": {
                "name": ticker,
                "sector": "Technology",
                "industry": "Software",
                "country": "USA",
                "valuation": {"pe_ratio": fundamentals["P/E"], "market_cap": f"{np.random.randint(50,200)}B", "eps": fundamentals["EPS"]},
                "price_trend_30d": trend
            }
        }

try:
    from core.etf_finder import etf_screener
except Exception:
    def etf_screener(theme):
        return [{"ETF": "SPY", "Sector": "S&P500"}, {"ETF": "QQQ", "Sector":"Nasdaq"}]

try:
    from core.favorites import load_favorites, add_favorite
except Exception:
    FAVORITES_DB = {}
    def load_favorites(username):
        return FAVORITES_DB.get(username, {"all": [], "categories": {}})
    def add_favorite(username, item):
        # item puede ser str o lista
        if username not in FAVORITES_DB:
            FAVORITES_DB[username] = {"all": [], "categories": {}}
        if isinstance(item, list):
            FAVORITES_DB[username]["all"] = item
        else:
            if item not in FAVORITES_DB[username]["all"]:
                FAVORITES_DB[username]["all"].append(item)
        return FAVORITES_DB[username]

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a, b): 
        return {"SMA": np.round(np.random.uniform(0,1),2), "EMA": np.round(np.random.uniform(0,1),2)}
    def compare_sentiment(a, b): 
        return {"Sentiment Diff": np.round(np.random.uniform(-1,1),2)}

try:
    from core.utils import sma, ema, rsi
except Exception:
    def sma(s, n): 
        try: return s.rolling(n).mean()
        except: return s
    def ema(s, n):
        try: return s.ewm(span=n).mean()
        except: return s
    def rsi(s, n):
        try:
            delta = s.diff()
            up = delta.clip(lower=0).rolling(n).mean()
            down = -delta.clip(upper=0).rolling(n).mean()
            rs = up / down
            return 100 - (100 / (1 + rs))
        except:
            return s*0

try:
    from core.sentiment_model import sentiment_score
except Exception:
    def sentiment_score(text):
        t = (text or "").lower()
        if "up" in t or "good" in t or "positivo" in t:
            return 0.6
        if "down" in t or "bad" in t or "negativo" in t:
            return -0.6
        return 0.0

# Demo tickers
DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]

def analyze_sentiment_textblob(text: str):
    score = sentiment_score(text)
    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return score, label

# ================================
# DASHBOARD PRINCIPAL
# ================================
def show_dashboard():
    st.set_page_config(page_title="AppFinanzAr", layout="wide")
    st.title("📊 AppFinanzAr – Dashboard PRO (Demo friendly)")

    # Sidebar: idioma + usuario + favoritos + export
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español", "English"])
        lang_code = "es" if lang=="Español" else "en"
        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")
        favs = load_favorites(username)
        favs.setdefault("all", [])
        favs.setdefault("categories", {})

        # Mostrar favoritos con botón eliminar
        st.markdown("**Favoritos:**")
        for f in favs["all"]:
            col_f1, col_f2 = st.columns([4,1])
            with col_f1:
                st.write(f"• {f}")
            with col_f2:
                if st.button("❌", key=f"del_{f}"):
                    favs["all"].remove(f)
                    add_favorite(username, favs["all"])
                    st.experimental_rerun()

        if not favs["all"]:
            st.write("_Sin favoritos_")
        # Botón borrar todos
        if favs["all"] and st.button("🗑️ Borrar todos los favoritos"):
            favs["all"] = []
            add_favorite(username, [])
            st.experimental_rerun()

        # Exportar favoritos
        if favs["all"] and st.button("💾 Exportar favoritos a CSV"):
            csv_buffer = io.StringIO()
            pd.DataFrame(favs["all"], columns=["Ticker"]).to_csv(csv_buffer, index=False)
            st.download_button("Descargar CSV", data=csv_buffer.getvalue(), file_name="favoritos.csv", mime="text/csv")

    # -----------------------------
    # Ticker input y demo suggestions
    # -----------------------------
    st.subheader("Búsqueda de activo")
    col1, col2 = st.columns([2,1])
    with col1:
        if "dash_demo_ticker" not in st.session_state:
            st.session_state["dash_demo_ticker"] = DEMO_TICKERS[0]
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state["dash_demo_ticker"], key="dash_ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa (opcional)","")

    ticker = ticker_input

    if company_search:
        try:
            results = search_ticker_by_name(company_search)
        except:
            results=[]
        if results:
            ticker = st.selectbox(f"Resultados para '{company_search}'", results, index=0)
        else:
            st.warning("No se encontraron tickers; probá con el ticker directamente.")

    # Sugerencias demo
    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", DEMO_TICKERS)
        if sel != st.session_state.get("dash_demo_ticker",""):
            st.session_state["dash_demo_ticker"] = sel
            ticker = sel

    # Agregar a favoritos
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar este ticker a favoritos"):
        add_favorite(username, ticker)
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
        start_date = st.date_input("Inicio", datetime.today() - timedelta(days=30))
        end_date = st.date_input("Fin", datetime.today())
    else:
        today = datetime.today().date()
        mapping = {"1m":30, "3m":90, "6m":180, "1y":365, "5y":365*5, "max":365*10}
        start_date = today - timedelta(days=mapping[range_days])
        end_date = today

    # -----------------------------
    # FETCH DATA DEMO/REAL
    # -----------------------------
    st.markdown("---")
    st.info(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")
    try:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    except:
        df = pd.DataFrame()
    # Si vacío, demo synthetic
    demo_mode=False
    if df is None or df.empty:
        idx = pd.date_range(end=datetime.today(), periods=60)
        prices = 100 + np.cumsum(np.random.randn(len(idx)))
        df = pd.DataFrame({"date":idx,"open":prices-1,"high":prices+1,"low":prices-2,"close":prices,"volume":1000})
        demo_mode=True

    # Indicadores
    try:
        df["SMA20"] = sma(df["close"],20)
        df["SMA50"] = sma(df["close"],50)
        df["EMA20"] = ema(df["close"],20)
        df["RSI14"] = rsi(df["close"],14)
    except:
        df["SMA20"] = df["SMA50"] = df["EMA20"] = df["RSI14"] = pd.NA

    # -----------------------------
    # Gráfico de precios
    # -----------------------------
    st.subheader("Gráfico de precios")
    fig = go.Figure(data=[go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        increasing_line_color="green", decreasing_line_color="red", name="OHLC"
    )])
    for col in ["SMA20","SMA50","EMA20"]:
        if col in df.columns and df[col].notna().any():
            fig.add_trace(go.Scatter(x=df["date"], y=df[col], mode="lines", name=col))
    fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    # RSI chart
    if "RSI14" in df.columns:
        st.subheader("RSI 14")
        rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
        rsi_fig.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
        st.plotly_chart(rsi_fig, use_container_width=True)

    # -----------------------------
    # Overview / executive summary
    # -----------------------------
    st.subheader("Overview / Resumen ejecutivo")
    overview = build_overview(ticker, lang=lang_code)
    exec_sum = overview.get("executive_summary",{})
    card = f"""
**{exec_sum.get('name', ticker)}**  
Sector: {exec_sum.get('sector','N/A')} • Industria: {exec_sum.get('industry','N/A')} • País: {exec_sum.get('country','N/A')}

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')} — Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')} — EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}

**Tendencia 30d (simulada):** {exec_sum.get('price_trend_30d','N/A')}% • Sentimiento: {overview.get('sentiment_label','Sin datos')}

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
    comps = overview.get("competitors",[]) or []
    if comps:
        st.write(", ".join(comps[:5]))
    else:
        st.info("No se encontraron competidores.")

    # Noticias y sentimiento
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news",[]) or []
    if news_items:
        simple=[]
        for n in news_items[:10]:
            title = n.get("title","")[:200]
            date = n.get("published_at","")
            score,label = analyze_sentiment_textblob(title)
            simple.append({"title":title,"date":date,"score":score,"label":label})
            st.write(f"- **{title}** ({date}) → *{label}* ({score:.2f})")
        sdf=pd.DataFrame(simple)
        colors = sdf['score'].apply(lambda x:"green" if x>0 else "red" if x<0 else "gray")
        fig_s = go.Figure(go.Bar(x=sdf['title'],y=sdf['score'],marker_color=colors))
        fig_s.update_layout(title="Sentimiento de noticias",template="plotly_dark",xaxis_tickangle=-45,height=300)
        st.plotly_chart(fig_s,use_container_width=True)
    else:
        st.info("No hay noticias disponibles.")

    # -----------------------------
    # ETF Finder
    # -----------------------------
    st.subheader("ETF Finder (temas)")
    tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)", key="etf_theme")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema) if tema else etf_screener(None)
        if etfs:
            st.table(pd.DataFrame(etfs))
        else:
            st.info("No se encontraron ETFs para ese tema (demo).")

    # -----------------------------
    # Comparación rápida
    # -----------------------------
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB = st.columns(2)
    with colA:
        t_a = st.text_input("Ticker A", ticker, key="cmp_a")
    with colB:
        t_b = st.text_input("Ticker B", "AAPL.US", key="cmp_b")
    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a,t_b)
        sent = compare_sentiment(t_a,t_b)
        st.markdown("**Indicadores (objeto):**")
        st.write(cmp)
        st.markdown("**Sentimiento:**")
        st.write(sent)

    # -----------------------------
    # Footer
    # -----------------------------
    st.markdown("---")
    if demo_mode:
        st.info("Mostrando datos de demo porque no hubo OHLC real o la API está limitada.")
    st.caption("AppFinanzAr — modo demo-friendly. Contacto: desarrollador para datos reales / keys.")

