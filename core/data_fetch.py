# core/data_fetch.py
import requests
from datetime import date, timedelta
from .config import API_KEY, NEWS_DAYS_BACK

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

def fetch_news(ticker, days_back=NEWS_DAYS_BACK):
    today = date.today()
    start = today - timedelta(days=days_back)
    url = f"https://eodhistoricaldata.com/api/news?symbol={ticker}&from={start}&to={today}&api_token={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        return r.json()
    except:
        return []

