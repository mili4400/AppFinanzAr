import os
import requests

EOD_API_KEY = os.getenv("EODHD_API_KEY", "")

BASE_URL = "https://eodhd.com/api"

def eod_request(endpoint: str, params: dict = None):
    """
    Pequeño wrapper seguro para API EODHD.
    Streamlit Cloud no falla aunque no haya API KEY.
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
        # Para que la app nunca explote si EOD no responde
        return None
