import streamlit as st
from core.auth import login_user

def login_screen():
    st.title("AppFinanzAr")
    st.write("Por favor, ingresa tus credenciales")

    # Usamos keys únicas para evitar StreamlitDuplicateElementId
    username = st.text_input("Usuario", key="login_username")
    password = st.text_input("Contraseña", type="password", key="login_password")

    # Botón con key único
    if st.button("Login", key="login_button"):
        login_user(username, password)
