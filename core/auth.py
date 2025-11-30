# core/auth.py
import json
import os
import hashlib
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

    def hash_password(self, pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()

    def login(self, username: str, password: str) -> bool:
    if username not in self.users:
        return False
    
    stored = self.users[username]["password_hash"]
    entered_hash = self.hash_password(password)

    # permite texto plano y hash
    return stored == password or stored == entered_hash

# ----------------------------
# Sesión Streamlit
# ----------------------------
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

def login_user(username, password):
    auth = AuthManager()

    if auth.login(username, password):
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
    else:
        st.error("Usuario o contraseña incorrectos")

