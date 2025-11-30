import json
import os

FAV_PATH = "data/favorites.json"


def _ensure_file():
    """
    Crea el archivo favorites.json si no existe.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(FAV_PATH):
        with open(FAV_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_favorites(username):
    """
    Devuelve la lista de favoritos del usuario.
    """
    _ensure_file()
    try:
        with open(FAV_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(username, [])
    except Exception:
        return []


def save_favorites(username, fav_list):
    """
    Guarda la lista completa de favoritos del usuario.
    """
    _ensure_file()
    try:
        with open(FAV_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    data[username] = fav_list

    with open(FAV_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_favorite(username, item):
    """
    Agrega un favorito si no está repetido.
    item es típicamente: {"ticker": "AAPL", "type": "stock"}
    """
    favs = load_favorites(username)

    # Evita duplicados usando ticker + type
    if item not in favs:
        favs.append(item)

    save_favorites(username, favs)
    return favs


def remove_favorite(username, item):
    """
    Elimina un favorito.
    """
    favs = load_favorites(username)
    favs = [f for f in favs if f != item]
    save_favorites(username, favs)
    return favs
