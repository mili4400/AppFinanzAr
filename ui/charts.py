
import plotly.graph_objects as go
import streamlit as st

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
