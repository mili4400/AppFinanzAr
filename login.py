# login.py
import streamlit as st

def authenticate(username: str, password: str) -> bool:
    """Check credentials stored in st.secrets under [users]."""
    users = st.secrets.get("users", {})
    return username in users and users[username] == password

def login_screen():
    st.markdown("<div style='max-width:420px;margin:0 auto;'>", unsafe_allow_html=True)
    st.markdown("## 🔐 Iniciar sesión", unsafe_allow_html=True)

    username = st.text_input("Usuario", key="login_username")
    password = st.text_input("Contraseña", type="password", key="login_password")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Ingresar", use_container_width=True):
            if authenticate(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Acceso correcto. Cargando app...")
                st.experimental_rerun()
            else:
                st.error("❌ Credenciales inválidas")
    with col2:
        if st.button("Borrar", use_container_width=True):
            st.session_state.pop("login_username", None)
            st.session_state.pop("login_password", None)

    st.markdown("</div>", unsafe_allow_html=True)
