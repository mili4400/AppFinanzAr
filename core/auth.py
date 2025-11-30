import json
import os
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users_example.json")

class AuthManager:
    def __init__(self):
        self.users = self.load_users()

    def load_users(self):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                users = json.load(f)
            return {u["username"]: u for u in users}
        except Exception as e:
            print("[ERROR] No se pudo leer users_example.json:", e)
            return {}

    def login(self, username: str, password: str) -> bool:
        """Login simple: usuario/contraseña en texto plano"""
        if username not in self.users:
            return False
        return self.users[username]["password"] == password


# ---------------------------
# Streamlit session helpers
# ---------------------------
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    if "login_attempted" not in st.session_state:
        st.session_state["login_attempted"] = False

def login_user(username, password):
    auth = AuthManager()
    st.session_state["login_attempted"] = True

    if auth.login(username, password):
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.success(f"Bienvenido, {username}!")
    else:
        st.session_state["logged_in"] = False
        st.error("Usuario o contraseña incorrectos")
