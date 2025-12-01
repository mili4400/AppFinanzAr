# core/data_fetch.py
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from .config import API_KEY, NEWS_DAYS_BACK

# Try to import helper from core.eodhd_api if present
try:
    from core.eodhd_api import fetch_eodhd, eod_request
    EOD_AVAILABLE = True
except Exception:
    fetch_eodhd = None
    eod_request = None
    EOD_AVAILABLE = False

# Demo fallback tickers & minimal metadata (used when no API_KEY or when API fails)
_DEMO_TICKERS = {
    "MSFT.US": {"name": "Microsoft Corp", "exchange": "XNAS", "country": "USA", "sector": "Technology"},
    "AAPL.US": {"name": "Apple Inc", "exchange": "XNAS", "country": "USA", "sector": "Technology"},
    "AMZN.US": {"name": "Amazon.com Inc", "exchange": "XNAS", "country": "USA", "sector": "Consumer Discretionary"},
    "MELI.US": {"name": "MercadoLibre, Inc.", "exchange": "XNAS", "country": "ARG/USA", "sector": "E-Commerce"},
    "GGAL.BA": {"name": "Grupo Financiero Galicia", "exchange": "BCBA", "country": "AR", "sector": "Financials"}
}

# -----------------------------
# OHLC HISTÓRICO
# -----------------------------
def fetch_ohlc(ticker, from_date=None, to_date=None):
    """
    Devuelve DataFrame OHLC con columnas mínimas:
      date, open, high, low, close, volume
    Usa EODHD si hay API_KEY; si no, genera demo/synthetic data (últimos 365 días por defecto).
    """
    # Normalize ticker param
    t = str(ticker).upper()

    # If EODHD available and API_KEY present, try real request
    if API_KEY and EOD_AVAILABLE and fetch_eodhd is not None:
        try:
            # Use fetch_eodhd wrapper (expected to return list of dicts or similar)
            # We request daily and a wide limit to cover date range
            limit = 2000
            raw = fetch_eodhd(ticker=t, interval="1d", limit=limit) if callable(fetch_eodhd) else None
            if raw and isinstance(raw, list):
                df = pd.DataFrame(raw)
                # try to normalize column names
                for c in list(df.columns):
                    # common keys: date, close, open, high, low, volume
                    pass
                # ensure required columns
                for col in ["date", "open", "high", "low", "close", "volume"]:
                    if col not in df.columns:
                        # try some common alternatives
                        if col == "date" and "datetime" in df.columns:
                            df.rename(columns={"datetime": "date"}, inplace=True)
                        else:
                            df[col] = pd.NA
                df["date"] = pd.to_datetime(df["date"])
                df.sort_values("date", inplace=True)
                df.reset_index(drop=True, inplace=True)

                # Filter by from_date / to_date if provided
                if from_date:
                    df = df[df["date"] >= pd.to_datetime(from_date)]
                if to_date:
                    df = df[df["date"] <= pd.to_datetime(to_date)]
                return df
        except Exception:
            # best-effort: fall through to demo generator
            pass

    # FALLBACK DEMO: generate synthetic OHLC for period
    try:
        # default to 365 days if not provided
        if to_date is None:
            to_dt = datetime.today().date()
        else:
            to_dt = pd.to_datetime(to_date).date()
        if from_date is None:
            from_dt = to_dt - timedelta(days=365)
        else:
            from_dt = pd.to_datetime(from_date).date()

        days = (to_dt - from_dt).days
        if days <= 0:
            days = 30
            from_dt = to_dt - timedelta(days=days)

        dates = pd.date_range(start=from_dt, end=to_dt, freq='D')
        n = len(dates)
        # seed based on ticker so demo is reproducible
        seed = abs(hash(t)) % (2**32)
        rng = np.random.default_rng(seed)
        base = 100 + (seed % 200)  # base price per ticker

        # create walk
        steps = rng.normal(loc=0.0005, scale=0.02, size=n)
        price = base * np.cumprod(1 + steps)
        open_ = price * (1 + rng.normal(0, 0.002, size=n))
        close = price
        high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.01, size=n)))
        low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.01, size=n)))
        volume = (rng.integers(1000, 1000000, size=n)).tolist()

        df = pd.DataFrame({
            "date": dates,
            "open": open_.round(2),
            "high": high.round(2),
            "low": low.round(2),
            "close": close.round(2),
            "volume": volume
        })
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

# -----------------------------
# FUNDAMENTALES
# -----------------------------
def fetch_fundamentals(ticker):
    """
    Retorna (fundamentals_dict, competitors_list).
    Intenta EODHD si hay API_KEY; si falla o no hay key, devuelve demo minimal.
    """
    t = str(ticker).upper()

    # If EODHD available
    if API_KEY and EOD_AVAILABLE and eod_request is not None:
        try:
            res = eod_request(f"fundamentals/{t}")
            if res:
                # try to extract human friendly fields (best-effort)
                data = {}
                g = res.get("General", {}) if isinstance(res, dict) else {}
                h = res.get("Highlights", {}) if isinstance(res, dict) else {}
                bs = res.get("Financials", {}).get("BalanceSheet", {}) if isinstance(res, dict) else {}

                data["Name"] = g.get("Name") or g.get("LongName") or t
                data["Country"] = g.get("Country")
                data["Sector"] = g.get("Sector")
                data["Industry"] = g.get("Industry")
                data["MarketCapitalization"] = h.get("MarketCapitalization")
                data["PERatio"] = h.get("PERatio")
                data["EPS"] = h.get("EPS")
                data["ProfitMargin"] = h.get("ProfitMargin")
                data["EBITDA"] = h.get("EBITDA")
                data["TotalAssets"] = bs.get("totalAssets")
                data["TotalLiabilities"] = bs.get("totalLiab")
                data["BookValue"] = bs.get("totalStockholderEquity")
                data["Description"] = g.get("Description") or g.get("LongBusinessSummary")
                competitors = res.get("Competitors", []) or []
                # ensure list of strings
                competitors = [c for c in competitors if isinstance(c, str)][:10]
                return data, competitors
        except Exception:
            pass

    # FALLBACK DEMO fundamental
    demo = _DEMO_TICKERS.get(t, None)
    if demo:
        fundamentals = {
            "Name": demo.get("name"),
            "Country": demo.get("country"),
            "Sector": demo.get("sector"),
            "Industry": demo.get("sector"),
            "MarketCapitalization": None,
            "PERatio": None,
            "EPS": None,
            "ProfitMargin": None,
            "EBITDA": None,
            "TotalAssets": None,
            "TotalLiabilities": None,
            "BookValue": None,
            "Description": f"Demo data for {demo.get('name')}"
        }
        # pick a few other demo tickers as competitors
        comps = [k for k in _DEMO_TICKERS.keys() if k != t][:5]
        return fundamentals, comps

    # ultimate fallback: empty
    return {}, []

# -----------------------------
# NOTICIAS
# -----------------------------
def fetch_news(ticker, days_back=NEWS_DAYS_BACK, translate_to_es=True):
    """
    Devuelve lista de noticias (cada item: title, content, published_at, source)
    Usa EODHD news endpoint si hay API; si no, crea un par de titulares demo.
    """
    t = str(ticker).upper()
    if API_KEY and EOD_AVAILABLE and eod_request is not None:
        try:
            today = date.today()
            start = today - timedelta(days=days_back)
            q = f"news?symbol={t}&from={start}&to={today}"
            res = eod_request(q)
            if res and isinstance(res, list):
                # standardize items
                out = []
                for item in res:
                    out.append({
                        "title": item.get("title") or item.get("headline"),
                        "content": item.get("description") or item.get("content") or "",
                        "published_at": item.get("date") or item.get("published_at") or item.get("datetime"),
                        "source": item.get("source") or item.get("provider")
                    })
                # optional translation step left to caller
                return out
            # some EOD plans return dict with data
            if res and isinstance(res, dict) and res.get("data"):
                out = []
                for item in res["data"]:
                    out.append({
                        "title": item.get("title"),
                        "content": item.get("description",""),
                        "published_at": item.get("date"),
                        "source": item.get("source")
                    })
                return out
        except Exception:
            pass

    # FALLBACK demo news
    now = datetime.utcnow()
    demo_news = [
        {"title": f"{ticker} - Demo headline: results beat expectations",
         "content": f"Demo content about {ticker}. Earnings and outlook discussed.",
         "published_at": (now - timedelta(days=1)).isoformat()},
        {"title": f"{ticker} - Demo headline: market reaction muted",
         "content": f"Demo content about {ticker}. Market shows limited reaction.",
         "published_at": (now - timedelta(days=3)).isoformat()},
    ]
    # If translate_to_es True we leave translation to caller (or keep as-is)
    return demo_news

# -----------------------------
# HISTÓRICO COMPATIBLE
# -----------------------------
def fetch_historical_data(ticker, period="1y", interval="1d"):
    """
    Mantiene compatibilidad con el antiguo fetch_historical_data.
    period: "1m","3m","6m","1y","2y","5y"
    interval: "1d", "1wk", etc. (best-effort)
    """
    period_map = {"1m":30,"3m":90,"6m":180,"1y":365,"2y":730,"5y":1825}
    days = period_map.get(period, 365)

    # Prefer EODHD helper
    if API_KEY and EOD_AVAILABLE and fetch_eodhd is not None:
        try:
            data = fetch_eodhd(ticker, interval=interval, limit=days)
            if data and isinstance(data, list):
                return data
        except Exception:
            pass

    # fallback: use fetch_ohlc and return as list of dicts
    df = fetch_ohlc(ticker, from_date=(datetime.today().date() - timedelta(days=days)), to_date=datetime.today().date())
    if df is None or df.empty:
        return []
    # convert DataFrame to list of dicts with minimal keys
    out = df.sort_values("date").to_dict(orient="records")
    return out

# -----------------------------
# BÚSQUEDA POR NOMBRE DE EMPRESA (SIMPLE)
# -----------------------------
def search_ticker_by_name(company_name, max_results=10):
    """
    Busca tickers por nombre de empresa.
    - Si EODHD disponible, intenta un endpoint 'search' (best-effort).
    - Si no, hace búsqueda local en _DEMO_TICKERS por substring.
    """
    q = (company_name or "").strip()
    if not q:
        return []

    # Try EODHD search endpoint if available
    if API_KEY and EOD_AVAILABLE and eod_request is not None:
        try:
            # EODHD may have endpoints like "search" or "ticker-search" depending on plan;
            # try common names (best-effort).
            for ep in [f"search?query={q}", f"search?keywords={q}", f"screener?keywords={q}&type=stock"]:
                try:
                    res = eod_request(ep)
                    if not res:
                        continue
                    # handle list or dict with 'data'
                    candidates = []
                    if isinstance(res, list):
                        candidates = res
                    elif isinstance(res, dict) and res.get("data"):
                        candidates = res["data"]
                    # extract codes
                    tickers = []
                    for item in candidates:
                        if isinstance(item, dict):
                            code = item.get("code") or item.get("symbol") or item.get("ticker")
                            name = item.get("name") or item.get("longName")
                            if code:
                                tickers.append(f"{code}")
                    if tickers:
                        return tickers[:max_results]
                except Exception:
                    continue
        except Exception:
            pass

    # Local substring search over demo list
    results = []
    qlow = q.lower()
    for tk, meta in _DEMO_TICKERS.items():
        if qlow in tk.lower() or qlow in (meta.get("name") or "").lower():
            results.append(tk)
    # If nothing, try returning tickers whose names contain any token
    if not results:
        tokens = qlow.split()
        for tk, meta in _DEMO_TICKERS.items():
            name = (meta.get("name") or "").lower()
            if any(tok in name for tok in tokens):
                results.append(tk)
    return results[:max_results]
