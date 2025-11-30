import streamlit as st
from utils.api import api_get

def get_fundamentals(ticker):
    data = api_get(f"fundamentals/{ticker}")

    if not data or "error" in data:
        return None

    return {
        "general": data.get("General", {}),
        "highlights": data.get("Highlights", {}),
        "valuation": data.get("Valuation", {}),
        "technicals": data.get("Technicals", {}),
    }


def render_fundamentals(ticker):
    fundamentals = get_fundamentals(ticker)

    if not fundamentals:
        st.warning("No hay fundamentales disponibles.")
        return

    highlights = fundamentals["highlights"]
    valuation = fundamentals["valuation"]

    st.subheader("📊 Fundamentales Clave")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Precio / Ganancias (P/E):**", highlights.get("PERatio", "N/A"))
        st.write("**Precio / Ventas (P/S):**", valuation.get("PriceSalesTTM", "N/A"))
        st.write("**ROE:**", highlights.get("ReturnOnEquityTTM", "N/A"))

    with col2:
        st.write("**EPS:**", highlights.get("EarningsShare", "N/A"))
        st.write("**Dividend Yield:**", highlights.get("DividendYield", "N/A"))
        st.write("**Beta:**", highlights.get("Beta", "N/A"))
