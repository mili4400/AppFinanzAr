# ui/login_ui.py
import streamlit as st
from core.auth import login_user

def login_screen():
    # Logo arriba
    st.image("assets/logo_finanzapp.svg", width=200)
    
    # Título y descripción
    st.title("AppFinanzAr")
    st.write("Por favor, ingresa tus credenciales")

    # Inputs con keys únicas
    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")

    # Botón de login
    if st.button("Login", key="login_btn"):
        login_user(username, password)


