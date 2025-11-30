import os
import requests

EOD_API_KEY = os.getenv("EODHD_API_KEY", "")

BASE_URL = "https://eodhd.com/api"


def eod_request(endpoint: str, params: dict = None):
    """
    Wrapper seguro para realizar solicitudes a EODHD.
    Si no hay API KEY o la API falla, devuelve None sin romper la app.
    """
    if params is None:
        params = {}

    params["api_token"] = EOD_API_KEY
    params["fmt"] = "json"

    url = f"{BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def fetch_eodhd(symbol: str, interval: str = "1d", limit: int = 100):
    """
    Función estandarizada que la app espera.
    Devuelve datos históricos del ticker usando el wrapper eod_request.
    """
    endpoint = f"eod/{symbol}.US"

    params = {
        "period": interval,  # "1d", "1w", etc.
        "limit": limit
    }

    data = eod_request(endpoint, params)

    # Asegura que la app no explote si la API falla
    if not data or not isinstance(data, list):
        return []

    return data
