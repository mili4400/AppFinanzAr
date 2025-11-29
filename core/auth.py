import json
import os
import hashlib
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users_example.json")


class AuthManager:
    """
    Manejo de usuarios: login, creación y validación de credenciales.
    """

    def __init__(self):
        self.users = self.load_users()

    def load_users(self):
        """
        Carga usuarios desde users_example.json.
        Devuelve un diccionario {username: user_data}.
        """
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                users = json.load(f)
            return {u["username"]: u for u in users}
        except Exception as e:
            print("[ERROR] No se pudo leer users_example.json:", e)
            return {}

    def hash_password(self, pwd: str) -> str:
        """Hashea la contraseña con SHA-256"""
        return hashlib.sha256(pwd.encode()).hexdigest()

    def login(self, username: str, password: str) -> bool:
        """Valida usuario y contraseña"""
        if username not in self.users:
            return False
        stored_hash = self.users[username]["password_hash"]
        entered_hash = self.hash_password(password)
        return stored_hash == entered_hash

    def create_user(self, username, password, role="user", email=""):
        """Crea un usuario nuevo y lo guarda en users_example.json"""
        if username in self.users:
            raise ValueError(f"El usuario '{username}' ya existe.")

        new_user = {
            "username": username,
            "password_hash": self.hash_password(password),
            "role": role,
            "email": email
        }

        data = list(self.users.values())
        data.append(new_user)

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.users[username] = new_user
        return True


# ----------------------------
# Integración con Streamlit
# ----------------------------

def init_session():
    """
    Inicializa variables de sesión necesarias para login en Streamlit.
    """
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    if "login_error_shown" not in st.session_state:
        st.session_state["login_error_shown"] = False


def login_user(username, password):
    """
    Realiza el login usando AuthManager y actualiza st.session_state.
    Evita duplicar el mensaje de error.
    """
    auth = AuthManager()
    if auth.login(username, password):
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["login_error_shown"] = False
        st.experimental_rerun()
    else:
        if not st.session_state["login_error_shown"]:
            st.error("Usuario o contraseña incorrectos")
            st.session_state["login_error_shown"] = True
