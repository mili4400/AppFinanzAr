import streamlit as st
from core.auth import login_user

def login_screen():
    st.title("AppFinanzAr")
    st.write("Por favor, ingresa tus credenciales")

    username = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")

    if st.button("Login", key="login_btn"):
        login_user(username, password)
