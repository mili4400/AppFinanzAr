# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.data_fetch import fetch_fundamentals, fetch_news
from core.utils import sma, ema, rsi

def show_dashboard():
    st.title("📈 AppFinanzAr — Dashboard")
    ticker = st.text_input("Ingrese ticker (ej: MELI.US)", "MELI.US", key="dashboard_ticker")

    if ticker:
        fundamentals, competitors = fetch_fundamentals(ticker)
        news = fetch_news(ticker, days_back=60)

        # Fundamentales
        st.subheader("Fundamentales clave")
        if fundamentals:
            df_f = pd.DataFrame.from_dict(fundamentals, orient="index", columns=["Valor"])
            st.dataframe(df_f)
        else:
            st.info("No se encontraron datos fundamentales.")

        # Competidores
        st.subheader("Competidores")
        if competitors:
            st.write(", ".join(competitors))
        else:
            st.info("No se encontraron competidores.")

        # Noticias
        st.subheader("Noticias recientes")
        if news:
            for n in news[:10]:
                title = n.get("title", "Sin título")
                date = n.get("published_at", n.get("date", ""))
                st.write(f"- {title} ({date})")
        else:
            st.info("No se encontraron noticias recientes.")
