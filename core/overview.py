import numpy as np
from datetime import datetime, timedelta
from core.fundamentals import fetch_fundamentals
from core.data_fetch import fetch_ohlc, fetch_news
from core.sentiment import sentiment_score

# ===========================================================
# === MÓDULOS INTERNOS AVANZADOS (NO SE ELIMINA NADA) =======
# ===========================================================

def summarize_text_local(paragraph, max_sentences=3):
    import re
    sentences = re.split(r'(?<=[.!?]) +', paragraph)
    if len(sentences) <= max_sentences:
        return paragraph
    
    words = paragraph.lower().split()
    freq = {w: words.count(w) for w in words}

    scoring = []
    for s in sentences:
        score = sum(freq.get(w.lower(), 0) for w in s.split())
        scoring.append((score, s))

    scoring.sort(reverse=True, key=lambda x: x[0])
    top_sentences = [s for _, s in scoring[:max_sentences]]
    return " ".join(top_sentences)


def compute_price_trend(df):
    if df.empty:
        return None
    first = df["close"].iloc[0]
    last = df["close"].iloc[-1]
    return round((last - first) / first * 100, 2)


def compute_sentiment_overview(ticker):
    news = fetch_news(ticker)
    if not news:
        return None

    scores = []
    for item in news[:15]:
        text = f"{item.get('title','')} {item.get('content','')}"
        scores.append(sentiment_score(text))

    if not scores:
        return None

    avg = float(np.mean(scores))

    if avg > 0.15:
        label = "positivo"
    elif avg < -0.15:
        label = "negativo"
    else:
        label = "neutral"

    return {"avg_score": round(avg,3), "label": label}


def competitors_stats(competitors):
    metrics = []
    for comp in competitors[:8]:
        f, _ = fetch_fundamentals(comp)
        if f and f.get("PERatio"):
            metrics.append(f["PERatio"])
    if len(metrics) < 3:
        return None
    return {
        "avg_pe": round(float(np.mean(metrics)),2),
        "min_pe": round(float(np.min(metrics)),2),
        "max_pe": round(float(np.max(metrics)),2)
    }


def create_overview(ticker):
    fundamentals, competitors = fetch_fundamentals(ticker)

    df = fetch_ohlc(
        ticker,
        from_date=(datetime.today() - timedelta(days=30)).date(),
        to_date=datetime.today().date()
    )
    price_trend = compute_price_trend(df)
    sentiment = compute_sentiment_overview(ticker)
    comp_stats = competitors_stats(competitors)

    summary = {
        "name": fundamentals.get("Name"),
        "sector": fundamentals.get("Sector"),
        "industry": fundamentals.get("Industry"),
        "country": fundamentals.get("Country"),
        "valuation": {
            "pe_ratio": fundamentals.get("PERatio"),
            "market_cap": fundamentals.get("MarketCapitalization"),
            "eps": fundamentals.get("EPS"),
        },
        "profitability": {
            "profit_margin": fundamentals.get("ProfitMargin"),
            "ebitda": fundamentals.get("EBITDA"),
        },
        "financial_strength": {
            "assets": fundamentals.get("TotalAssets"),
            "liabilities": fundamentals.get("TotalLiabilities"),
            "book_value": fundamentals.get("BookValue"),
        },
        "price_trend_30d": price_trend,
        "sentiment": sentiment,
        "competitor_benchmark": comp_stats,
        "competitors_list": competitors
    }

    narrative = []

    if fundamentals.get("Description"):
        narrative.append(summarize_text_local(fundamentals["Description"],2))

    if price_trend is not None:
        narrative.append(
            f"El precio {'subió' if price_trend>0 else 'cayó'} {abs(price_trend)}% en 30 días."
        )

    if sentiment:
        narrative.append(
            f"El sentimiento es **{sentiment['label']}** (score {sentiment['avg_score']})."
        )

    if comp_stats:
        pe = fundamentals.get("PERatio")
        avg_pe = comp_stats["avg_pe"]
        if pe and avg_pe:
            if pe > avg_pe:
                narrative.append(f"El PER actual ({pe}) está por encima del sector ({avg_pe}).")
            elif pe < avg_pe:
                narrative.append(f"El PER actual ({pe}) está por debajo del sector ({avg_pe}).")

    summary["narrative"] = " ".join(narrative)
    return summary


# ===========================================================
# ===   MODO SIMPLE (COMPATIBLE CON DASHBOARD UI)         ===
# ===========================================================

def build_overview(ticker, fundamentals=None):
    """
    Modo SIMPLE para dashboard (no crashea).
    Reutiliza datos del overview avanzado.
    """
    full = create_overview(ticker)
    fund = full["valuation"]
    sent = full["sentiment"]

    return {
        "Ticker": ticker,
        "Sector": full["sector"],
        "Industria": full["industry"],
        "País": full["country"],
        "Market Cap": fund.get("market_cap"),
        "P/E Ratio": fund.get("pe_ratio"),
        "EPS": fund.get("eps"),
        "Tendencia 30d (%)": full.get("price_trend_30d"),
        "Sentimiento": sent["label"] if sent else "sin datos",
        "Sentiment Score": sent["avg_score"] if sent else None,
        "Resumen Ejecutivo": full["narrative"]
    }
