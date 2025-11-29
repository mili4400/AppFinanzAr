# ui/dashboard_ui.py
import streamlit as st
from core.data_fetch import fetch_fundamentals, fetch_news

def show_dashboard():
    st.title("AppFinanzAr - Dashboard")

    ticker = st.text_input("Ingrese ticker (ej: MELI.US)", "MELI.US")

    if ticker:
        fundamentals, competitors = fetch_fundamentals(ticker)
        news = fetch_news(ticker, days_back=60)

        st.subheader("Fundamentales clave")
        if fundamentals:
            st.json(fundamentals)
        else:
            st.info("No se encontraron datos fundamentales.")

        st.subheader("Competidores")
        if competitors:
            st.write(", ".join(competitors))
        else:
            st.info("No se encontraron competidores.")

        st.subheader("Noticias recientes")
        if news:
            for n in news[:10]:
                st.write(f"- {n.get('title')} ({n.get('published_at')})")
        else:
            st.info("No se encontraron noticias recientes.")
