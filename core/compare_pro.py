# core/compare_pro.py
import pandas as pd
import numpy as np
from datetime import datetime
from core.data_fetch import fetch_ohlc
from core.fundamentals import fetch_fundamentals
from core.overview import compute_sentiment_overview  # reusa función ya existente
from core.utils import sma, ema, rsi  # si tenés utilidades
try:
    from core.sentiment_model import sentiment_score
    from core.translator import translate_to_english
    SENT_AVAILABLE = True
except Exception:
    SENT_AVAILABLE = False

def compute_volatility(series):
    # daily returns volatility annualized
    returns = series.pct_change().dropna()
    return round(returns.std() * np.sqrt(252), 4)

def compute_sharpe(series, rf=0.0):
    returns = series.pct_change().dropna()
    if returns.empty:
        return None
    excess = returns - rf/252
    return round((excess.mean() / returns.std()) * np.sqrt(252), 4)

def prepare_indicators(df):
    d = df.copy()
    d["SMA20"] = d["close"].rolling(20).mean()
    d["SMA50"] = d["close"].rolling(50).mean()
    d["EMA20"] = d["close"].ewm(span=20).mean()
    d["RSI14"] = rsi(d["close"], 14) if "rsi" in globals() else None
    return d

def compare_pro(ticker_a, ticker_b, from_date, to_date):
    # fetch OHLC
    df_a = fetch_ohlc(ticker_a, from_date=from_date, to_date=to_date)
    df_b = fetch_ohlc(ticker_b, from_date=from_date, to_date=to_date)

    if df_a.empty or df_b.empty:
        return None

    # prepare indicators
    A = prepare_indicators(df_a)
    B = prepare_indicators(df_b)

    # latest metrics
    metrics = {}
    metrics[ticker_a] = {
        "volatility": compute_volatility(A["close"]),
        "sharpe": compute_sharpe(A["close"]),
        "last_close": float(A["close"].iloc[-1])
    }
    metrics[ticker_b] = {
        "volatility": compute_volatility(B["close"]),
        "sharpe": compute_sharpe(B["close"]),
        "last_close": float(B["close"].iloc[-1])
    }

    # fundamentals
    f_a, comp_a = fetch_fundamentals(ticker_a)
    f_b, comp_b = fetch_fundamentals(ticker_b)

    # sentiment (overview average) best-effort
    sent_a = compute_sentiment_overview(ticker_a) if callable(compute_sentiment_overview) else None
    sent_b = compute_sentiment_overview(ticker_b) if callable(compute_sentiment_overview) else None

    # If sentiment_model available, compute direct sentiment on latest headlines
    if SENT_AVAILABLE:
        try:
            # get a few headlines
            from core.data_fetch import fetch_news
            headlines_a = fetch_news(ticker_a)[:10]
            headlines_b = fetch_news(ticker_b)[:10]
            def avg_sent(items):
                s = []
                for it in items:
                    text = (it.get("title","") + " " + it.get("content",""))
                    text_en = translate_to_english(text) if 'translate_to_english' in globals() else text
                    s.append(sentiment_score(text_en))
                return float(np.mean(s)) if s else None
            sent_a = {"avg_score": avg_sent(headlines_a)}
            sent_b = {"avg_score": avg_sent(headlines_b)}
        except Exception:
            pass

    return {
        "df_a": A,
        "df_b": B,
        "metrics": metrics,
        "fundamentals": {ticker_a: f_a, ticker_b: f_b},
        "competitors": {ticker_a: comp_a, ticker_b: comp_b},
        "sentiment": {ticker_a: sent_a, ticker_b: sent_b}
    }

# =======================================================
# RETROCOMPATIBILIDAD PARA EL DASHBOARD
# =======================================================

def compare_indicators(ticker_a, ticker_b, from_date=None, to_date=None):
    """
    Wrapper retrocompatible para el dashboard.
    Antes existía compare_indicators.
    Ahora simplemente usa compare_pro.
    """
    return compare_pro(ticker_a, ticker_b, from_date, to_date)


def compare_sentiment(ticker_a, ticker_b, from_date=None, to_date=None):
    """
    Devuelve solo la parte de sentimiento esperada por el dashboard.
    """
    result = compare_pro(ticker_a, ticker_b, from_date, to_date)

    if not result or "sentiment" not in result:
        return {
            ticker_a: None,
            ticker_b: None
        }

    return result["sentiment"]

