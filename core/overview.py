import streamlit as st
from utils.api import api_get

def get_overview(ticker):
    """Devuelve summary básico del ticker."""
    data = api_get(f"fundamentals/{ticker}")

    if not data or "error" in data:
        return None

    general = data.get("General", {})
    highlights = data.get("Highlights", {})

    return {
        "name": general.get("Name", ""),
        "exchange": general.get("Exchange", ""),
        "country": general.get("Country", ""),
        "sector": general.get("Sector", ""),
        "industry": general.get("Industry", ""),
        "description": general.get("Description", ""),
        "market_cap": highlights.get("MarketCapitalization", ""),
        "employees": general.get("FullTimeEmployees", ""),
    }


def render_overview(ticker):
    summary = get_overview(ticker)

    if not summary:
        st.warning("No hay información general disponible para este activo.")
        return

    st.subheader("📌 Executive Summary")

    st.markdown(f"""
    **Empresa:** {summary['name']}  
    **Exchange:** {summary['exchange']}  
    **País:** {summary['country']}  
    **Sector:** {summary['sector']}  
    **Industria:** {summary['industry']}  

    **Market Cap:** {summary['market_cap']}  
    **Empleados:** {summary['employees']}  
    """)

    if summary["description"]:
        st.write("### 📝 Descripción")
        st.write(summary["description"])
