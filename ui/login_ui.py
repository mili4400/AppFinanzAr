# ui/login_ui.py
import streamlit as st
from core.auth import login_user

def login_screen():
    st.title("AppFinanzAr")  # <- título corregido
    st.write("Por favor, ingresa tus credenciales")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Login"):
        login_user(username, password)
