import json
import os

def cache_load(path, default=None):
    """
    Carga un archivo JSON. Si no existe o está corrupto, devuelve default.
    """
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def cache_save(path, data):
    """
    Guarda un archivo JSON sin romper si falla.
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass
# Placeholder: future caching
