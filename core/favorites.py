import json
import os

FAV_PATH = os.path.join("data", "favorites.json")
DEFAULT_STRUCTURE = {"all": [], "categories": {}}

def _ensure_file():
    os.makedirs(os.path.dirname(FAV_PATH), exist_ok=True)
    if not os.path.exists(FAV_PATH):
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
    Retorna dict: {"all": [...], "categories": {...}}
    Si no existe usuario, devuelve estructura vacía por compatibilidad.
    """
    if not username:
        username = "demo"
    all_data = _load_all()
    user_data = all_data.get(username)
    if not user_data:
        # soporta versiones antiguas donde se guardaba lista simple
        # si all_data tiene keys que parecen tickers, mantener compat.
        return {"all": [], "categories": {}}
    # Si guardaste solo una lista (versiones previas), convertir
    if isinstance(user_data, list):
        return {"all": user_data, "categories": {}}
    # Si es dict, asegurarse de las claves
    if isinstance(user_data, dict):
        user_data.setdefault("all", [])
        user_data.setdefault("categories", {})
        return user_data
    # fallback
    return {"all": [], "categories": {}}

def save_favorites(username: str, fav_struct):
    """
    Guarda la estructura completa para el usuario.
    fav_struct debe ser dict {"all": [...], "categories": {...}}
    """
    if not username:
        username = "demo"
    all_data = _load_all()
    all_data[username] = fav_struct
    _save_all(all_data)
    return fav_struct

def add_favorite(username: str, item):
    """
    Agrega item a la lista 'all'. Aquí item puede ser:
    - string ticker como "AAPL.US"
    - o dict {"ticker": "...", "type": "..."}
    Mantenemos retro-compatibilidad: si es string, lo guardamos como string.
    """
    if not username:
        username = "demo"
    data = _load_all()
    user = data.get(username)
    if not user:
        user = {"all": [], "categories": {}}
    # normalize
    if isinstance(user, list):
        user = {"all": user, "categories": {}}
    user.setdefault("all", [])
    user.setdefault("categories", {})

    # evitar duplicados (comparar por ticker si dict)
    exists = False
    if isinstance(item, dict):
        t = item.get("ticker") or item.get("symbol")
        for e in user["all"]:
            if isinstance(e, dict) and (e.get("ticker") == t):
                exists = True
            if isinstance(e, str) and e == t:
                exists = True
    else:
        t = str(item)
        for e in user["all"]:
            if isinstance(e, str) and e == t:
                exists = True
            if isinstance(e, dict) and e.get("ticker") == t:
                exists = True

    if not exists:
        user["all"].append(item)

    data[username] = user
    _save_all(data)
    return user

def remove_favorite(username: str, item):
    if not username:
        username = "demo"
    data = _load_all()
    user = data.get(username, {"all": [], "categories": {}})
    if isinstance(user, list):
        user = {"all": user, "categories": {}}
    # remove matching items
    new_all = []
    for e in user.get("all", []):
        if isinstance(item, dict) and isinstance(e, dict):
            if e.get("ticker") == item.get("ticker"):
                continue
        elif isinstance(item, dict) and isinstance(e, str):
            if e == item.get("ticker"):
                continue
        elif isinstance(item, str) and isinstance(e, str):
            if e == item:
                continue
        elif isinstance(item, str) and isinstance(e, dict):
            if e.get("ticker") == item:
                continue
        new_all.append(e)
    user["all"] = new_all
    data[username] = user
    _save_all(data)
    return user

def clear_favorites(username: str):
    if not username:
        username = "demo"
    data = _load_all()
    data[username] = {"all": [], "categories": {}}
    _save_all(data)
    return data[username]

