# core/data_fetch.py
import requests
import pandas as pd
from datetime import date, timedelta
from .config import API_KEY, NEWS_DAYS_BACK
from core.eodhd_api import fetch_eodhd

# -----------------------------
# OHLC HISTÓRICO
# -----------------------------
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

# -----------------------------
# FUNDAMENTALES
# -----------------------------
def fetch_fundamentals(ticker):
    url = f"https://eodhistoricaldata.com/api/fundamentals/{ticker}?api_token={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {}, []
        data = r.json()
        fundamentals = {
            "Name": data.get("General", {}).get("Name"),
            "Country": data.get("General", {}).get("Country"),
            "Sector": data.get("General", {}).get("Sector"),
            "Industry": data.get("General", {}).get("Industry"),
            "MarketCapitalization": data.get("Highlights", {}).get("MarketCapitalization"),
            "PERatio": data.get("Highlights", {}).get("PERatio"),
            "EPS": data.get("Highlights", {}).get("EPS"),
            "ProfitMargin": data.get("Highlights", {}).get("ProfitMargin"),
            "EBITDA": data.get("Highlights", {}).get("EBITDA"),
            "TotalAssets": data.get("Financials", {}).get("BalanceSheet", {}).get("totalAssets"),
            "TotalLiabilities": data.get("Financials", {}).get("BalanceSheet", {}).get("totalLiab"),
            "BookValue": data.get("Financials", {}).get("BalanceSheet", {}).get("totalStockholderEquity"),
            "Description": data.get("General", {}).get("Description")
        }
        competitors = data.get("Competitors", [])[:5]  # máximo 5
        return fundamentals, competitors
    except:
        return {}, []

# -----------------------------
# NOTICIAS
# -----------------------------
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

# -----------------------------
# HISTÓRICO COMPATIBLE
# -----------------------------
def fetch_historical_data(ticker, period="1y", interval="1d"):
    period_map = {"1m":30,"3m":90,"6m":180,"1y":365,"2y":730,"5y":1825}
    days = period_map.get(period, 365)
    data = fetch_eodhd(ticker, interval=interval, limit=days)
    if not data or not isinstance(data, list):
        return []
    return data

# -----------------------------
# BÚSQUEDA POR NOMBRE DE EMPRESA
# -----------------------------
def search_ticker_by_name(company_name, max_results=10):
    """
    Retorna lista de tickers que coinciden con un nombre de empresa.
    Solo usa EODHD (no Alpha Vantage).
    """
    from core.eodhd_api import eod_request
    try:
        query = f"search-symbol?query={company_name}&limit={max_results}"
        data = eod_request(query)
        if not data or "data" not in data:
            return []
        return [item["code"] for item in data["data"]][:max_results]
    except:
        return []
