from textblob import TextBlob

def analyze_sentiment_textblob(text: str):
    """
    Analiza sentimiento usando TextBlob.
    Devuelve:
        polarity (-1 a 1)
        subjectivity (0 a 1)
    """
    if not text or not isinstance(text, str):
        return 0, 0

    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        return polarity, subjectivity
    except:
        return 0, 0
