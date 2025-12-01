# core/sentiment.py

from core.sentiment_model import sentiment_score

def analyze_sentiment_textblob(text: str):
    """
    Compatibilidad para dashboard_ui.
    Usa el modelo transformer real.
    """

    score = sentiment_score(text)

    if score > 0.1:
        sentiment = "positive"
    elif score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "polarity": score,
        "sentiment": sentiment
    }

__all__ = ["analyze_sentiment_textblob", "sentiment_score"]
