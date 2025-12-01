# core/data_fetch.py
import os
import requests
import pandas as pd
from datetime import date, timedelta, datetime
from .config import API_KEY, NEWS_DAYS_BACK

# Intentar usar eodhd_api si existe en el proyecto
EOD_AVAILABLE = False
try:
    from core.eodhd_api import fetch_eodhd, eod_request  # funciones compatibles si existen
    EOD_AVAILABLE = True
except Exception:
    try:
        from core.eodhd_api import eod_request
        EOD_AVAILABLE = True
    except Exception:
        EOD_AVAILABLE = False

# -----------------------------
# FALLBACK DEMO DATA (para mostrar la app sin consumir la API)
# -----------------------------
DEMO_OHLC = {
    "MSFT.US": [
        {"date": (datetime.today() - pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
         "open": 300 + i*0.2, "high": 302 + i*0.2, "low": 299 + i*0.2, "close": 301 + i*0.2, "volume": 1000000}
        for i in range(60, -1, -1)
    ],
    "GGAL.BA": [
        {"date": (datetime.today() - pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
         "open": 90 + i*0.1, "high": 91 + i*0.1, "low": 89 + i*0.1, "close": 90.5 + i*0.1, "volume": 200000}
        for i in range(60, -1, -1)
    ]
}

DEMO_FUNDAMENTALS = {
    "MSFT.US": {
        "Name": "Microsoft Corporation",
        "Country": "USA",
        "Sector": "Technology",
        "Industry": "Software—Infrastructure",
        "MarketCapitalization": 2500000000000,
        "PERatio": 30.5,
        "EPS": 9.12,
        "ProfitMargin": 0.36,
        "EBITDA": 110000000000,
        "TotalAssets": 350000000000,
        "TotalLiabilities": 150000000000,
        "BookValue": 25.5,
        "Description": "Microsoft develops, licenses, and supports software, services, devices, and solutions worldwide."
    },
    "GGAL.BA": {
        "Name": "Grupo Financiero Galicia S.A.",
        "Country": "Argentina",
        "Sector": "Financial",
        "Industry": "Banks—Regional",
        "MarketCapitalization": 120000000000,
        "PERatio": 6.8,
        "EPS": 2.3,
        "ProfitMargin": 0.15,
        "EBITDA": None,
        "TotalAssets": None,
        "TotalLiabilities": None,
        "BookValue": None,
        "Description": "Banco y servicios financieros con fuerte presencia en Argentina."
    }
}

DEMO_NEWS = {
    "MSFT.US": [
        {"title": "Microsoft reports strong quarterly earnings", "content": "Microsoft beat expectations.", "published_at": (datetime.today()-pd.Timedelta(days=1)).isoformat()},
        {"title": "Azure growth accelerates", "content": "Cloud business continues to expand.", "published_at": (datetime.today()-pd.Timedelta(days=3)).isoformat()},
    ],
    "GGAL.BA": [
        {"title": "Grupo Galicia posts solid retail results", "content": "Positive numbers in consumer loans.", "published_at": (datetime.today()-pd.Timedelta(days=2)).isoformat()}
    ]
}

# -----------------------------
# UTILIDADES
# -----------------------------
def _to_df_from_json_list(json_list):
    try:
        df = pd.DataFrame(json_list)
        for col in ["date","open","high","low","close","volume"]:
            if col not in df.columns:
                df[col] = pd.NA
        df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

# -----------------------------
# OHLC HISTÓRICO
# -----------------------------
def fetch_ohlc(ticker, from_date=None, to_date=None):
    """
    Devuelve DataFrame OHLC. Intenta EODHD; si falla, usa DEMO para que la app muestre algo.
    """
    ticker_norm = ticker.upper()
    # 1) Si EOD disponible y API_KEY, usarlo (best-effort)
    if EOD_AVAILABLE and API_KEY:
        try:
            # Si fetch_eodhd existe, usarlo (espera lista de dicts)
            if "fetch_eodhd" in globals():
                data = fetch_eodhd(ticker_norm, interval="1d", limit=200)
                if data and isinstance(data, list):
                    return _to_df_from_json_list(data)
            # fallback a eod_request endpoints (por si existe)
            if "eod_request" in globals():
                res = eod_request(f"historical-prices/{ticker_norm}")
                if res and isinstance(res, list):
                    return _to_df_from_json_list(res)
        except Exception:
            pass

    # 2) DEMO fallback (no más consultas)
    if ticker_norm in DEMO_OHLC:
        return _to_df_from_json_list(DEMO_OHLC[ticker_norm])

    # 3) Intentar llamada pública de EODHD sin API (muy probable que falle), y si falla devolver vacío
    try:
        url = f"https://eodhistoricaldata.com/api/eod/{ticker_norm}?fmt=json"
        if API_KEY:
            url += f"&api_token={API_KEY}"
        if from_date and to_date:
            url += f"&from={from_date}&to={to_date}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return _to_df_from_json_list(r.json())
    except Exception:
        pass

    return pd.DataFrame()

# -----------------------------
# FUNDAMENTALES
# -----------------------------
def fetch_fundamentals(ticker):
    """
    Devuelve (fundamentals_dict, competitors_list).
    Usa EODHD si hay key/función; si no, fallback DEMO.
    """
    ticker_norm = ticker.upper()
    # 1) Intentar EODHD
    if EOD_AVAILABLE and API_KEY:
        try:
            # usar eod_request si está
            if "eod_request" in globals():
                res = eod_request(f"fundamentals/{ticker_norm}")
                # estructura EODHD -> extraer de forma segura
                if res and isinstance(res, dict):
                    # extracciones seguras
                    general = res.get("General", {})
                    highlights = res.get("Highlights", {})
                    balance = res.get("Financials", {}).get("BalanceSheet", {})
                    fundamentals = {
                        "Name": general.get("Name") or general.get("LongName") or ticker_norm,
                        "Country": general.get("Country"),
                        "Sector": general.get("Sector"),
                        "Industry": general.get("Industry"),
                        "MarketCapitalization": highlights.get("MarketCapitalization"),
                        "PERatio": highlights.get("PERatio"),
                        "EPS": highlights.get("EPS"),
                        "ProfitMargin": highlights.get("ProfitMargin"),
                        "EBITDA": highlights.get("EBITDA"),
                        "TotalAssets": balance.get("totalAssets") if isinstance(balance, dict) else None,
                        "TotalLiabilities": balance.get("totalLiab") if isinstance(balance, dict) else None,
                        "BookValue": balance.get("totalStockholderEquity") if isinstance(balance, dict) else None,
                        "Description": general.get("Description")
                    }
                    comps = res.get("Competitors", []) or []
                    return fundamentals, comps[:10]
            # si fetch_general endpoints existen, puedes añadir aquí otras llamadas
        except Exception:
            pass

    # 2) DEMO fallback
    if ticker_norm in DEMO_FUNDAMENTALS:
        demo = DEMO_FUNDAMENTALS[ticker_norm]
        # devolver lista de competidores vacía si no existe
        return demo, []

    # 3) Si no hay nada, devolver dict vacío y lista vacía
    return {}, []

# -----------------------------
# NOTICIAS
# -----------------------------
def fetch_news(ticker, days_back=NEWS_DAYS_BACK, translate_to_es=True):
    """
    Intenta EODHD -> fallback demo -> [].
    Devuelve lista de dicts con keys: title, content, published_at.
    """
    ticker_norm = ticker.upper()
    # 1) EODHD
    if EOD_AVAILABLE and API_KEY:
        try:
            if "eod_request" in globals():
                start = (date.today() - timedelta(days=days_back)).isoformat()
                end = date.today().isoformat()
                res = eod_request(f"news?symbols={ticker_norm}&from={start}&to={end}")
                # eodhd puede devolver lista o dict con "data"
                if isinstance(res, dict) and res.get("data"):
                    items = res["data"]
                elif isinstance(res, list):
                    items = res
                else:
                    items = []
                # normalizar a formato sencillo
                news = []
                for it in items[:50]:
                    title = it.get("title") or it.get("headline") or ""
                    content = it.get("content") or it.get("description") or ""
                    published = it.get("published_at") or it.get("date") or datetime.now().isoformat()
                    news.append({"title": title, "content": content, "published_at": published})
                if translate_to_es:
                    # placeholder: no translate API para evitar llamadas extra
                    for n in news:
                        n["title"] = n["title"]
                return news
        except Exception:
            pass

    # 2) DEMO
    if ticker_norm in DEMO_NEWS:
        return DEMO_NEWS[ticker_norm]

    return []

# -----------------------------
# HISTÓRICO COMPATIBLE / UTIL
# -----------------------------
def fetch_historical_data(ticker, period="1y", interval="1d"):
    """
    Mantiene compatibilidad con el antiguo compare.py.
    Devuelve lista de dicts o lista vacía.
    """
    period_map = {"1m":30,"3m":90,"6m":180,"1y":365,"2y":730,"5y":1825}
    days = period_map.get(period, 365)

    # 1) si fetch_eodhd disponible, pedir limit=days
    if EOD_AVAILABLE and API_KEY and "fetch_eodhd" in globals():
        try:
            data = fetch_eodhd(ticker, interval=interval, limit=days)
            if isinstance(data, list):
                return data
        except Exception:
            pass

    # 2) intentar usar fetch_ohlc y convertir a lista de dicts (lo más seguro)
    df = fetch_ohlc(ticker)
    if df is not None and not df.empty:
        # tomar últimos `days` rows
        df2 = df.tail(days).copy()
        return df2.to_dict(orient="records")

    # 3) fallback vacío
    return []

# -----------------------------
# BUSQUEDA POR NOMBRE DE EMPRESA (autocompletado local)
# -----------------------------
def search_ticker_by_name(company_name, max_results=10):
    """
    Búsqueda local + EOD best-effort. NO usa AlphaVantage.
    - Primero busca en una lista local mínima (rápida y sin uso de API).
    - Si EOD está disponible, intenta usar su endpoint de búsqueda.
    """
    if not company_name or not company_name.strip():
        return []

    q = company_name.strip().lower()

    # Lista local (puedes ampliar): (nombre_fragmento -> ticker)
    local_index = {
        "microsoft": "MSFT.US",
        "msft": "MSFT.US",
        "galicia": "GGAL.BA",
        "ggal": "GGAL.BA",
        "mercadolibre": "MELI.US",
        "amazon": "AMZN.US",
        "apple": "AAPL.US",
        "google": "GOOGL.US",
        "tesla": "TSLA.US"
    }

    results = []
    for name_part, tk in local_index.items():
        if q in name_part:
            results.append(tk)
    # si hay resultados locales, retornarlos de inmediato (prioridad)
    if results:
        return results[:max_results]

    # Si EOD disponible, intentar un screener o búsqueda
    if EOD_AVAILABLE and API_KEY:
        try:
            # uso best-effort: endpoint puede variar según plan
            res = None
            if "eod_request" in globals():
                res = eod_request(f"screener?keywords={company_name}&limit={max_results}")
            if res:
                # normalizar resultados si vienen en data
                items = res.get("data") if isinstance(res, dict) and res.get("data") else res
                tickers = []
                for it in items[:max_results]:
                    code = it.get("code") or it.get("symbol") or it.get("ticker")
                    if code:
                        tickers.append(code)
                if tickers:
                    return tickers
        except Exception:
            pass

    # si no se encontró nada, devolver lista vacía
    return []
