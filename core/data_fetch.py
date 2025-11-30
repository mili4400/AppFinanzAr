# core/data_fetch.py
import requests
import pandas as pd
from datetime import date, timedelta
from .config import API_KEY, NEWS_DAYS_BACK
from core.eodhd_api import fetch_eodhd


def fetch_ohlc(ticker, from_date=None, to_date=None):
    url = f"https://eodhistoricaldata.com/api/eod/{ticker}?api_token={API_KEY}&fmt=json"
    if from_date and to_date:
        url += f"&from={from_date}&to={to_date}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        data = r.json()
        df = pd.DataFrame(data)
        for col in ["date","open","high","low","close","volume"]:
            if col not in df.columns:
                df[col] = pd.NA
        df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except:
        return pd.DataFrame()

def fetch_fundamentals(ticker):
    url = f"https://eodhistoricaldata.com/api/fundamentals/{ticker}?api_token={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {}, []
        data = r.json()
        fundamentals = data.get("Financials", {}).get("KeyRatios", {})
        competitors = data.get("Competitors", [])
        return fundamentals, competitors
    except:
        return {}, []

def fetch_news(ticker, days_back=NEWS_DAYS_BACK, translate_to_es=True):
    today = date.today()
    start = today - timedelta(days=days_back)
    url = f"https://eodhistoricaldata.com/api/news?symbol={ticker}&from={start}&to={today}&api_token={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        news = r.json()
        if translate_to_es:
            for n in news:
                n["title"] = translate_text(n.get("title",""), "es")
        return news
    except:
        return []

def translate_text(text, target_lang="es"):
    # Placeholder: reemplazar con API real de traducción si se desea
    return text


def fetch_historical_data(ticker, period="1y", interval="1d"):
    """
    Devuelve datos históricos OHLCV desde la API EODHD.
    Mantiene compatibilidad con el antiguo fetch_historical_data esperado por compare.py.
    """

    # Mapear periodos a días
    period_map = {
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825
    }

    days = period_map.get(period, 365)

    data = fetch_eodhd(
        endpoint="historical-prices",
        params={
            "s": ticker,
            "from": None,
            "to": None,
            "period": interval
        }
    )

    if not data:
        return []

    # Reducir tamaño según periodo solicitado
    return data[-days:]

