import requests
from datetime import date, timedelta
import streamlit as st
from .config import API_KEY, NEWS_DAYS_BACK

# -------------------------
# Fetch fundamentals + competitors
# -------------------------
@st.cache_data(ttl=3600)
def fetch_fundamentals(ticker: str):
    """
    Trae fundamentales clave y competidores de un ticker usando EODHD
    """
    if not API_KEY:
        st.error("API_KEY no configurada en core/config.py o secrets")
        return {}, []

    url = f"https://eodhistoricaldata.com/api/fundamentals/{ticker}?api_token={API_KEY}&fmt=json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.warning(f"No se pudieron obtener fundamentales para {ticker}: {e}")
        return {}, []

    # Fundamentales clave
    key_fundamentals = {}
    if "Financials" in data and "KeyRatios" in data["Financials"]:
        key_fundamentals = data["Financials"]["KeyRatios"]

    # Competidores
    competitors = data.get("Competitors", [])

    return key_fundamentals, competitors

# -------------------------
# Fetch news
# -------------------------
@st.cache_data(ttl=1800)
def fetch_news(ticker: str, days_back: int = NEWS_DAYS_BACK):
    """
    Trae noticias recientes de un ticker en el rango definido
    """
    if not API_KEY:
        st.error("API_KEY no configurada en core/config.py o secrets")
        return []

    today = date.today()
    start_date = today - timedelta(days=days_back)

    url = f"https://eodhistoricaldata.com/api/news?symbol={ticker}&from={start_date}&to={today}&api_token={API_KEY}&fmt=json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news = response.json()
        if not isinstance(news, list):
            return []
        return news
    except Exception as e:
        st.warning(f"No se pudieron obtener noticias para {ticker}: {e}")
        return []

# -------------------------
# Fetch historical OHLC
# -------------------------
@st.cache_data(ttl=1800)
def fetch_eod_ohlc(ticker: str, from_date: str = None, to_date: str = None):
    """
    Trae datos OHLC diarios de un ticker
    """
    if not API_KEY:
        st.error("API_KEY no configurada en core/config.py o secrets")
        return None

    url = f"https://eodhistoricaldata.com/api/eod/{ticker}?api_token={API_KEY}&fmt=json"
    if from_date and to_date:
        url += f"&from={from_date}&to={to_date}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        return data
    except Exception as e:
        st.warning(f"No se pudieron obtener datos OHLC para {ticker}: {e}")
        return None

# -------------------------
# Fetch real-time snapshot
# -------------------------
@st.cache_data(ttl=60)
def fetch_realtime(ticker: str):
    """
    Trae un snapshot real-time rápido
    """
    if not API_KEY:
        return None

    url = f"https://eodhistoricaldata.com/api/real-time/{ticker}?api_token={API_KEY}&fmt=json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

