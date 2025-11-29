# core/data_fetch.py
import requests
from datetime import date, timedelta
from .config import API_KEY, NEWS_DAYS_BACK

def fetch_fundamentals(ticker):
    """
    Trae fundamentales clave y competidores de un ticker usando EODHD
    """
    url = f"https://eodhistoricaldata.com/api/fundamentals/{ticker}?api_token={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return {}, []

    data = response.json()

    # Fundamentales clave
    key_fundamentals = {}
    if "Financials" in data and "KeyRatios" in data["Financials"]:
        key_fundamentals = data["Financials"]["KeyRatios"]

    # Competidores
    competitors = data.get("Competitors", [])

    return key_fundamentals, competitors


def fetch_news(ticker, days_back=NEWS_DAYS_BACK):
    """
    Trae noticias recientes de un ticker en el rango definido
    """
    today = date.today()
    start_date = today - timedelta(days=days_back)

    url = f"https://eodhistoricaldata.com/api/news?symbol={ticker}&from={start_date}&to={today}&api_token={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return []

    return response.json()
