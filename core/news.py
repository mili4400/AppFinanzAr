# core/news.py

import streamlit as st
from core.eodhd_api import api_get
from googletrans import Translator

translator = Translator()

def fetch_news(ticker, limit=20):
    """
    Obtiene noticias desde EODHD para un ticker dado.
    Usa el API existente en core/eodhd_api.py
    """
    endpoint = f"news"
    params = {
        "s": ticker,
        "limit": limit
    }

    data = api_get(endpoint, params)

    if not data or isinstance(data, dict) and "error" in data:
        return []

    return data


def is_relevant(article, ticker):
    """
    Filtro de relevancia:
    - si menciona el ticker exacto
    - o nombre de empresa en el título
    - o palabras clave relacionadas
    """

    title = (article.get("title") or "").lower()
    content = (article.get("content") or "").lower()
    ticker_l = ticker.lower()

    if ticker_l in title:
        return True
    if ticker_l in content:
        return True

    keywords = ["earnings", "forecast", "upgrade", "downgrade", "market"]

    if any(k in title for k in keywords):
        return True

    return False


def translate_text_if_needed(text, lang):
    """
    Traduce automáticamente si el usuario selecciona español.
    """
    if lang == "EN":
        return text

    try:
        translated = translator.translate(text, dest="es").text
        return translated
    except:
        return text


def process_news(ticker, lang="EN"):
    """
    - Obtiene noticias
    - Filtra por relevancia
    - Traduce si se pide
    """

    raw_news = fetch_news(ticker)

    relevant = [a for a in raw_news if is_relevant(a, ticker)]

    processed = []
    for article in relevant:
        processed.append({
            "title": translate_text_if_needed(article.get("title", ""), lang),
            "content": translate_text_if_needed(article.get("content", ""), lang),
            "date": article.get("date"),
            "url": article.get("url")
        })

    return processed
