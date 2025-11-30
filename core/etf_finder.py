# core/etf_finder.py
import json
import os
from datetime import datetime, timedelta

# Intentará usar eodhd para obtener metadata; si no existe, usa local DB
try:
    from core.eodhd_api import eod_request
    EOD_AVAILABLE = True
except Exception:
    EOD_AVAILABLE = False

CACHE_PATH = "data/cache_etf_universe.json"
CACHE_TTL_HOURS = 24

# Minimal universe fallback (puedes ampliar este JSON en data/etf_universe.json)
DEFAULT_UNIVERSE = {
    "metals": [
        {"ticker": "GLD", "name": "SPDR Gold Trust", "desc": "Oro físico"},
        {"ticker": "SLV", "name": "iShares Silver Trust", "desc": "Plata física"},
        {"ticker": "IAU", "name": "iShares Gold Trust", "desc": "Oro físico"}
    ],
    "tech": [
        {"ticker": "XLK", "name": "Technology Select Sector SPDR Fund", "desc": "Teconología US"},
        {"ticker": "QQQ", "name": "Invesco QQQ Trust", "desc": "Nasdaq 100"}
    ],
    "bonds": [
        {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "desc": "Bonos largos US"},
        {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "desc": "Bonos diversificados"}
    ],
    "commodity": [
        {"ticker": "DBC", "name": "Invesco DB Commodity Index Tracking Fund", "desc": "Commodities varios"}
    ],
    "energy": [
        {"ticker": "XLE", "name": "Energy Select Sector SPDR Fund", "desc": "Energía US"}
    ],
    "financials": [
        {"ticker": "XLF", "name": "Financial Select Sector SPDR Fund", "desc": "Sector financiero US"}
    ]
}

def load_cached_universe():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # TTL check
        ts = datetime.fromisoformat(data.get("_ts"))
        if datetime.now() - ts > timedelta(hours=CACHE_TTL_HOURS):
            return {}
        return data.get("universe", {})
    except Exception:
        return {}

def save_cached_universe(universe):
    data = {"_ts": datetime.now().isoformat(), "universe": universe}
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_universe():
    # 1) Try cache
    cached = load_cached_universe()
    if cached:
        return cached

    # 2) Try to fetch/enrich from EODHD if available (best-effort)
    universe = DEFAULT_UNIVERSE.copy()
    if EOD_AVAILABLE:
        try:
            # Example: try to get list of ETFs per sector (endpoint names vary)
            # This is best-effort: if eod_request not fitting, it will fail safely
            # Replace with suitable endpoints for your plan if desired
            for theme in list(universe.keys()):
                res = eod_request(f"screening?keywords={theme}&type=etf&limit=10")
                if res and isinstance(res, dict) and res.get("data"):
                    universe[theme] = []
                    for item in res["data"]:
                        universe[theme].append({
                            "ticker": item.get("code") or item.get("ticker"),
                            "name": item.get("name") or item.get("longName"),
                            "desc": item.get("description") or ""
                        })
        except Exception:
            pass

    # Save cache and return
    save_cached_universe(universe)
    return universe

def suggest_etfs_by_keyword(keyword, max_results=8):
    kw = (keyword or "").lower()
    universe = get_universe()
    suggestions = []

    # match theme labels
    for theme, etfs in universe.items():
        if kw in theme or theme in kw:
            suggestions.extend([dict(e, theme=theme) for e in etfs])

    # keyword match within ETF name/desc
    if not suggestions:
        for theme, etfs in universe.items():
            for e in etfs:
                if kw in (e.get("name","").lower()) or kw in (e.get("desc","").lower()):
                    suggestions.append(dict(e, theme=theme))

    # limit
    return suggestions[:max_results]

# Optional: lookup single ETF metadata (best-effort)
def get_etf_metadata(ticker):
    # Try EODHD if available, else return minimal
    if EOD_AVAILABLE:
        try:
            res = eod_request(f"fundamentals/{ticker}")
            return res
        except Exception:
            pass
    # fallback minimal
    return {"ticker": ticker}
