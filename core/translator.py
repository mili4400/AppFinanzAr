# core/translator.py

from deep_translator import GoogleTranslator
import langdetect

def translate_to_english(text: str) -> str:
    try:
        lang = langdetect.detect(text)
    except:
        lang = "en"

    # Si ya está en inglés → devolver tal cual
    if lang == "en":
        return text

    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text
