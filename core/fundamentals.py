import json
import os
from datetime import datetime, timedelta
from core.eodhd_api import eod_request
from core.cache_manager import cache_load, cache_save

CACHE_PATH = "data/cache_fundamentals.json"
CACHE_TTL_HOURS = 24


def get_cached_fundamentals(ticker):
    cache = cache_load(CACHE_PATH, {})
    if ticker in cache:
        last_update = datetime.fromisoformat(cache[ticker]["timestamp"])
        if datetime.now() - last_update < timedelta(hours=CACHE_TTL_HOURS):
            return cache[ticker]["fundamentals"], cache[ticker]["competitors"]
    return None, None


def save_cached_fundamentals(ticker, fundamentals, competitors):
    cache = cache_load(CACHE_PATH, {})
    cache[ticker] = {
        "timestamp": datetime.now().isoformat(),
        "fundamentals": fundamentals,
        "competitors": competitors,
    }
    cache_save(CACHE_PATH, cache)


def fetch_general_fundamentals(ticker):
    return eod_request(f"fundamentals/{ticker}")


def fetch_income_statement(ticker):
    return eod_request(f"financials/income-statement/{ticker}?period=yearly")


def fetch_balance_sheet(ticker):
    return eod_request(f"financials/balance-sheet/{ticker}?period=yearly")


def fetch_cash_flow(ticker):
    return eod_request(f"financials/cash-flow/{ticker}?period=yearly")


def extract_main_metrics(general, income, balance, cash):
    data = {}

    # --- General fundamentals ---
    if general:
        if "General" in general:
            g = general["General"]
            fields = [
                "Code", "Name", "Exchange", "CurrencyISO", "Sector",
                "Industry", "Country", "MarketCapitalization",
                "SharesOutstanding", "Description"
            ]
            for f in fields:
                data[f] = g.get(f)

        if "Highlights" in general:
            h = general["Highlights"]
            fields = ["PERatio", "EPS", "ProfitMargin", "EBITDA", "DividendYield"]
            for f in fields:
                data[f] = h.get(f)

    # --- Try to improve fundamental values using other endpoints ---
    if income and "financials" in income:
        last = income["financials"][0]
        data.setdefault("Revenue", last.get("totalRevenue"))
        data.setdefault("NetIncome", last.get("netIncome"))

    if balance and "financials" in balance:
        last = balance["financials"][0]
        data.setdefault("TotalAssets", last.get("totalAssets"))
        data.setdefault("TotalLiabilities", last.get("totalLiab"))
        data.setdefault("BookValue", last.get("totalStockholderEquity"))

    if cash and "financials" in cash:
        last = cash["financials"][0]
        data.setdefault("OperatingCashFlow", last.get("totalCashFromOperatingActivities"))
        data.setdefault("FreeCashFlow", last.get("changeInCash"))

    # --- Derived fallback metrics ---
    if data.get("MarketCapitalization") is None and data.get("SharesOutstanding") and general:
        try:
            price = general["SharesStats"]["52WeekHigh"]  # fallback
            data["MarketCapitalization"] = price * data.get("SharesOutstanding")
        except:
            pass

    return data


def fetch_competitors(general):
    """Build competitor list by Industry, Sector, Country."""
    if not general or "General" not in general:
        return []

    industry = general["General"].get("Industry")
    sector = general["General"].get("Sector")
    country = general["General"].get("Country")

    # EODHD: screener endpoint
    query = f"screener?industry={industry}&sector={sector}&country={country}"
    data = eod_request(query)

    competitors = []
    if data and "data" in data:
        for item in data["data"][:10]:
            competitors.append(item.get("code"))

    return competitors


def fetch_fundamentals(ticker):
    # --- Cache check ---
    cached_f, cached_c = get_cached_fundamentals(ticker)
    if cached_f:
        return cached_f, cached_c

    # --- Queries ---
    general = fetch_general_fundamentals(ticker)
    income = fetch_income_statement(ticker)
    balance = fetch_balance_sheet(ticker)
    cash = fetch_cash_flow(ticker)

    # --- Extract main metrics ---
    fundamentals = extract_main_metrics(general, income, balance, cash)

    # --- Competitors ---
    competitors = fetch_competitors(general)

    # --- Save cache ---
    save_cached_fundamentals(ticker, fundamentals, competitors)

    return fundamentals, competitors
