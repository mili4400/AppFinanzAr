# core/utils.py
import json
import pandas as pd

# JSON helpers
def load_json(path, default=None):
    try:
        with open(path,"r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, obj):
    with open(path,"w", encoding="utf-8") as f:
        json.dump(obj,f,indent=2)

# Technical indicators
def sma(series: pd.Series, window: int):
    return series.rolling(window=window).mean()

def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / (avg_loss.replace(0, pd.NA))
    rsi = 100 - (100 / (1 + rs))
    return rsi

