# ui/dashboard_ui.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# Intenta importar las funciones que ya tenés en core.
# Si faltan, el código seguirá funcionando con fallbacks.
try:
    from core.data_fetch import fetch_ohlc, fetch_fundamentals, fetch_news, search_ticker_by_name
except Exception:
    # Proporcionar fallbacks si no existen
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
            "fundamentals": {},
            "competitors": [],
            "price": pd.DataFrame(),
            "news": [],
            "sentiment_value": 0,
            "sentiment_label": "Sin datos",
            "fundamentals_summary": "",
            "executive_summary": {
                "name": ticker,
                "sector": "N/A",
                "industry": "N/A",
                "country": "N/A",
                "valuation": {"pe_ratio": "N/A", "market_cap": "N/A", "eps": "N/A"},
                "price_trend_30d": "N/A"
            }
        }

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
        # fallback superficial: positivo si contiene "up", negativo si "down"
        t = (text or "").lower()
        if "up" in t or "good" in t or "positivo" in t:
            return 0.6
        if "down" in t or "bad" in t or "negativo" in t:
            return -0.6
        return 0.0

# Small demo universe used when APIs are rate-limited or missing.
DEMO_TICKERS = [
    "MSFT.US", "AAPL.US", "GOOGL.US", "AMZN.US", "GGAL.BA"
]

# ================================
# Retro-compat: function dashboard expects
# ================================
def analyze_sentiment_textblob(text: str):
    """Compat wrapper: dashboard used to call this; now use sentiment_score."""
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
    st.title("📊 AppFinanzAr – Dashboard (Demo friendly)")

    # Sidebar: idioma + usuario + favorites + quick actions
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        lang = st.selectbox("Idioma / Language", ["Español", "English"])
        lang_code = "es" if lang == "Español" else "en"

        st.markdown("---")
        st.markdown("### 👤 Sesión / Favoritos")
        username = st.session_state.get("username", "demo")
        st.write(f"Usuario: **{username}**")

        favs = load_favorites(username)
        if not isinstance(favs, dict):
            favs = {"all": favs or [], "categories": {}}
        favs.setdefault("all", [])
        favs.setdefault("categories", {})

        st.markdown("**Favoritos**")
        if favs["all"]:
            for f in favs["all"]:
                st.write(f"• {f}")
        else:
            st.write("_Sin favoritos_")

        st.markdown("---")
        st.markdown("### Demo / Utilities")
        if st.button("Cargar ejemplo demo"):
            # rellena sesión con un ticker demo para mostrar UI
            st.session_state["dash_demo_ticker"] = DEMO_TICKERS[0]
            st.experimental_rerun()

    # Top controls: Ticker input + search by company name
    st.subheader("Búsqueda de activo")
    col1, col2 = st.columns([2, 1])

    with col1:
        ticker_input = st.text_input("Ticker (ej: MSFT.US)", st.session_state.get("dash_demo_ticker", "MSFT.US"), key="dash_ticker_input")
    with col2:
        company_search = st.text_input("Buscar por nombre de empresa (opcional)", "")

    # Try to get search results using search_ticker_by_name (if available)
    ticker = ticker_input
    if company_search:
        try:
            results = search_ticker_by_name(company_search)
        except Exception:
            results = []
        if results:
            ticker = st.selectbox("Resultados para '"+company_search+"'", results, index=0)
        else:
            st.warning("No se encontraron tickers con esa búsqueda; probá con el ticker directamente.")

    # Quick alternate: show demo suggestions (simple autocomplete substitute)
    if st.checkbox("Mostrar sugerencias demo"):
        sel = st.selectbox("Sugerencias", DEMO_TICKERS)
        if sel:
            ticker = sel

    # Date range controls
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
    # FETCH DATA (con manejo de errores)
    # -----------------------------
    st.markdown("---")
    st.info(f"Mostrando datos para: **{ticker}** — rango {start_date} → {end_date}")

    try:
        df = fetch_ohlc(ticker, from_date=start_date, to_date=end_date)
    except Exception:
        df = pd.DataFrame()

    # If OHLC is empty, try fallback demo: small synthetic data so charts render
    if df is None or df.empty:
        # Create tiny demo timeseries for UI preview
        idx = pd.date_range(end=datetime.today(), periods=60, freq='D')
        import numpy as _np
        prices = 100 + _np.cumsum(_np.random.randn(len(idx)))
        df = pd.DataFrame({"date": idx, "open": prices-1, "high": prices+1, "low": prices-2, "close": prices, "volume": 1000})
        df.reset_index(drop=True, inplace=True)
        demo_mode = True
    else:
        demo_mode = False

    # Indicators (safe)
    try:
        df["SMA20"] = sma(df["close"], 20)
        df["SMA50"] = sma(df["close"], 50)
        df["EMA20"] = ema(df["close"], 20)
        df["RSI14"] = rsi(df["close"], 14)
    except Exception:
        # If utilities misbehave, create simple columns
        df["SMA20"] = pd.NA
        df["SMA50"] = pd.NA
        df["EMA20"] = pd.NA
        df["RSI14"] = pd.NA

    # -----------------------------
    # CHART: Candlestick + indicators
    # -----------------------------
    st.subheader("Gráfico de precios")
    try:
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            increasing_line_color="green", decreasing_line_color="red", name="OHLC"
        )])
        if "SMA20" in df.columns and df["SMA20"].notna().any():
            fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], mode="lines", name="SMA20"))
        if "SMA50" in df.columns and df["SMA50"].notna().any():
            fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], mode="lines", name="SMA50"))
        if "EMA20" in df.columns and df["EMA20"].notna().any():
            fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20"))
        fig.update_layout(height=520, template="plotly_dark", margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("No se pudo dibujar el gráfico de precios: " + str(e))

    # RSI small chart
    if "RSI14" in df.columns:
        st.subheader("RSI 14")
        try:
            rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
            rsi_fig.update_layout(height=200, template="plotly_dark", margin=dict(t=10))
            st.plotly_chart(rsi_fig, use_container_width=True)
        except:
            pass

    # -----------------------------
    # OVERVIEW (tarjeta compacta)
    # -----------------------------
    st.subheader("Overview / Resumen ejecutivo")
    try:
        overview = build_overview(ticker, lang=("es" if lang=="Español" else "en"))
    except Exception:
        overview = build_overview(ticker)  # fallback

    exec_sum = overview.get("executive_summary", {})
    card = f"""
**{exec_sum.get('name', ticker)}**  
Sector: {exec_sum.get('sector','N/A')}  •  Industria: {exec_sum.get('industry','N/A')}  •  País: {exec_sum.get('country','N/A')}

**Valuación:** P/E: {exec_sum.get('valuation',{}).get('pe_ratio','N/A')}  —  Market Cap: {exec_sum.get('valuation',{}).get('market_cap','N/A')}  —  EPS: {exec_sum.get('valuation',{}).get('eps','N/A')}

**Tendencia 30d:** {exec_sum.get('price_trend_30d','N/A')}%  •  **Sentimiento:** {overview.get('sentiment_label','Sin datos')}

**Resumen:** {overview.get('fundamentals_summary','')}
"""
    st.markdown(card)

    # Fundamentales tabla
    st.subheader("Fundamentales (clave)")
    fund = overview.get("fundamentals", {})
    if fund:
        try:
            st.dataframe(pd.DataFrame.from_dict(fund, orient="index", columns=["Valor"]))
        except Exception:
            st.write(fund)
    else:
        st.info("No se encontraron fundamentales válidos.")

    # Competidores
    st.subheader("Competidores (máx 5)")
    comps = overview.get("competitors", []) or []
    if comps:
        st.write(", ".join(comps[:5]))
    else:
        st.info("No se encontraron competidores.")

    # -----------------------------
    # Noticias + sentimiento simplificado
    # -----------------------------
    st.subheader("Noticias recientes (y sentimiento)")
    news_items = overview.get("news", []) or []
    if not news_items:
        # try direct fetch if overview didn't include news
        try:
            news_items = fetch_news(ticker) or []
        except:
            news_items = []

    if news_items:
        simple = []
        for n in news_items[:10]:
            title = n.get("title", "")[:200]
            published = n.get("published_at", n.get("date", ""))
            score, label = analyze_sentiment_textblob(title)
            simple.append({"title": title, "date": published, "score": score, "label": label})
            st.write(f"- **{title}** ({published}) → *{label}* ({score:.2f})")

        sdf = pd.DataFrame(simple)
        try:
            colors = sdf['score'].apply(lambda x: "green" if x>0 else "red" if x<0 else "gray")
            fig_s = go.Figure(go.Bar(x=sdf['title'], y=sdf['score'], marker_color=colors))
            fig_s.update_layout(title="Sentimiento de noticias (bar)", template="plotly_dark", xaxis_tickangle=-45, height=300)
            st.plotly_chart(fig_s, use_container_width=True)
        except:
            pass
    else:
        st.info("No hay noticias disponibles.")

    # -----------------------------
    # ETF Finder (simple)
    # -----------------------------
    st.subheader("ETF Finder (temas)")
    tema = st.text_input("Buscar ETFs por tema (ej: energy, metals, tech)", key="etf_theme")
    if st.button("Buscar ETFs"):
        try:
            etfs = etf_screener(tema) if tema else etf_screener(None)
        except Exception:
            etfs = []
        if etfs:
            st.table(pd.DataFrame(etfs))
        else:
            st.info("No se encontraron ETFs para ese tema (o demo activo).")

    # -----------------------------
    # Comparación entre dos tickers (rápida)
    # -----------------------------
    st.subheader("Comparación rápida (2 tickers)")
    colA, colB = st.columns(2)
    with colA:
        t_a = st.text_input("Ticker A", ticker, key="cmp_a")
    with colB:
        t_b = st.text_input("Ticker B", "AAPL.US", key="cmp_b")

    if st.button("Comparar ahora"):
        try:
            cmp = compare_indicators(t_a, t_b)
            sent = compare_sentiment(t_a, t_b)
            st.markdown("**Indicadores (objeto):**")
            st.write(cmp)
            st.markdown("**Sentimiento:**")
            st.write(sent)
        except Exception as e:
            st.error("Error comparando: " + str(e))

    # -----------------------------
    # Footer notes
    # -----------------------------
    st.markdown("---")
    if demo_mode:
        st.info("Mostrando datos de demo porque no hubo OHLC real disponibles o la API está limitada.")
    st.caption("AppFinanzAr — modo demo-friendly. Contacto: desarrollador para ajustar datos reales / keys.")



