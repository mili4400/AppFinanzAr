# core/utils.py
import json
import pandas as pd

# -----------------------------
# Funciones de manejo de JSON
# -----------------------------
def load_json(path, default=None):
    try:
        with open(path,"r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, obj):
    with open(path,"w", encoding="utf-8") as f:
        json.dump(obj,f,indent=2)

# -----------------------------
# Funciones técnicas (para dashboard)
# -----------------------------
def sma(series: pd.Series, window: int):
    """Simple Moving Average"""
    return series.rolling(window=window).mean()

def ema(series: pd.Series, span: int):
    """Exponential Moving Average"""
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14):
    """Relative Strength Index"""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / (avg_loss.replace(0, pd.NA))
    rsi = 100 - (100 / (1 + rs))
    return rsi
