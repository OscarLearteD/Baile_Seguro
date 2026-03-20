import calendar as cal_module
from datetime import date, datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.auth import hash_password, is_admin, register_user as auth_register_user
from src.config import (
    CATEGORIES,
    DAY_NAMES_ES,
    DEFAULT_THUMBNAIL,
    LEVELS,
    MONTH_NAMES_ES,
    TIME_BLOCKS,
)
from src.db import (
    create_slot,
    delete_slot,
    execute_insert,
    execute_query,
    fetch_all,
    fetch_slot_counts_for_month,
    fetch_slot_videos_for_user,
    fetch_slots_for_date,
    fetch_upcoming_slots,
    fetch_vacation_days,
    fetch_vacation_map,
    set_vacation_days,
    update_slot,
)
from src.utils import (
    get_video_source_type,
    is_valid_url,
    navigate_to,
    sanitize_text,
    save_uploaded_thumbnail,
    save_uploaded_video,
    youtube_embed_url,
)


# ---------------------------------------------------------------------------
# Componentes de cabecera reutilizables
# ---------------------------------------------------------------------------

def render_app_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_registration_form() -> None:
    levels = fetch_all("SELECT id, name FROM levels ORDER BY sort_order ASC")
    level_options = {row["name"]: row["id"] for row in levels}
    level_names = list(level_options.keys())

    with st.form("register_form", clear_on_submit=True):
        st.markdown("### Crear cuenta")

        full_name = st.text_input("Nombre", placeholder="Tu nombre")
        first_surname = st.text_input("Primer apellido", placeholder="Tu primer apellido")
        username = st.text_input("Nombre de usuario", placeholder="Ej. maria123")
        password = st.text_input("Contraseña", type="password", placeholder="Elige una contraseña")
        confirm_password = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña")
        phone = st.text_input("Teléfono", placeholder="Ej. 612345678")

        dance_role_label = st.radio(
            "Rol en el baile",
            ["Leader", "Follower", "Ambos"],
            horizontal=True,
        )

        dance_style_label = st.radio(
            "Estilos de baile",
            ["Salsa", "Bachata", "Ambos", "Otros"],
            horizontal=True,
        )

        level_name = st.selectbox("Nivel", level_names) if level_names else None

        submitted = st.form_submit_button("Crear cuenta")

        if submitted:
            role_map = {"Leader": "leader", "Follower": "follower", "Ambos": "both"}
            style_map = {
                "Salsa": ["Salsa"],
                "Bachata": ["Bachata"],
                "Ambos": ["Salsa", "Bachata"],
                "Otros": ["Otros"],
            }

            success, message = auth_register_user({
                "full_name": full_name,
                "first_surname": first_surname,
                "username": username,
                "password": password,
                "confirm_password": confirm_password,
                "phone": phone,
                "dance_role": role_map[dance_role_label],
                "dance_styles": style_map[dance_style_label],
                "level_id": level_options.get(level_name) if level_name else None,
            })

            if success:
                st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
            else:
                st.error(message)


def render_login_screen(on_login) -> None:
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    render_app_header(
        "Tu escuela de baile, en tu móvil",
        "Accede a tus vídeos privados de salsa, bachata y otros estilos de forma simple y segura.",
    )

    tab_login, tab_register = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### Iniciar sesión")
            username = st.text_input("Usuario", placeholder="Ej. maria")
            password = st.text_input("Contraseña", type="password", placeholder="Introduce tu contraseña")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                success, message = on_login(username, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        with st.expander("Credenciales de prueba"):
            st.write("Admin: admin  |  Contraseña: AdminDance2026!")
            st.write("Usuario: maria  |  Contraseña: Dance2026!")
            st.write("Usuario: oscar  |  Contraseña: BailaSeguro2026!")

    with tab_register:
        render_registration_form()


def render_top_bar(on_logout=None) -> None:
    user = st.session_state.get("user", {})

    _logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
    import base64 as _b64
    _logo_tag = (
        f'<img src="data:image/png;base64,{_b64.b64encode(_logo_path.read_bytes()).decode()}"'
        f' alt="Baile Seguro"'
        f' style="display:block;object-fit:contain;width:auto;max-height:56px;">'
        if _logo_path.exists() else ""
    )

    full_name = user.get("full_name", "")
    role = user.get("role", "student")

    st.markdown(
        """
        <style>
        /* ── Logo+text group ─────────────────────────────────────────── */
        .hdr-left {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
            overflow: visible;
        }

        /* ── Header card: scope every rule with :has(.hdr-left) ─────── */
        /* Targets the stHorizontalBlock/stColumns that contains our header */
        [data-testid="stHorizontalBlock"]:has(.hdr-left),
        [data-testid="stColumns"]:has(.hdr-left) {
            align-items: center !important;
            flex-wrap: nowrap !important;         /* never stack on mobile */
            background: white;
            border-radius: 16px;
            padding: 0.75rem 1rem;
            box-shadow: 0 4px 12px rgba(57,56,54,0.07);
            border: 1px solid #e9dfcd;
            margin-bottom: 1rem;
        }

        /* Left column: take remaining space, allow shrink, no overflow clip */
        [data-testid="stHorizontalBlock"]:has(.hdr-left) [data-testid="stColumn"]:first-child,
        [data-testid="stColumns"]:has(.hdr-left) [data-testid="stColumn"]:first-child {
            flex: 1 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
            overflow: visible !important;
        }

        /* Button columns: shrink to fit content, never full-width */
        [data-testid="stHorizontalBlock"]:has(.hdr-left) [data-testid="stColumn"]:not(:first-child),
        [data-testid="stColumns"]:has(.hdr-left) [data-testid="stColumn"]:not(:first-child) {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: fit-content !important;
        }

        /* Buttons: compact width, never stretch to column width */
        [data-testid="stHorizontalBlock"]:has(.hdr-left) [data-testid="stButton"] > button,
        [data-testid="stColumns"]:has(.hdr-left) [data-testid="stButton"] > button {
            width: auto !important;
        }

        /* Hide user-info text on very small screens */
        @media (max-width: 480px) { .hdr-user-text { display: none; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_admin, col_logout = st.columns([5, 1, 1])

    with col_left:
        st.markdown(
            f"""
            <div class="hdr-left">
                {_logo_tag}
                <div class="small-note hdr-user-text">
                    Conectado como <strong>{full_name}</strong> · {role}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_admin:
        if is_admin():
            if st.button("Admin", key="go_admin"):
                navigate_to("admin")

    with col_logout:
        if on_logout and st.button("Salir", key=f"logout_{st.session_state.get('screen', 'screen')}"):
            on_logout()


# ---------------------------------------------------------------------------
# Calendario mensual
# ---------------------------------------------------------------------------

def render_calendar(vacation_map: dict | None = None) -> None:
    """
    Renderiza un calendario mensual navegable.
    Cada día es un botón clickable que navega a la pantalla del día.
    El grid de 7 columnas se fuerza a permanecer en fila en móvil
    mediante CSS Grid override en styles.py.

    vacation_map: dict {date_str: label} de días marcados como vacaciones.
                  Esos días se renderizan como celdas no-interactivas.
    """
    vacation_map = vacation_map or {}
    today = date.today()
    year = st.session_state.get("calendar_year") or today.year
    month = st.session_state.get("calendar_month") or today.month

    with st.container(border=True):
        # Canal JS→Python: input oculto con placeholder único como selector
        nav_action = st.text_input(
            "", key="cal_nav_action",
            label_visibility="collapsed",
            placeholder="cal_nav_hidden",
        )
        if nav_action == "prev":
            st.session_state["cal_nav_action"] = ""
            if month == 1:
                st.session_state["calendar_month"] = 12
                st.session_state["calendar_year"] = year - 1
            else:
                st.session_state["calendar_month"] = month - 1
                st.session_state["calendar_year"] = year
            st.rerun()
        elif nav_action == "next":
            st.session_state["cal_nav_action"] = ""
            if month == 12:
                st.session_state["calendar_month"] = 1
                st.session_state["calendar_year"] = year + 1
            else:
                st.session_state["calendar_month"] = month + 1
                st.session_state["calendar_year"] = year
            st.rerun()

        # Header: HTML flexbox con flechas reales — no depende de st.columns()
        today_hint = (
            f"Hoy: {today.day}"
            if (year == today.year and month == today.month)
            else ""
        )
        btn_style = (
            "width:48px;height:48px;border-radius:50%;border:none;cursor:pointer;"
            "background:linear-gradient(135deg,#393836,#746f6a);"
            "color:#e9dfcd;font-size:1.2rem;font-weight:700;flex-shrink:0;"
            "box-shadow:0 4px 14px rgba(57,56,54,0.35);"
        )
        components.html(
            f"""
            <div style="display:flex;align-items:center;
                        justify-content:space-between;padding:4px 2px 2px 2px;">
              <button style="{btn_style}" onclick="sendNav('prev')">&#9664;</button>
              <div style="text-align:center;flex:1;padding:0 0.5rem;">
                <div style="font-size:1rem;font-weight:800;color:#1a1917;
                            line-height:1.3;">{MONTH_NAMES_ES[month]} {year}</div>
                <div style="font-size:0.75rem;color:#cca865;font-weight:600;">
                  {today_hint}</div>
              </div>
              <button style="{btn_style}" onclick="sendNav('next')">&#9654;</button>
            </div>
            <script>
            function sendNav(action) {{
              var input = window.parent.document.querySelector(
                'input[placeholder="cal_nav_hidden"]'
              );
              if (!input) return;
              var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
              ).set;
              setter.call(input, action);
              input.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
            </script>
            """,
            height=68,
        )

        # --- Cabecera de días de la semana ---
        day_labels = ["L", "M", "X", "J", "V", "S", "D"]
        header_cols = st.columns(7)
        for i, label in enumerate(day_labels):
            with header_cols[i]:
                st.markdown(
                    f"<div class='cal-day-header'>{label}</div>",
                    unsafe_allow_html=True,
                )

        # --- Grid de semanas ---
        today_str = today.strftime("%Y-%m-%d")
        month_weeks = cal_module.monthcalendar(year, month)

        for week in month_weeks:
            week_cols = st.columns(7)
            for i, day in enumerate(week):
                with week_cols[i]:
                    if day == 0:
                        # Día fuera del mes: celda vacía
                        st.markdown("<div class='cal-empty'></div>", unsafe_allow_html=True)
                    else:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        if date_str in vacation_map:
                            # Día de vacaciones: celda no-interactiva con tooltip
                            tooltip = vacation_map[date_str] or "Sin clases"
                            st.markdown(
                                f"<div class='cal-vacation' title='{tooltip}'>{day}</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            # Día normal: botón navegable
                            label = f"·{day}·" if date_str == today_str else str(day)
                            if st.button(label, key=f"cal_d_{date_str}"):
                                st.session_state["selected_date"] = date_str
                                st.session_state["screen"] = "calendar_day"
                                st.rerun()

        # Resaltar el botón de hoy con JS: busca por el texto ·N· y aplica estilos
        components.html(
            """
            <script>
            (function() {
                function styleToday() {
                    var buttons = window.parent.document.querySelectorAll(
                        '[data-testid="stButton"] > button'
                    );
                    buttons.forEach(function(btn) {
                        var p = btn.querySelector('p');
                        var text = p ? p.innerText.trim() : btn.innerText.trim();
                        if (text && text.startsWith('\u00b7') && text.endsWith('\u00b7')) {
                            btn.style.background = 'linear-gradient(135deg,#393836,#cca865)';
                            btn.style.color = '#e9dfcd';
                            btn.style.borderColor = 'transparent';
                            btn.style.boxShadow = '0 4px 14px rgba(204,168,101,0.4)';
                            btn.style.fontWeight = '800';
                        }
                    });
                }
                setTimeout(styleToday, 100);
                setTimeout(styleToday, 400);
                setTimeout(styleToday, 900);
            })();
            </script>
            """,
            height=0,
        )


# ---------------------------------------------------------------------------
# Dashboard principal (home)
# ---------------------------------------------------------------------------

def render_dashboard(on_logout) -> None:
    render_top_bar(on_logout=on_logout)

    render_app_header(
        "Bienvenido a tu escuela",
        "Consulta el calendario de clases o accede a tu biblioteca de vídeos.",
    )

    # Sección 1: Calendario mensual
    st.markdown("<div class='section-label'>Calendario de clases</div>", unsafe_allow_html=True)
    render_calendar(vacation_map=fetch_vacation_map())

    # Separador visual
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Sección 2: Biblioteca por categorías (funcionalidad existente)
    st.markdown("<div class='section-label'>Biblioteca de vídeos</div>", unsafe_allow_html=True)

    for category in CATEGORIES:
        if st.button(category, key=f"cat_{category}"):
            navigate_to("levels", category=category, level=None)


# ---------------------------------------------------------------------------
# Pantalla de niveles (existente, sin cambios)
# ---------------------------------------------------------------------------

def render_level_screen(on_logout) -> None:
    category = st.session_state.get("selected_category")

    if not category:
        navigate_to("dashboard")
        return

    render_top_bar(on_logout=on_logout)

    st.markdown(
        f"<div class='breadcrumb'>Inicio / {category}</div>",
        unsafe_allow_html=True,
    )

    render_app_header(
        category,
        "Elige el nivel para ver los vídeos disponibles para tu usuario.",
    )

    if st.button("← Volver", key="back_to_dashboard"):
        navigate_to("dashboard", category=None, level=None)

    st.markdown("<div class='section-label'>Niveles</div>", unsafe_allow_html=True)

    for level in LEVELS:
        if st.button(level, key=f"level_{level}"):
            navigate_to("videos", category=category, level=level)


# ---------------------------------------------------------------------------
# Pantalla de vídeos por categoría/nivel (existente, sin cambios)
# ---------------------------------------------------------------------------

def get_authorized_videos(user_id: int, category: str, level: str):
    return fetch_all(
        """
        SELECT
            v.id,
            v.title,
            v.description,
            v.video_url,
            v.video_source_type,
            v.thumbnail_url,
            v.upload_date,
            c.name AS category_name,
            l.name AS level_name
        FROM videos v
        INNER JOIN categories c ON c.id = v.category_id
        INNER JOIN levels l ON l.id = v.level_id
        INNER JOIN user_video_permissions uvp ON uvp.video_id = v.id
        WHERE uvp.user_id = ?
          AND v.is_active = 1
          AND v.show_in_library = 1
          AND c.name = ?
          AND l.name = ?
        ORDER BY v.upload_date DESC, v.title ASC
        """,
        (user_id, category, level),
    )


def render_video_player(video) -> None:
    source_type = video["video_source_type"]
    source = video["video_url"]

    if source_type == "youtube":
        embed_url = youtube_embed_url(source)
        if embed_url:
            components.html(
                f"""
                <iframe
                    width="100%"
                    height="360"
                    src="{embed_url}?autoplay=1"
                    title="YouTube video player"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowfullscreen>
                </iframe>
                """,
                height=380,
            )
        else:
            st.error("El enlace de YouTube no es válido.")
    elif source_type == "upload":
        file_path = Path(source)
        if file_path.exists():
            st.video(str(file_path))
        else:
            st.error("El archivo de vídeo no se encuentra en el servidor.")
    else:
        st.video(source)

    if source_type in ("upload", "direct_url"):
        components.html(
            """
            <script>
            (function() {
                function tryPlay() {
                    var videos = window.parent.document.querySelectorAll('video');
                    if (videos.length === 0) { setTimeout(tryPlay, 150); return; }
                    videos.forEach(function(v) {
                        v.play().catch(function(err) {
                            console.warn('Autoplay blocked:', err);
                        });
                    });
                }
                setTimeout(tryPlay, 100);
                setTimeout(tryPlay, 500);
            })();
            </script>
            """,
            height=0,
        )


def render_video_card(video) -> None:
    vid_id = str(video["id"])
    title = video["title"]
    upload_date = video["upload_date"] or "Fecha no disponible"
    meta = f"{video['category_name']} · {video['level_name']} · {upload_date}"
    description = video["description"] or ""
    thumbnail = video["thumbnail_url"] or ""
    is_playing = st.session_state.get(f"play_{vid_id}", False)

    st.markdown(
        f"<div class='video-card'><div class='video-title'>{title}</div>",
        unsafe_allow_html=True,
    )

    if is_playing:
        render_video_player(video)
    else:
        if thumbnail:
            path = Path(thumbnail)
            thumb_src = (
                f"data:image/{path.suffix.lstrip('.').lower().replace('jpg','jpeg')}"
                f";base64,{__import__('base64').b64encode(path.read_bytes()).decode()}"
                if path.exists() and path.is_file()
                else thumbnail
            )
            st.markdown(
                f"""
                <div id="thumb-wrap-{vid_id}"
                     style="position:relative;border-radius:14px;
                            overflow:hidden;margin-bottom:0.5rem;cursor:pointer;">
                    <img src="{thumb_src}"
                         style="width:100%;display:block;height:auto;" />
                    <div class="play-overlay-btn"
                         style="position:absolute;top:50%;left:50%;
                                transform:translate(-50%,-50%);
                                background:rgba(0,0,0,0.80);
                                border-radius:50%;width:64px;height:64px;
                                display:flex;align-items:center;
                                justify-content:center;color:#e9dfcd;
                                font-size:1.6rem;pointer-events:none;
                                transition:background 0.15s ease;
                                box-shadow:0 4px 16px rgba(0,0,0,0.4);">
                        &#9654;
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Wire thumbnail click → hidden Streamlit play button, golden active state
            components.html(
                f"""
                <script>
                (function() {{
                    var vidId = '{vid_id}';
                    function setup() {{
                        var par = window.parent.document;
                        var wrap = par.getElementById('thumb-wrap-' + vidId);
                        if (!wrap) {{ setTimeout(setup, 150); return; }}

                        var allBtns = Array.from(
                            par.querySelectorAll('[data-testid="stButton"] > button')
                        );
                        var targetBtn = null;
                        for (var i = 0; i < allBtns.length; i++) {{
                            var btn = allBtns[i];
                            var p = btn.querySelector('p');
                            var text = p ? p.innerText.trim() : btn.innerText.trim();
                            if (text.includes('Reproducir')) {{
                                var pos = wrap.compareDocumentPosition(btn);
                                if (pos & Node.DOCUMENT_POSITION_FOLLOWING) {{
                                    targetBtn = btn;
                                    break;
                                }}
                            }}
                        }}

                        if (targetBtn) {{
                            var container = targetBtn.closest('[data-testid="stButton"]');
                            if (container) container.style.display = 'none';

                            wrap.onclick = function() {{ targetBtn.click(); }};

                            wrap.addEventListener('mousedown', function() {{
                                var ov = wrap.querySelector('.play-overlay-btn');
                                if (ov) ov.style.background = 'rgba(204,168,101,0.88)';
                            }});
                            wrap.addEventListener('mouseup', function() {{
                                var ov = wrap.querySelector('.play-overlay-btn');
                                if (ov) ov.style.background = 'rgba(0,0,0,0.80)';
                            }});
                            wrap.addEventListener('mouseleave', function() {{
                                var ov = wrap.querySelector('.play-overlay-btn');
                                if (ov) ov.style.background = 'rgba(0,0,0,0.80)';
                            }});
                        }} else {{
                            setTimeout(setup, 300);
                        }}
                    }}
                    setTimeout(setup, 100);
                    setTimeout(setup, 600);
                }})();
                </script>
                """,
                height=0,
            )

        if st.button("▶ Reproducir", key=f"play_btn_{vid_id}"):
            st.session_state[f"play_{vid_id}"] = True
            st.rerun()

    st.markdown(f"<div class='video-meta'>{meta}</div>", unsafe_allow_html=True)
    if description:
        st.write(description)
    st.markdown("</div>", unsafe_allow_html=True)


def render_video_screen(on_logout) -> None:
    user = st.session_state.get("user")
    category = st.session_state.get("selected_category")
    level = st.session_state.get("selected_level")

    if not user or not category or not level:
        navigate_to("dashboard")
        return

    render_top_bar(on_logout=on_logout)

    st.markdown(
        f"<div class='breadcrumb'>Inicio / {category} / {level}</div>",
        unsafe_allow_html=True,
    )

    render_app_header(
        f"{category} · {level}",
        "Aquí solo aparecen los vídeos autorizados para tu cuenta.",
    )

    if st.button("← Volver", key="back_to_levels"):
        navigate_to("levels", category=category, level=None)

    videos = get_authorized_videos(
        user_id=user["id"],
        category=category,
        level=level,
    )

    st.markdown("<div class='section-label'>Vídeos disponibles</div>", unsafe_allow_html=True)

    if not videos:
        st.markdown(
            """
            <div class='empty-state'>
                <h4 style='margin-bottom: 0.35rem;'>Aún no tienes vídeos en este nivel</h4>
                <p style='margin: 0;'>Cuando la escuela te asigne nuevos contenidos, aparecerán aquí.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for video in videos:
        render_video_card(video)


# ---------------------------------------------------------------------------
# Pantalla del día (nueva)
# ---------------------------------------------------------------------------

def render_calendar_day_screen(on_logout) -> None:
    """
    Muestra las 3 franjas horarias del día seleccionado y las tarjetas
    (slots) que hay en cada franja. 9 tarjetas en total si el día tiene
    clases programadas en todas las franjas.
    """
    selected_date = st.session_state.get("selected_date")

    if not selected_date:
        navigate_to("dashboard")
        return

    render_top_bar(on_logout=on_logout)

    # Formatear fecha para mostrar en español
    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    day_name = DAY_NAMES_ES[dt.weekday()]
    month_name = MONTH_NAMES_ES[dt.month]

    st.markdown(
        f"<div class='breadcrumb'>Inicio / {day_name} {dt.day} de {month_name}</div>",
        unsafe_allow_html=True,
    )

    render_app_header(
        f"{day_name}, {dt.day} de {month_name}",
        f"Clases programadas · {dt.day} de {month_name} de {dt.year}",
    )

    if st.button("← Volver al calendario", key="back_to_calendar"):
        navigate_to("dashboard")

    # Cargar slots de este día desde la BD
    slots = fetch_slots_for_date(selected_date)

    # Agrupar por franja horaria
    slots_by_block: dict[str, list] = {block: [] for block in TIME_BLOCKS}
    for slot in slots:
        block = slot["time_block"]
        if block in slots_by_block:
            slots_by_block[block].append(slot)

    # Renderizar cada franja horaria con sus tarjetas
    for block in TIME_BLOCKS:
        st.markdown(
            f"<div class='time-block-header'>{block}</div>",
            unsafe_allow_html=True,
        )

        block_slots = slots_by_block[block]

        if not block_slots:
            st.markdown(
                "<div class='slot-empty'>Sin clases programadas en esta franja</div>",
                unsafe_allow_html=True,
            )
        else:
            for slot in block_slots:
                if st.button(
                    slot["name"],
                    key=f"slot_{slot['id']}",
                ):
                    st.session_state["selected_slot_id"] = slot["id"]
                    st.session_state["selected_slot_name"] = slot["name"]
                    st.session_state["selected_time_block"] = slot["time_block"]
                    st.session_state["screen"] = "slot_videos"
                    st.rerun()


# ---------------------------------------------------------------------------
# Pantalla de vídeos de un slot (nueva)
# ---------------------------------------------------------------------------

def render_slot_videos_screen(on_logout) -> None:
    """
    Muestra los vídeos asociados a un slot concreto (día + franja + tarjeta).
    Solo se muestran los vídeos que el usuario tiene permiso para ver.
    """
    user = st.session_state.get("user")
    selected_date = st.session_state.get("selected_date")
    slot_id = st.session_state.get("selected_slot_id")
    slot_name = st.session_state.get("selected_slot_name", "")
    time_block = st.session_state.get("selected_time_block", "")

    if not user or not selected_date or not slot_id:
        navigate_to("dashboard")
        return

    render_top_bar(on_logout=on_logout)

    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    day_name = DAY_NAMES_ES[dt.weekday()]
    month_name = MONTH_NAMES_ES[dt.month]

    st.markdown(
        f"<div class='breadcrumb'>Inicio / {dt.day} {month_name} / {time_block} / {slot_name}</div>",
        unsafe_allow_html=True,
    )

    render_app_header(
        slot_name,
        f"{day_name} {dt.day} de {month_name} · {time_block}",
    )

    if st.button("← Volver", key="back_to_day"):
        st.session_state["screen"] = "calendar_day"
        st.rerun()

    videos = fetch_slot_videos_for_user(slot_id=slot_id, user_id=user["id"])

    st.markdown("<div class='section-label'>Vídeos disponibles</div>", unsafe_allow_html=True)

    if not videos:
        st.markdown(
            """
            <div class='empty-state'>
                <h4 style='margin-bottom: 0.35rem;'>Sin vídeos disponibles</h4>
                <p style='margin: 0;'>No hay vídeos asignados a esta clase para tu cuenta.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for video in videos:
        render_video_card(video)


# ---------------------------------------------------------------------------
# Panel de administración (existente, sin cambios)
# ---------------------------------------------------------------------------

def fetch_students():
    return fetch_all(
        "SELECT id, username, full_name FROM users WHERE role = 'student' AND is_active = 1 ORDER BY full_name ASC"
    )


def fetch_categories():
    return fetch_all("SELECT id, name FROM categories ORDER BY name ASC")


def fetch_levels():
    return fetch_all("SELECT id, name FROM levels ORDER BY sort_order ASC")


def handle_create_user() -> None:
    with st.form("create_user_form", clear_on_submit=True):
        st.markdown("### Crear usuario")
        full_name = st.text_input("Nombre completo")
        username = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña inicial", type="password")
        role = st.selectbox("Rol", ["student", "admin"], index=0)
        submitted = st.form_submit_button("Crear usuario")

        if submitted:
            clean_name = sanitize_text(full_name)
            clean_username = sanitize_text(username).lower()
            clean_password = password.strip()

            if not clean_name or not clean_username or not clean_password:
                st.error("Completa todos los campos.")
                return

            existing = fetch_all(
                "SELECT id FROM users WHERE username = ?",
                (clean_username,),
            )
            if existing:
                st.error("Ese nombre de usuario ya existe.")
                return

            execute_query(
                "INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, ?)",
                (clean_username, clean_name, hash_password(clean_password), role),
            )
            st.success("Usuario creado correctamente.")


def handle_create_video() -> None:
    students = fetch_students()
    categories = fetch_categories()
    levels = fetch_levels()

    if not students:
        st.warning("Primero necesitas crear al menos un usuario alumno.")
        return

    category_names = [row["name"] for row in categories]
    level_names = [row["name"] for row in levels]
    student_labels = [f'{row["full_name"]} ({row["username"]})' for row in students]

    student_map = {
        f'{row["full_name"]} ({row["username"]})': row["id"]
        for row in students
    }
    category_map = {row["name"]: row["id"] for row in categories}
    level_map = {row["name"]: row["id"] for row in levels}

    st.markdown("### Añadir vídeo")

    # Destino al principio: condiciona qué campos se muestran
    destination = st.radio(
        "Destino del vídeo",
        ["Biblioteca de vídeos", "Día del calendario", "Ambos"],
        horizontal=True,
        key="video_destination",
    )

    title = st.text_input("Título", key="video_title")
    description = st.text_area("Descripción", key="video_description")

    source_mode = st.radio(
        "Fuente del vídeo",
        ["YouTube / URL", "Subir archivo"],
        horizontal=True,
        key="video_source_mode",
    )

    video_url = ""
    uploaded_file = None

    if source_mode == "YouTube / URL":
        video_url = st.text_input(
            "Enlace del vídeo",
            placeholder="https://www.youtube.com/watch?v=...",
            key="video_url_input",
        )
    else:
        uploaded_file = st.file_uploader(
            "Arrastra aquí tu vídeo o haz clic para seleccionarlo",
            type=["mp4", "mov", "m4v", "webm"],
            key="video_file_uploader",
            help="Formatos permitidos: mp4, mov, m4v, webm",
        )
        if uploaded_file is not None:
            st.success(f"Archivo seleccionado: {uploaded_file.name}")

    thumbnail_file = st.file_uploader(
        "Miniatura (opcional — sube una imagen desde tu dispositivo)",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        key="video_thumbnail_file",
    )
    if thumbnail_file is not None:
        st.image(thumbnail_file, width=180, caption="Vista previa")

    upload_date = st.text_input(
        "Fecha de subida",
        value=date.today().strftime("%Y-%m-%d"),
        key="video_upload_date",
    )

    # Categoría y nivel: solo relevantes cuando va a la biblioteca
    if destination in ("Biblioteca de vídeos", "Ambos"):
        category_name = st.selectbox("Categoría", category_names, key="video_category")
        level_name = st.selectbox("Nivel", level_names, key="video_level")
    else:
        category_name = category_names[0]
        level_name = level_names[0]

    selected_students = st.multiselect(
        "Usuarios con acceso",
        student_labels,
        key="video_students",
    )

    # Selector de fecha y clase: solo cuando va al calendario
    selected_slot_id = None
    if destination in ("Día del calendario", "Ambos"):
        cal_date = st.date_input(
            "Fecha de la clase",
            value=date.today(),
            key="video_cal_date",
        )
        cal_date_str = cal_date.strftime("%Y-%m-%d")
        slots = fetch_slots_for_date(cal_date_str)

        if slots:
            slot_options = {
                f"{s['time_block']} — {s['name']}": s["id"]
                for s in slots
            }
            chosen_slot_label = st.selectbox(
                "Clase del calendario",
                list(slot_options.keys()),
                key="video_slot",
            )
            selected_slot_id = slot_options[chosen_slot_label]
        else:
            st.warning("No hay clases programadas para ese día. Elige otra fecha.")

    if st.button("Guardar vídeo", key="save_video_button"):
        clean_title = sanitize_text(title)
        clean_description = sanitize_text(description)
        if thumbnail_file is not None:
            clean_thumbnail = save_uploaded_thumbnail(thumbnail_file)
        else:
            clean_thumbnail = DEFAULT_THUMBNAIL

        if not clean_title:
            st.error("El título es obligatorio.")
            return

        if not selected_students:
            st.error("Selecciona al menos un alumno con acceso.")
            return

        if destination in ("Día del calendario", "Ambos") and selected_slot_id is None:
            st.error("Selecciona una fecha con clases programadas para asignar al calendario.")
            return

        try:
            if source_mode == "Subir archivo":
                if uploaded_file is None:
                    st.error("Sube un archivo de vídeo.")
                    return

                final_source = save_uploaded_video(uploaded_file)
                source_type = "upload"
            else:
                if not is_valid_url(video_url):
                    st.error("Introduce una URL válida.")
                    return

                final_source = sanitize_text(video_url)
                source_type = get_video_source_type(final_source)

            show_in_library = 0 if destination == "Día del calendario" else 1

            video_id = execute_insert(
                """
                INSERT INTO videos (
                    title,
                    description,
                    video_url,
                    video_source_type,
                    thumbnail_url,
                    upload_date,
                    category_id,
                    level_id,
                    show_in_library
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_title,
                    clean_description,
                    final_source,
                    source_type,
                    clean_thumbnail,
                    upload_date,
                    category_map[category_name],
                    level_map[level_name],
                    show_in_library,
                ),
            )

            for label in selected_students:
                execute_query(
                    "INSERT INTO user_video_permissions (user_id, video_id) VALUES (?, ?)",
                    (student_map[label], video_id),
                )

            # El admin siempre tiene acceso a los vídeos que sube
            admin_id = st.session_state["user"]["id"]
            execute_query(
                "INSERT OR IGNORE INTO user_video_permissions (user_id, video_id) VALUES (?, ?)",
                (admin_id, video_id),
            )

            if selected_slot_id is not None:
                execute_query(
                    "INSERT OR IGNORE INTO slot_videos (slot_id, video_id) VALUES (?, ?)",
                    (selected_slot_id, video_id),
                )

            st.success("Vídeo creado y permisos asignados correctamente.")

        except ValueError as exc:
            st.error(str(exc))


def _render_admin_slot_card(slot) -> None:
    """Renders one class card with inline edit / delete-confirm actions."""
    slot_id = slot["id"]
    is_editing = st.session_state.get("admin_editing_slot") == slot_id
    confirm_del = st.session_state.get("admin_delete_confirm") == slot_id

    if is_editing:
        with st.form(f"edit_slot_{slot_id}", clear_on_submit=False):
            new_name = st.text_input("Nombre", value=slot["name"])
            tb_idx = TIME_BLOCKS.index(slot["time_block"]) if slot["time_block"] in TIME_BLOCKS else 0
            new_block = st.selectbox("Franja", TIME_BLOCKS, index=tb_idx)
            new_order = st.number_input("Orden", min_value=0, value=int(slot["sort_order"]), step=1)
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("Guardar", type="primary"):
                    clean = sanitize_text(new_name)
                    if clean:
                        update_slot(slot_id, clean, new_block, int(new_order))
                        st.session_state.pop("admin_editing_slot", None)
                        st.success(f"'{clean}' actualizada.")
                        st.rerun()
                    else:
                        st.error("El nombre no puede estar vacío.")
            with col_cancel:
                if st.form_submit_button("Cancelar"):
                    st.session_state.pop("admin_editing_slot", None)
                    st.rerun()

    elif confirm_del:
        st.warning(f"¿Eliminar **{slot['name']}**?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Sí, eliminar", key=f"confirm_del_{slot_id}", type="primary"):
                delete_slot(slot_id)
                st.session_state.pop("admin_delete_confirm", None)
                st.success("Clase eliminada.")
                st.rerun()
        with col_no:
            if st.button("Cancelar", key=f"cancel_del_{slot_id}"):
                st.session_state.pop("admin_delete_confirm", None)
                st.rerun()

    else:
        col_info, col_edit, col_del = st.columns([5, 1, 1])
        with col_info:
            st.markdown(
                f"**{slot['name']}** "
                f"<span style='color:#9a7a3f;font-size:0.82rem;'>"
                f"(orden {slot['sort_order']})</span>",
                unsafe_allow_html=True,
            )
        with col_edit:
            if st.button("✏️", key=f"edit_slot_{slot_id}", help="Editar"):
                st.session_state["admin_editing_slot"] = slot_id
                st.session_state.pop("admin_delete_confirm", None)
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_slot_{slot_id}", help="Eliminar"):
                st.session_state["admin_delete_confirm"] = slot_id
                st.session_state.pop("admin_editing_slot", None)
                st.rerun()


def _render_admin_day_panel(date_str: str, vacation_map: dict) -> None:
    """Day panel shown below the admin calendar when a day is selected."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = DAY_NAMES_ES[dt.weekday()]
    month_name = MONTH_NAMES_ES[dt.month]

    st.markdown(
        f"<div class='section-label'>{day_name} {dt.day} de {month_name}</div>",
        unsafe_allow_html=True,
    )

    if date_str in vacation_map:
        label = vacation_map[date_str] or "Vacaciones"
        st.warning(f"Día marcado como vacaciones: **{label}**. "
                   "Puedes igualmente añadir/editar clases si lo necesitas.")

    slots = fetch_slots_for_date(date_str)
    slots_by_block: dict[str, list] = {block: [] for block in TIME_BLOCKS}
    for slot in slots:
        if slot["time_block"] in slots_by_block:
            slots_by_block[slot["time_block"]].append(slot)

    for block in TIME_BLOCKS:
        st.markdown(
            f"<div class='time-block-header'>{block}</div>",
            unsafe_allow_html=True,
        )
        block_slots = slots_by_block[block]
        if not block_slots:
            st.markdown(
                "<div class='slot-empty'>Sin clases en esta franja</div>",
                unsafe_allow_html=True,
            )
        else:
            for slot in block_slots:
                _render_admin_slot_card(slot)

    # ── Add class form ──
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    with st.expander("➕ Añadir clase a este día", expanded=False):
        with st.form(f"add_slot_{date_str}", clear_on_submit=True):
            new_block = st.selectbox("Franja horaria", TIME_BLOCKS)
            new_name = st.text_input("Nombre de la clase", placeholder="Ej. Salsa Básica")
            new_order = st.number_input("Orden dentro de la franja", min_value=0, value=0, step=1)
            if st.form_submit_button("Crear clase", type="primary"):
                clean = sanitize_text(new_name)
                if not clean:
                    st.error("El nombre es obligatorio.")
                else:
                    ok, msg = create_slot(
                        date=date_str,
                        time_block=new_block,
                        name=clean,
                        sort_order=int(new_order),
                    )
                    if ok:
                        st.success(f"Clase '{clean}' añadida.")
                        st.rerun()
                    else:
                        st.error(msg)


def handle_admin_calendar() -> None:
    """
    Calendar-based class management for the admin panel.
    Replaces the old flat-list 'Gestionar clases existentes'.
    """
    import json as _json

    today = date.today()
    year = st.session_state.get("admin_cal_year") or today.year
    month = st.session_state.get("admin_cal_month") or today.month
    selected_date: str | None = st.session_state.get("admin_selected_date")

    vacation_map = fetch_vacation_map()
    slot_counts = fetch_slot_counts_for_month(year, month)

    # ── JS↔Python navigation channel ──
    adm_nav = st.text_input(
        "", key="admin_nav_action",
        label_visibility="collapsed",
        placeholder="admin_nav_hidden",
    )
    if adm_nav == "prev":
        st.session_state["admin_nav_action"] = ""
        if month == 1:
            st.session_state["admin_cal_month"] = 12
            st.session_state["admin_cal_year"] = year - 1
        else:
            st.session_state["admin_cal_month"] = month - 1
            st.session_state["admin_cal_year"] = year
        st.rerun()
    elif adm_nav == "next":
        st.session_state["admin_nav_action"] = ""
        if month == 12:
            st.session_state["admin_cal_month"] = 1
            st.session_state["admin_cal_year"] = year + 1
        else:
            st.session_state["admin_cal_month"] = month + 1
            st.session_state["admin_cal_year"] = year
        st.rerun()

    with st.container(border=True):
        # ── Month/year navigation header ──
        btn_style = (
            "width:48px;height:48px;border-radius:50%;border:none;cursor:pointer;"
            "background:linear-gradient(135deg,#393836,#746f6a);"
            "color:#e9dfcd;font-size:1.2rem;font-weight:700;flex-shrink:0;"
            "box-shadow:0 4px 14px rgba(57,56,54,0.35);"
        )
        components.html(
            f"""
            <div style="display:flex;align-items:center;
                        justify-content:space-between;padding:4px 2px 2px 2px;">
              <button style="{btn_style}" onclick="sendAdmNav('prev')">&#9664;</button>
              <div style="text-align:center;flex:1;padding:0 0.5rem;">
                <div style="font-size:1rem;font-weight:800;color:#1a1917;
                            line-height:1.3;">{MONTH_NAMES_ES[month]} {year}</div>
                <div style="font-size:0.75rem;color:#cca865;font-weight:600;">
                  Haz clic en un día para gestionar sus clases</div>
              </div>
              <button style="{btn_style}" onclick="sendAdmNav('next')">&#9654;</button>
            </div>
            <script>
            function sendAdmNav(action) {{
              var input = window.parent.document.querySelector(
                'input[placeholder="admin_nav_hidden"]'
              );
              if (!input) return;
              var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
              ).set;
              setter.call(input, action);
              input.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
            </script>
            """,
            height=68,
        )

        # ── Day-of-week headers ──
        for col, lbl in zip(st.columns(7), ["L", "M", "X", "J", "V", "S", "D"]):
            with col:
                st.markdown(f"<div class='cal-day-header'>{lbl}</div>", unsafe_allow_html=True)

        # ── Day grid ──
        today_str = today.strftime("%Y-%m-%d")
        for week in cal_module.monthcalendar(year, month):
            for col, day in zip(st.columns(7), week):
                with col:
                    if day == 0:
                        st.markdown("<div class='cal-empty'></div>", unsafe_allow_html=True)
                    elif f"{year}-{month:02d}-{day:02d}" in vacation_map:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        vac_tip = vacation_map[date_str] or "Sin clases"
                        st.markdown(
                            f"<div class='cal-vacation' title='{vac_tip}'>{day}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        lbl = f"·{day}·" if date_str == today_str else str(day)
                        if st.button(lbl, key=f"adm_d_{date_str}"):
                            st.session_state["admin_selected_date"] = date_str
                            st.session_state.pop("admin_editing_slot", None)
                            st.session_state.pop("admin_delete_confirm", None)
                            st.rerun()

        # ── JS: today styling + selected day highlight + class-count badges ──
        sel_js = selected_date or ""
        counts_js = _json.dumps(dict(slot_counts))
        components.html(
            f"""
            <script>
            (function() {{
                var slotCounts = {counts_js};
                var selDate = "{sel_js}";
                var yr = {year};
                var mo = {month};

                function styleAdmDays() {{
                    var buttons = window.parent.document.querySelectorAll(
                        '[data-testid="stButton"] > button'
                    );
                    buttons.forEach(function(btn) {{
                        var p = btn.querySelector('p');
                        var raw = p ? p.innerText.trim() : btn.innerText.trim();
                        var isToday = raw.charAt(0) === '\u00b7' && raw.slice(-1) === '\u00b7';
                        var day = parseInt(raw.replace(/[\u00b7]/g, ''));
                        if (isNaN(day) || day < 1 || day > 31) return;
                        var pad = function(n) {{ return String(n).padStart(2,'0'); }};
                        var dateStr = yr + '-' + pad(mo) + '-' + pad(day);

                        if (isToday) {{
                            btn.style.background = 'linear-gradient(135deg,#393836,#cca865)';
                            btn.style.color = '#e9dfcd';
                            btn.style.borderColor = 'transparent';
                            btn.style.boxShadow = '0 4px 14px rgba(204,168,101,0.4)';
                            btn.style.fontWeight = '800';
                        }}
                        if (selDate && dateStr === selDate) {{
                            btn.style.background = 'linear-gradient(135deg,#cca865,#d6ba85)';
                            btn.style.color = '#1a1917';
                            btn.style.borderColor = 'transparent';
                            btn.style.boxShadow = '0 4px 14px rgba(204,168,101,0.35)';
                            btn.style.fontWeight = '800';
                        }}
                        var cnt = slotCounts[dateStr];
                        if (cnt && !btn.querySelector('.adm-badge')) {{
                            var badge = document.createElement('sup');
                            badge.className = 'adm-badge';
                            badge.textContent = cnt > 9 ? '9+' : String(cnt);
                            badge.style.cssText = (
                                'background:#cca865;color:#1a1917;border-radius:6px;'
                                'padding:0 3px;font-size:9px;font-weight:800;margin-left:1px;'
                            );
                            (p || btn).appendChild(badge);
                        }}
                    }});
                }}
                setTimeout(styleAdmDays, 100);
                setTimeout(styleAdmDays, 450);
                setTimeout(styleAdmDays, 950);
            }})();
            </script>
            """,
            height=0,
        )

    # ── Day panel ──
    if selected_date:
        _render_admin_day_panel(selected_date, vacation_map)
    else:
        st.markdown(
            "<div class='slot-empty'>Selecciona un día en el calendario para ver y gestionar sus clases.</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Gestión de días de vacaciones (admin)
# ---------------------------------------------------------------------------

def handle_vacation_days() -> None:
    """
    Interfaz admin para marcar / desmarcar días de vacaciones.
    El admin navega el calendario, hace clic en días para togglearlos
    y guarda los cambios con el botón "Guardar cambios".
    """
    import json as _json

    today = date.today()
    year = st.session_state.get("vac_cal_year") or today.year
    month = st.session_state.get("vac_cal_month") or today.month

    # Cargar estado pendiente desde la BD al abrir la primera vez
    if "vac_pending" not in st.session_state:
        st.session_state["vac_pending"] = fetch_vacation_map()

    vac_pending: dict = st.session_state["vac_pending"]

    st.markdown(
        "Haz clic en cualquier día para marcarlo o desmarcarlo como vacaciones. "
        "Pulsa **Guardar cambios** para persistir la selección.",
        unsafe_allow_html=False,
    )

    with st.container(border=True):
        # --- Canal JS→Python para navegación (placeholder único) ---
        vac_nav = st.text_input(
            "", key="vac_nav_action",
            label_visibility="collapsed",
            placeholder="vac_nav_hidden",
        )
        if vac_nav == "prev":
            st.session_state["vac_nav_action"] = ""
            if month == 1:
                st.session_state["vac_cal_month"] = 12
                st.session_state["vac_cal_year"] = year - 1
            else:
                st.session_state["vac_cal_month"] = month - 1
                st.session_state["vac_cal_year"] = year
            st.rerun()
        elif vac_nav == "next":
            st.session_state["vac_nav_action"] = ""
            if month == 12:
                st.session_state["vac_cal_month"] = 1
                st.session_state["vac_cal_year"] = year + 1
            else:
                st.session_state["vac_cal_month"] = month + 1
                st.session_state["vac_cal_year"] = year
            st.rerun()

        # --- Cabecera de navegación mes/año ---
        btn_style = (
            "width:48px;height:48px;border-radius:50%;border:none;cursor:pointer;"
            "background:linear-gradient(135deg,#393836,#746f6a);"
            "color:#e9dfcd;font-size:1.2rem;font-weight:700;flex-shrink:0;"
            "box-shadow:0 4px 14px rgba(57,56,54,0.35);"
        )
        components.html(
            f"""
            <div style="display:flex;align-items:center;
                        justify-content:space-between;padding:4px 2px 2px 2px;">
              <button style="{btn_style}" onclick="sendVacNav('prev')">&#9664;</button>
              <div style="text-align:center;flex:1;padding:0 0.5rem;">
                <div style="font-size:1rem;font-weight:800;color:#1a1917;
                            line-height:1.3;">{MONTH_NAMES_ES[month]} {year}</div>
              </div>
              <button style="{btn_style}" onclick="sendVacNav('next')">&#9654;</button>
            </div>
            <script>
            function sendVacNav(action) {{
              var input = window.parent.document.querySelector(
                'input[placeholder="vac_nav_hidden"]'
              );
              if (!input) return;
              var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
              ).set;
              setter.call(input, action);
              input.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
            </script>
            """,
            height=68,
        )

        # --- Cabecera días de semana ---
        day_labels = ["L", "M", "X", "J", "V", "S", "D"]
        for col, lbl in zip(st.columns(7), day_labels):
            with col:
                st.markdown(
                    f"<div class='cal-day-header'>{lbl}</div>",
                    unsafe_allow_html=True,
                )

        # --- Grid de días ---
        today_str = today.strftime("%Y-%m-%d")
        for week in cal_module.monthcalendar(year, month):
            for col, day in zip(st.columns(7), week):
                with col:
                    if day == 0:
                        st.markdown("<div class='cal-empty'></div>", unsafe_allow_html=True)
                    else:
                        date_str = f"{year}-{month:02d}-{day:02d}"
                        is_vac = date_str in vac_pending
                        # Vacation days use ✕ prefix so JS can find and style them
                        if is_vac:
                            btn_lbl = f"✕{day}"
                        elif date_str == today_str:
                            btn_lbl = f"·{day}·"
                        else:
                            btn_lbl = str(day)

                        if st.button(btn_lbl, key=f"vac_d_{date_str}"):
                            if is_vac:
                                del st.session_state["vac_pending"][date_str]
                            else:
                                # Label is set at save time; pre-fill with current input
                                st.session_state["vac_pending"][date_str] = ""
                            st.rerun()

        # --- JS: style vacation buttons (✕ prefix) and today button ---
        components.html(
            """
            <script>
            (function() {
                function styleVacDays() {
                    var buttons = window.parent.document.querySelectorAll(
                        '[data-testid="stButton"] > button'
                    );
                    buttons.forEach(function(btn) {
                        var p = btn.querySelector('p');
                        var text = p ? p.innerText.trim() : btn.innerText.trim();
                        if (text && text.charAt(0) === '\u2715') {
                            btn.style.background = 'linear-gradient(135deg,#cca865,#d6ba85)';
                            btn.style.color = '#1a1917';
                            btn.style.borderColor = 'transparent';
                            btn.style.fontWeight = '700';
                            btn.style.opacity = '0.9';
                        }
                        if (text && text.charAt(0) === '\u00b7' && text.slice(-1) === '\u00b7') {
                            btn.style.background = 'linear-gradient(135deg,#393836,#cca865)';
                            btn.style.color = '#e9dfcd';
                            btn.style.borderColor = 'transparent';
                            btn.style.boxShadow = '0 4px 14px rgba(204,168,101,0.4)';
                            btn.style.fontWeight = '800';
                        }
                    });
                }
                setTimeout(styleVacDays, 100);
                setTimeout(styleVacDays, 400);
                setTimeout(styleVacDays, 900);
            })();
            </script>
            """,
            height=0,
        )

    # --- Etiqueta y guardado ---
    col_lbl, col_btn = st.columns([3, 1])
    with col_lbl:
        vac_label = st.text_input(
            "Etiqueta del periodo (opcional)",
            key="vac_label_input",
            placeholder="Ej. Semana Santa, Navidad...",
        )
    with col_btn:
        st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        if st.button("Guardar cambios", key="save_vacation_days", type="primary"):
            label_val = vac_label.strip()
            entries = [
                (d, lbl if lbl else label_val)
                for d, lbl in st.session_state["vac_pending"].items()
            ]
            set_vacation_days(entries)
            # Refresh pending from DB so labels are up to date
            st.session_state["vac_pending"] = fetch_vacation_map()
            st.success(f"Guardados {len(entries)} días de vacaciones.")

    # --- Resumen de días marcados ---
    if vac_pending:
        month_prefix = f"{year}-{month:02d}-"
        month_vac = {d: lbl for d, lbl in sorted(vac_pending.items()) if d.startswith(month_prefix)}
        total = len(vac_pending)

        if month_vac:
            items = []
            for d, lbl in month_vac.items():
                day_num = d.split("-")[2].lstrip("0")
                items.append(f"{day_num} {MONTH_NAMES_ES[int(d.split('-')[1])]}" + (f" ({lbl})" if lbl else ""))
            st.markdown(
                f"<div class='video-meta'><strong>Este mes:</strong> {', '.join(items)}</div>",
                unsafe_allow_html=True,
            )
        if total > len(month_vac):
            st.caption(f"Total en todos los meses: {total} días marcados.")
    else:
        st.info("No hay días de vacaciones marcados.")


def render_admin_screen(on_logout) -> None:
    if not is_admin():
        st.error("No tienes permisos para acceder al panel admin.")
        navigate_to("dashboard")
        return

    render_top_bar(on_logout=on_logout)

    st.markdown(
        "<div class='breadcrumb'>Inicio / Administración</div>",
        unsafe_allow_html=True,
    )

    render_app_header(
        "Panel de administración",
        "Gestiona usuarios, sube vídeos y asigna permisos desde una única pantalla.",
    )

    if st.button("← Volver al inicio", key="back_from_admin"):
        navigate_to("dashboard", category=None, level=None)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Usuarios", "Vídeos", "Calendario", "Resumen", "Vacaciones"])

    with tab1:
        handle_create_user()
        users = fetch_all(
            "SELECT full_name, username, role, is_active FROM users ORDER BY created_at DESC"
        )
        st.markdown("### Usuarios actuales")
        st.dataframe(users, use_container_width=True, hide_index=True)

    with tab2:
        handle_create_video()
        videos = fetch_all(
            """
            SELECT
                v.title,
                v.video_source_type,
                c.name AS category,
                l.name AS level,
                v.upload_date
            FROM videos v
            INNER JOIN categories c ON c.id = v.category_id
            INNER JOIN levels l ON l.id = v.level_id
            ORDER BY v.created_at DESC
            """
        )
        st.markdown("### Vídeos registrados")
        st.dataframe(videos, use_container_width=True, hide_index=True)

    with tab3:
        handle_admin_calendar()

    with tab4:
        total_users = fetch_all("SELECT COUNT(*) AS total FROM users")[0]["total"]
        total_students = fetch_all("SELECT COUNT(*) AS total FROM users WHERE role = 'student'")[0]["total"]
        total_videos = fetch_all("SELECT COUNT(*) AS total FROM videos")[0]["total"]
        total_permissions = fetch_all("SELECT COUNT(*) AS total FROM user_video_permissions")[0]["total"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Usuarios totales", total_users)
            st.metric("Alumnos", total_students)
        with col2:
            st.metric("Vídeos", total_videos)
            st.metric("Permisos", total_permissions)

    with tab5:
        handle_vacation_days()
