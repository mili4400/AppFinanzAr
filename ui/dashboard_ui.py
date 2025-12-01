# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# =========================================
# Importaciones core con fallback si falta
# =========================================
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
        # Genera demo completo para mostrar UI
        df_idx = pd.date_range(end=datetime.today(), periods=60, freq='D')
        prices = 100 + np.cumsum(np.random.randn(len(df_idx)))
        price_df = pd.DataFrame({
            "date": df_idx, "open": prices-1, "high": prices+1,
            "low": prices-2, "close": prices, "volume": 1000
        })
        return {
            "fundamentals": {"Revenue": 1.2e9, "Net Income": 2.5e8, "EPS": 3.45, "PE": 18.5},
            "competitors": ["COMP1", "COMP2", "COMP3", "COMP4", "COMP5"],
            "price": price_df,
            "news": [
                {"title":"Demo noticia positiva sobre "+ticker,"published_at":"2025-12-01"},
                {"title":"Demo noticia negativa sobre "+ticker,"published_at":"2025-11-30"},
            ],
            "sentiment_value": 0.2,
            "sentiment_label": "neutral",
            "fundamentals_summary": "Resumen demo: finanzas sólidas, crecimiento estable.",
            "executive_summary": {
                "name": ticker,
                "sector": "Tecnología",
                "industry": "Software",
                "country": "US",
                "valuation": {"pe_ratio": "18.5", "market_cap": "120B", "eps": "3.45"},
                "price_trend_30d": "2.5"
            }
        }

try:
    from core.etf_finder import etf_screener
except Exception:
    def etf_screener(theme):
        return [{"ETF":"DEMO1","Theme":"Tech"},{"ETF":"DEMO2","Theme":"Energy"}]

try:
    from core.favorites import load_favorites, add_favorite
except Exception:
    _demo_favs = {}
    def load_favorites(username):
        return {"all": _demo_favs.get(username, []), "categories": {}}
    def add_favorite(username, items):
        _demo_favs[username] = items
        return items

try:
    from core.compare_pro import compare_indicators, compare_sentiment
except Exception:
    def compare_indicators(a, b): return {"demo_indicator":"value"}
    def compare_sentiment(a, b): return {"sentiment_a":0.2,"sentiment_b":-0.1}

try:
    from core.utils import sma, ema, rsi
except Exception:
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
except Exception:
    def sentiment_score(text):
        t = (text or "").lower()
        if "up" in t or "good" in t or "positivo" in t: return 0.6
        if "down" in t or "bad" in t or "negativo" in t: return -0.6
        return 0.0

# ================================
# Config demo tickers
# ================================
DEMO_TICKERS = ["MSFT.US","AAPL.US","GOOGL.US","AMZN.US","GGAL.BA"]

# ================================
# Retro-compat sentiment
# ================================
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
    st.title("📊 AppFinanzAr – Dashboard PRO Demo")

    # ---------------- Sidebar ----------------
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español","English"])
        lang_code = "es" if lang=="Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username","demo")
        st.write(f"Usuario: **{username}**")

        # --- Favoritos ---
        if "favorites_list" not in st.session_state:
            st.session_state["favorites_list"] = load_favorites(username).get("all",[])

        if st.session_state["favorites_list"]:
            for f in st.session_state["favorites_list"]:
                col_f1,col_f2 = st.columns([4,1])
                with col_f1: st.write(f"• {f}")
                with col_f2:
                    if st.button("❌", key=f"del_{f}"):
                        st.session_state["favorites_list"].remove(f)
                        add_favorite(username, st.session_state["favorites_list"])
                        st.success(f"{f} eliminado de favoritos.")

        else:
            st.write("_Sin favoritos_")

        # Botón borrar todos
        if st.session_state["favorites_list"]:
            if st.button("🗑️ Borrar todos los favoritos"):
                st.session_state["favorites_list"] = []
                add_favorite(username, [])
                st.success("Todos los favoritos eliminados.")

        st.markdown("---")
        st.markdown("### Demo / Utilities")
        if "load_demo" not in st.session_state:
            st.session_state["load_demo"] = False
        if st.button("Cargar ejemplo demo"):
            st.session_state["dash_demo_ticker"] = DEMO_TICKERS[0]
            st.session_state["load_demo"] = True
            st.success(f"Cargando demo para {DEMO_TICKERS[0]}")

    # ---------------- Demo ticker aplicado al inicio ----------------
    if st.session_state.get("load_demo",False):
        st.session_state["dash_ticker_input"] = st.session_state.get("dash_demo_ticker",DEMO_TICKERS[0])
        st.session_state["load_demo"] = False

    # ---------------- Top controls: ticker input ----------------
    st.subheader("Búsqueda de activo")
    col1,col2 = st.columns([2,1])
    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state.get("dash_ticker_input","MSFT.US"), key="dash_ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa (opcional)","")

    ticker = ticker_input
    if company_search:
        try:
            results = search_ticker_by_name(company_search)
        except: results = []
        if results:
            ticker = st.selectbox(f"Resultados para {company_search}", results, index=0)
        else:
            st.warning("No se encontraron tickers; probá con el ticker directamente.")

    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", DEMO_TICKERS)
        if sel: ticker = sel

    # ---------------- Agregar ticker a favoritos ----------------
    st.markdown("### ⭐ Agregar a Favoritos")
    if st.button("Agregar este ticker a favoritos"):
        if ticker not in st.session_state["favorites_list"]:
            st.session_state["favorites_list"].append(ticker)
            add_favorite(username, st.session_state["favorites_list"])
            st.success(f"{ticker} agregado a favoritos.")
        else:
            st.info(f"{ticker} ya estaba en favoritos.")

    # ---------------- Date range ----------------
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

    # ---------------- Fetch data ----------------
    st.markdown("---")
    st.info(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")

    try:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    except: df = pd.DataFrame()

    # Demo si no hay datos
    if df.empty:
        idx = pd.date_range(end=datetime.today(), periods=60, freq='D')
        prices = 100 + np.cumsum(np.random.randn(len(idx)))
        df = pd.DataFrame({
            "date": idx, "open": prices-1, "high": prices+1,
            "low": prices-2, "close": prices, "volume":1000
        })
        demo_mode = True
    else:
        demo_mode = False

    # Indicators
    df["SMA20"] = sma(df["close"],20)
    df["SMA50"] = sma(df["close"],50)
    df["EMA20"] = ema(df["close"],20)
    df["RSI14"] = rsi(df["close"],14)

    # ---------------- Charts ----------------
    st.subheader("Gráfico de precios")
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"],
            low=df["low"], close=df["close"],
            increasing_line_color="green", decreasing_line_color="red", name="OHLC"
        )])
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
        fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
        fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
    except: st.error("Error dibujando gráfico de precios")

    # RSI
    st.subheader("RSI 14")
    try:
        rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
        rsi_fig.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
        st.plotly_chart(rsi_fig, use_container_width=True)
    except: pass

    # ---------------- Overview / fundamentals ----------------
    st.subheader("Overview / Resumen ejecutivo")
    overview = build_overview(ticker, lang=("es" if lang=="Español" else "en"))
    exec_sum = overview.get("executive_summary",{})
    card = f"""
**{exec_sum.get('name',ticker)}**  
Sector: {exec_sum.get('sector','N/A')}  • Industria: {exec_sum.get('industry','N/A')}  • País: {exec_sum.get('country','N/A')}

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')}  —  Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')}  —  EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}

**Tendencia 30d:** {exec_sum.get('price_trend_30d','N/A')}%  •  **Sentimiento:** {overview.get('sentiment_label','Sin datos')}

**Resumen:** {overview.get('fundamentals_summary','')}
"""
    st.markdown(card)

    # Fundamentales
    st.subheader("Fundamentales (clave)")
    fund = overview.get("fundamentals",{})
    if fund: st.dataframe(pd.DataFrame.from_dict(fund, orient="index", columns=["Valor"]))
    else: st.info("No se encontraron fundamentales.")

    # Competidores
    st.subheader("Competidores (máx 5)")
    comps = overview.get("competitors",[])
    if comps: st.write(", ".join(comps[:5]))
    else: st.info("No se encontraron competidores.")

    # Noticias y sentimiento
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news",[]) or []
    if news_items:
        simple = []
        for n in news_items[:10]:
            title = n.get("title","")[:200]
            published = n.get("published_at", n.get("date",""))
            score,label = analyze_sentiment_textblob(title)
            simple.append({"title":title,"date":published,"score":score,"label":label})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")
        sdf = pd.DataFrame(simple)
        try:
            colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
            fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['score'], marker_color=colors))
            fig_s.update_layout(title="Sentimiento de noticias (bar)", template="plotly_dark", xaxis_tickangle=-45, height=300)
            st.plotly_chart(fig_s, use_container_width=True)
        except: pass
    else:
        st.info("No hay noticias disponibles.")

    # ---------------- ETF Finder ----------------
    st.subheader("ETF Finder (temas)")
    tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)", key="etf_theme")
    if st.button("Buscar ETFs"):
        etfs = etf_screener(tema) if tema else etf_screener(None)
        if etfs: st.table(pd.DataFrame(etfs))
        else: st.info("No se encontraron ETFs.")

    # ---------------- Comparación rápida ----------------
    st.subheader("Comparación rápida (2 tickers)")
    colA,colB = st.columns(2)
    with colA: t_a = st.text_input("Ticker A", ticker, key="cmp_a")
    with colB: t_b = st.text_input("Ticker B","AAPL.US", key="cmp_b")
    if st.button("Comparar ahora"):
        cmp = compare_indicators(t_a,t_b)
        sent = compare_sentiment(t_a,t_b)
        st.markdown("**Indicadores (objeto):**")
        st.write(cmp)
        st.markdown("**Sentimiento:**")
        st.write(sent)

    # ---------------- Footer ----------------
    st.markdown("---")
    if demo_mode: st.info("Mostrando datos de demo, API real limitada o agotada.")
    st.caption("AppFinanzAr PRO — modo demo-friendly. Contacto: desarrollador para datos reales / keys.")
