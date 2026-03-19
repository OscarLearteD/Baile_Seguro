from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
        # Splash
        "splash_shown": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def show_splash() -> None:
    """Inyecta el splash vía JS en el documento padre para que sea visible de inmediato."""
    components.html(
        """
        <script>
        (function () {
            var doc = window.parent.document;

            // Evitar duplicados si Streamlit re-ejecuta antes de que el overlay desaparezca
            if (doc.getElementById('splash-overlay')) return;

            var overlay = doc.createElement('div');
            overlay.id = 'splash-overlay';
            overlay.style.cssText = [
                'position:fixed', 'top:0', 'left:0',
                'width:100vw', 'height:100vh',
                'background:#000',
                'display:flex', 'align-items:center', 'justify-content:center',
                'z-index:99999',
                'opacity:1',
                'transition:opacity 0.5s ease',
            ].join(';');

            var img = doc.createElement('img');
            img.src = 'https://www.clasesdesalsaybachata.com/wp-content/uploads/2018/02/logo.png';
            img.style.cssText = [
                'max-width:300px',
                'width:80vw',
                'filter:drop-shadow(0 0 24px rgba(236,72,153,0.6))',
                'animation:splashIn 0.5s ease forwards',
            ].join(';');

            var style = doc.createElement('style');
            style.textContent = '@keyframes splashIn{from{opacity:0;transform:scale(0.9)}to{opacity:1;transform:scale(1)}}';
            doc.head.appendChild(style);

            overlay.appendChild(img);
            doc.body.appendChild(overlay);

            // Fade-out y eliminación tras 2 segundos
            setTimeout(function () {
                overlay.style.opacity = '0';
                setTimeout(function () { overlay.remove(); style.remove(); }, 500);
            }, 2000);
        })();
        </script>
        """,
        height=0,
    )


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

    if not st.session_state.get("splash_shown"):
        show_splash()
        st.session_state["splash_shown"] = True

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
