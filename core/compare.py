# core/compare.py

import pandas as pd
from core.data_fetch import fetch_historical_data

def compare_tickers(ticker1, ticker2, period="3mo"):
    """
    Compara dos tickers obteniendo precios históricos y variación porcentual.
    Utiliza el data_fetch existente para no duplicar lógica ni gastar requests.
    """

    data1 = fetch_historical_data(ticker1, period)
    data2 = fetch_historical_data(ticker2, period)

    if data1 is None or data2 is None:
        return None

    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)

    # Normalizamos por fecha (inner join)
    merged = pd.merge(df1[['date', 'close']], df2[['date', 'close']],
                      on='date', suffixes=(f"_{ticker1}", f"_{ticker2}"))

    # Variación porcentual desde el inicio
    merged[f"pct_{ticker1}"] = (merged[f"close_{ticker1}"] /
                                merged[f"close_{ticker1}"].iloc[0] - 1) * 100

    merged[f"pct_{ticker2}"] = (merged[f"close_{ticker2}"] /
                                merged[f"close_{ticker2}"].iloc[0] - 1) * 100

    return merged
