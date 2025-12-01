import json
import os

FAVORITES_FILE = "data/favorites.json"

def load_favorites(username="demo"):
    if not os.path.exists(FAVORITES_FILE):
        return {"all": [], "categories": {}}
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(username, {"all": [], "categories": {}})
    except:
        return {"all": [], "categories": {}}

def save_favorites(username, favorites):
    data = {}
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    data[username] = favorites
    os.makedirs(os.path.dirname(FAVORITES_FILE), exist_ok=True)
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_favorite(username, ticker, category=None):
    favs = load_favorites(username)
    if ticker not in favs["all"]:
        favs["all"].append(ticker)
    if category:
        if category not in favs["categories"]:
            favs["categories"][category] = []
        if ticker not in favs["categories"][category]:
            favs["categories"][category].append(ticker)
    save_favorites(username, favs)

def remove_favorite(username, ticker, category=None):
    favs = load_favorites(username)
    if ticker in favs["all"]:
        favs["all"].remove(ticker)
    if category and category in favs["categories"]:
        if ticker in favs["categories"][category]:
            favs["categories"][category].remove(ticker)
    save_favorites(username, favs)
