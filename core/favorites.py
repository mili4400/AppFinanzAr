import json
import os

FAV_PATH = "data/favorites.json"


def _ensure_file():
    """
    Garantiza que favorites.json existe y tiene estructura mínima.
    """
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(FAV_PATH):
        with open(FAV_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def _ensure_user_structure(data, username):
    """
    Garantiza que el usuario tenga la estructura correcta:
    {
        "all": [],
        "categories": {}
    }
    """
    if username not in data:
        data[username] = {"all": [], "categories": {}}

    # Seguridad extra si el archivo estaba corrompido
    if "all" not in data[username]:
        data[username]["all"] = []

    if "categories" not in data[username]:
        data[username]["categories"] = {}

    return data


def load_favorites(username):
    """
    Devuelve favoritos con estructura:
    {
        "all": [tickers],
        "categories": { "tech": ["AAPL"], ... }
    }
    """
    _ensure_file()

    try:
        with open(FAV_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    data = _ensure_user_structure(data, username)
    return data[username]


def save_favorites(username, favs):
    """
    Guarda estructura completa de favoritos del usuario.
    """
    _ensure_file()

    try:
        with open(FAV_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    data = _ensure_user_structure(data, username)
    data[username] = favs

    with open(FAV_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_favorite(username, ticker):
    """
    Agrega un ticker simple (ej. 'AAPL.US') a la lista 'all'.
    NO usa objetos complejos para evitar errores.
    """
    favs = load_favorites(username)

    ticker = ticker.upper()
    if ticker not in favs["all"]:
        favs["all"].append(ticker)

    save_favorites(username, favs)
    return favs


def remove_favorite(username, ticker):
    """
    Elimina un ticker.
    """
    favs = load_favorites(username)

    ticker = ticker.upper()
    favs["all"] = [t for t in favs["all"] if t != ticker]

    save_favorites(username, favs)
    return favs
