import bcrypt
import streamlit as st

from src.db import fetch_one



def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")



def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False



def get_user_by_username(username: str):
    return fetch_one(
        """
        SELECT id, username, full_name, password_hash, role, is_active
        FROM users
        WHERE username = ?
        LIMIT 1
        """,
        (username.strip().lower(),),
    )



def login_user(username: str, password: str) -> tuple[bool, str]:
    clean_username = username.strip().lower()
    clean_password = password.strip()

    if not clean_username or not clean_password:
        return False, "Introduce usuario y contraseña."

    user = get_user_by_username(clean_username)
    if user is None:
        return False, "Credenciales inválidas."

    if int(user["is_active"]) != 1:
        return False, "Tu cuenta está desactivada."

    if not verify_password(clean_password, user["password_hash"]):
        return False, "Credenciales inválidas."

    st.session_state["authenticated"] = True
    st.session_state["user"] = {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
    }
    st.session_state["screen"] = "dashboard"
    st.session_state["selected_category"] = None
    st.session_state["selected_level"] = None
    return True, "Acceso correcto."



def logout_user() -> None:
    st.session_state.clear()
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["screen"] = "login"
    st.session_state["selected_category"] = None
    st.session_state["selected_level"] = None
    st.rerun()



def require_auth() -> None:
    if not st.session_state.get("authenticated") or not st.session_state.get("user"):
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
        st.session_state["screen"] = "login"
        st.warning("Debes iniciar sesión para acceder.")
        st.stop()



def is_admin() -> bool:
    user = st.session_state.get("user")
    return bool(user and user.get("role") == "admin")