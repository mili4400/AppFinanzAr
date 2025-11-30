# ui/charts.py

import streamlit as st
import plotly.graph_objects as go

def comparison_chart(df, ticker1, ticker2):
    """Grafico de comparación porcentual entre dos activos."""

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], 
        y=df[f"pct_{ticker1}"],
        mode="lines",
        name=ticker1
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], 
        y=df[f"pct_{ticker2}"],
        mode="lines",
        name=ticker2
    ))

    fig.update_layout(
        title=f"Comparación de desempeño: {ticker1} vs {ticker2}",
        xaxis_title="Fecha",
        yaxis_title="Variación % desde inicio",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

def render_candlestick(df, ticker):
    fig=go.Figure(data=[go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )])
    fig.update_layout(title=f"Velas - {ticker}", height=600)
    st.plotly_chart(fig, use_container_width=True)
