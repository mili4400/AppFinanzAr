import json
import os
from typing import List, Union

FAV_PATH = os.path.join("data", "favorites.json")
MAX_DEFAULT_PER_USER = 50  # you can adjust; dashboard enforces free limit separately

def _ensure_file():
    os.makedirs(os.path.dirname(FAV_PATH), exist_ok=True)
    if not os.path.exists(FAV_PATH):
        # structure: { "<username>": { "all": [ "TICKER", ... ], "categories": { "tech": [...], ... } } }
        with open(FAV_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def _load_all():
    _ensure_file()
    try:
        with open(FAV_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}

def _save_all(data):
    os.makedirs(os.path.dirname(FAV_PATH), exist_ok=True)
    with open(FAV_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_favorites(username: str):
    """
    Retorna estructura consistente para un usuario:
    { "all": [ "AAPL", "MSFT" ], "categories": { "tech": ["AAPL"] } }
    Si username no existe, crea estructura vacía en memoria (pero no persiste).
    """
    if not username:
        username = "demo"
    data = _load_all()
    user = data.get(username)
    if not user:
        # return standardized empty structure
        return {"all": [], "categories": {}}
    # ensure keys
    user.setdefault("all", [])
    user.setdefault("categories", {})
    return user

def save_favorites(username: str, fav_list: Union[List, dict]):
    """
    Guarda fav_list para username.
    fav_list puede ser:
      - lista simple de tickers -> será guardada en "all"
      - dict con keys "all" y/o "categories"
    """
    if not username:
        username = "demo"
    data = _load_all()
    if isinstance(fav_list, dict):
        to_save = fav_list
        to_save.setdefault("all", [])
        to_save.setdefault("categories", {})
    else:
        # list -> wrap
        to_save = {"all": fav_list, "categories": {}}
    data[username] = to_save
    _save_all(data)
    return to_save

def add_favorite(username: str, item: Union[str, dict], category: str = None):
    """
    Agrega favorito:
      - item puede ser string ticker (ej: "AAPL") o dict {"ticker": "...", "type": "..."}
      - category opcional (ej "tech")
    Evita duplicados (por ticker string).
    Devuelve la lista actualizada.
    """
    if not username:
        username = "demo"
    user = load_favorites(username)
    # normalize item -> ticker string
    ticker = None
    if isinstance(item, str):
        ticker = item.upper()
    elif isinstance(item, dict):
        # try common keys
        ticker = (item.get("ticker") or item.get("code") or item.get("symbol") or "").upper()
    if not ticker:
        return user  # nothing to add

    # ensure unique in 'all'
    if ticker not in user["all"]:
        user["all"].append(ticker)

    # add to category if provided
    if category:
        user["categories"].setdefault(category, [])
        if ticker not in user["categories"][category]:
            user["categories"][category].append(ticker)

    # persist
    save_favorites(username, user)
    return user

def remove_favorite(username: str, item: Union[str, dict], category: str = None):
    """
    Elimina favorito. Si category provisto, lo quita de esa categoría; si no, lo quita de 'all' y todas las categorías.
    """
    if not username:
        username = "demo"
    user = load_favorites(username)
    ticker = None
    if isinstance(item, str):
        ticker = item.upper()
    elif isinstance(item, dict):
        ticker = (item.get("ticker") or item.get("code") or item.get("symbol") or "").upper()
    if not ticker:
        return user

    if category:
        if category in user["categories"]:
            user["categories"][category] = [t for t in user["categories"][category] if t != ticker]
    else:
        user["all"] = [t for t in user["all"] if t != ticker]
        # also remove from all categories
        for cat in list(user["categories"].keys()):
            user["categories"][cat] = [t for t in user["categories"][cat] if t != ticker]

    save_favorites(username, user)
    return user

def clear_user_favorites(username: str):
    if not username:
        username = "demo"
    data = _load_all()
    data[username] = {"all": [], "categories": {}}
    _save_all(data)
    return data[username]
