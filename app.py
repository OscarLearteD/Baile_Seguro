from pathlib import Path

import streamlit as st

from src.auth import login_user, logout_user, require_auth
from src.config import APP_NAME, PAGE_ICON, PAGE_LAYOUT, UPLOADS_DIR
from src.db import initialize_database
from src.seed import seed_database_if_needed
from src.styles import inject_global_styles
from src.views import (
    render_admin_screen,
    render_calendar_day_screen,
    render_dashboard,
    render_level_screen,
    render_login_screen,
    render_slot_videos_screen,
    render_video_screen,
)


def bootstrap() -> None:
    Path("data").mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()
    seed_database_if_needed()


def initialize_session_state() -> None:
    defaults = {
        # Auth
        "authenticated": False,
        "user": None,
        # Navegación base
        "screen": "login",
        "selected_category": None,
        "selected_level": None,
        # Calendario — None significa "usar mes actual"
        "calendar_year": None,
        "calendar_month": None,
        # Navegación por calendario
        "selected_date": None,
        "selected_slot_id": None,
        "selected_slot_name": None,
        "selected_time_block": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state="collapsed",
    )

    bootstrap()
    initialize_session_state()
    inject_global_styles()

    if st.session_state.get("authenticated"):
        require_auth()

    if not st.session_state.get("authenticated"):
        render_login_screen(on_login=login_user)
        return

    screen = st.session_state.get("screen", "dashboard")

    if screen == "dashboard":
        render_dashboard(on_logout=logout_user)
    elif screen == "levels":
        render_level_screen(on_logout=logout_user)
    elif screen == "videos":
        render_video_screen(on_logout=logout_user)
    elif screen == "admin":
        render_admin_screen(on_logout=logout_user)
    elif screen == "calendar_day":
        render_calendar_day_screen(on_logout=logout_user)
    elif screen == "slot_videos":
        render_slot_videos_screen(on_logout=logout_user)
    else:
        st.session_state["screen"] = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()
