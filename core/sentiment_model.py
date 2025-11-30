# core/sentiment_model.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import functools

@functools.lru_cache(maxsize=1)
def load_sentiment_model():
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    return tokenizer, model


def sentiment_score(text):
    tokenizer, model = load_sentiment_model()

    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)

    scores = torch.softmax(outputs.logits, dim=1).tolist()[0]
    negative, positive = scores

    # Escala normalizada: -1 (negativo) a +1 (positivo)
    score = positive - negative

    return float(score)
