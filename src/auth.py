import re

import bcrypt
import streamlit as st

from src.db import fetch_one, register_user as db_register_user



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



def register_user(form_data: dict) -> tuple[bool, str]:
    """
    Valida los datos del formulario de registro y crea el usuario.
    Devuelve (True, "") si OK, o (False, "mensaje de error") si falla.
    """
    full_name = form_data.get("full_name", "").strip()
    first_surname = form_data.get("first_surname", "").strip()
    username = form_data.get("username", "").strip().lower()
    password = form_data.get("password", "").strip()
    confirm_password = form_data.get("confirm_password", "").strip()
    phone = form_data.get("phone", "").strip()
    dance_role = form_data.get("dance_role", "").strip()
    dance_styles = form_data.get("dance_styles", [])
    level_id = form_data.get("level_id")

    if not all([full_name, first_surname, username, password, confirm_password, phone, dance_role]):
        return False, "Completa todos los campos."

    if not dance_styles:
        return False, "Selecciona al menos un estilo de baile."

    if level_id is None:
        return False, "Selecciona un nivel."

    if password != confirm_password:
        return False, "Las contraseñas no coinciden."

    if not re.fullmatch(r"\d{9,15}", phone):
        return False, "El teléfono debe tener entre 9 y 15 dígitos (solo números)."

    existing = fetch_one("SELECT id FROM users WHERE username = ?", (username,))
    if existing:
        return False, "Ese nombre de usuario ya está en uso."

    try:
        db_register_user(
            username=username,
            full_name=full_name,
            first_surname=first_surname,
            phone=phone,
            dance_role=dance_role,
            dance_styles=dance_styles,
            level_id=level_id,
            password_hash=hash_password(password),
        )
        return True, ""
    except Exception as exc:
        return False, f"Error al crear la cuenta: {exc}"


def is_admin() -> bool:
    user = st.session_state.get("user")
    return bool(user and user.get("role") == "admin")