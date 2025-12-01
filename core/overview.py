import numpy as np
from datetime import datetime, timedelta
from core.fundamentals import fetch_fundamentals
from core.data_fetch import fetch_ohlc, fetch_news
from core.sentiment import sentiment_score

def summarize_text_local(paragraph, max_sentences=3, lang="es"):
    """Mini resumen local sin modelos externos, con idioma."""
    import re
    sentences = re.split(r'(?<=[.!?]) +', paragraph)
    if len(sentences) <= max_sentences:
        return paragraph
    
    # Rank sentences by keyword frequency
    words = paragraph.lower().split()
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    
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
    change_pct = (last - first) / first * 100
    return round(change_pct, 2)

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

    avg = np.mean(scores)
    if avg > 0.15:
        label = "positivo"
    elif avg < -0.15:
        label = "negativo"
    else:
        label = "neutral"

    return {
        "avg_score": round(float(avg),3),
        "label": label
    }

def competitors_stats(competitors):
    """Calcula comentarios básicos de valoración sectorial."""
    import numpy as np
    metrics = []

    for comp in competitors[:8]:
        f, _ = fetch_fundamentals(comp)
        if f and f.get("PERatio"):
            metrics.append(f["PERatio"])

    if len(metrics) < 3:
        return None  # Not enough for benchmark analysis

    return {
        "avg_pe": round(float(np.mean(metrics)),2),
        "min_pe": round(float(np.min(metrics)),2),
        "max_pe": round(float(np.max(metrics)),2)
    }

def create_overview(ticker, lang="es"):
    # --- Fundamentals ---
    fundamentals, competitors = fetch_fundamentals(ticker)

    # --- Price trend ---
    df = fetch_ohlc(ticker, 
                    from_date=(datetime.today() - timedelta(days=30)).date(),
                    to_date=datetime.today().date())
    price_trend = compute_price_trend(df)

    # --- Sentiment ---
    sentiment = compute_sentiment_overview(ticker)

    # --- Benchmark ---
    comp_stats = competitors_stats(competitors)

    # --- Executive Summary (structured) ---
    summary = {}
    
    # Company basic info
    summary["name"] = fundamentals.get("Name", "N/A")
    summary["sector"] = fundamentals.get("Sector", "N/A")
    summary["industry"] = fundamentals.get("Industry", "N/A")
    summary["country"] = fundamentals.get("Country", "N/A")

    # Financial snapshot
    summary["valuation"] = {
        "pe_ratio": fundamentals.get("PERatio") or "N/A",
        "market_cap": fundamentals.get("MarketCapitalization") or "N/A",
        "eps": fundamentals.get("EPS") or "N/A",
    }
    summary["profitability"] = {
        "profit_margin": fundamentals.get("ProfitMargin") or "N/A",
        "ebitda": fundamentals.get("EBITDA") or "N/A",
    }
    summary["financial_strength"] = {
        "assets": fundamentals.get("TotalAssets") or "N/A",
        "liabilities": fundamentals.get("TotalLiabilities") or "N/A",
        "book_value": fundamentals.get("BookValue") or "N/A",
    }

    # Trend & sentiment
    summary["price_trend_30d"] = price_trend
    summary["sentiment"] = sentiment

    # Benchmark
    summary["competitor_benchmark"] = comp_stats
    summary["competitors_list"] = competitors[:5]  # mostrar max 5

    # NLP-style narrative summary
    narrative = []

    # Mensajes por idioma
    price_up = "El precio subió" if lang=="es" else "Price increased"
    price_down = "El precio cayó" if lang=="es" else "Price decreased"
    sentiment_msg = "El sentimiento del mercado es" if lang=="es" else "Market sentiment is"
    pe_above = "está por encima del promedio sectorial" if lang=="es" else "is above industry average"
    pe_below = "está por debajo del promedio sectorial" if lang=="es" else "is below industry average"

    # Core description
    if fundamentals.get("Description"):
        narrative.append(summarize_text_local(fundamentals["Description"], max_sentences=2, lang=lang))

    # Price trend
    if price_trend is not None:
        if price_trend > 0:
            narrative.append(f"{price_up} {price_trend}% en los últimos 30 días.")
        else:
            narrative.append(f"{price_down} {abs(price_trend)}% en los últimos 30 días.")

    # Sentiment
    if sentiment:
        narrative.append(f"{sentiment_msg} **{sentiment['label']}** (promedio {sentiment['avg_score']}).")

    # Competitor benchmark
    if comp_stats:
        pe = fundamentals.get("PERatio")
        avg_pe = comp_stats["avg_pe"]

        if pe and avg_pe:
            if pe > avg_pe:
                narrative.append(f"El PER actual ({pe}) {pe_above} ({avg_pe}).")
            elif pe < avg_pe:
                narrative.append(f"El PER actual ({pe}) {pe_below} ({avg_pe}).")

    summary["narrative"] = " ".join(narrative)

    return summary

def build_overview(ticker: str, lang="es"):
    """
    Wrapper usado por dashboard_ui.
    Combina:
    - fundamentals
    - competitors
    - price data
    - news
    - sentiment
    - executive summary avanzado
    """

    # Executive summary avanzado basado en tu lógica
    summary = create_overview(ticker, lang=lang)

    # Datos adicionales del dashboard
    fundamentals, competitors = fetch_fundamentals(ticker)
    price_data = fetch_ohlc(ticker)
    news = fetch_news(ticker)

    # Etiqueta simple de sentimiento
    sentiment_info = summary.get("sentiment", None)
    if sentiment_info:
        sentiment_label = {
            "positivo": "📈 Positivo",
            "negativo": "📉 Negativo",
            "neutral": "🔍 Neutral"
        }.get(sentiment_info["label"], "🔍 Neutral")
    else:
        sentiment_label = "Sin datos"

    return {
        "fundamentals": fundamentals,
        "competitors": competitors[:5],  # mostrar máximo 5
        "price": price_data,
        "news": news,
        "sentiment_value": sentiment_info["avg_score"] if sentiment_info else 0,
        "sentiment_label": sentiment_label,
        "fundamentals_summary": summary["narrative"],   # resumen avanzado
        "executive_summary": summary                     # TODO: usar en UI futura
    }
