import calendar as cal_module
from datetime import date, datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.auth import hash_password, is_admin
from src.config import (
    CATEGORIES,
    DAY_NAMES_ES,
    DEFAULT_THUMBNAIL,
    LEVELS,
    MONTH_NAMES_ES,
    TIME_BLOCKS,
)
from src.db import (
    execute_insert,
    execute_query,
    fetch_all,
    fetch_slot_videos_for_user,
    fetch_slots_for_date,
)
from src.utils import (
    get_video_source_type,
    is_valid_url,
    navigate_to,
    sanitize_text,
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


def render_login_screen(on_login) -> None:
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    render_app_header(
        "Tu escuela de baile, en tu móvil",
        "Accede a tus vídeos privados de salsa, bachata y otros estilos de forma simple y segura.",
    )

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


def render_top_bar(on_logout=None) -> None:
    user = st.session_state.get("user", {})
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(
            f"<div class='small-note'>Conectado como <strong>{user.get('full_name', '')}</strong> · {user.get('role', 'student')}</div>",
            unsafe_allow_html=True,
        )

    with col2:
        if is_admin():
            if st.button("Admin", key="go_admin"):
                navigate_to("admin")

    with col3:
        if on_logout and st.button("Salir", key=f"logout_{st.session_state.get('screen', 'screen')}"):
            on_logout()


# ---------------------------------------------------------------------------
# Calendario mensual
# ---------------------------------------------------------------------------

def render_calendar() -> None:
    """
    Renderiza un calendario mensual navegable.
    Cada día es un botón clickable que navega a la pantalla del día.
    Usa st.columns(7) para el grid semanal (mobile-first: celdas cuadradas).
    """
    today = date.today()
    year = st.session_state.get("calendar_year") or today.year
    month = st.session_state.get("calendar_month") or today.month

    st.markdown("<div class='cal-wrapper'>", unsafe_allow_html=True)

    # --- Cabecera: mes/año y flechas de navegación ---
    col_prev, col_title, col_next = st.columns([1, 4, 1])

    with col_prev:
        if st.button("◀", key="cal_prev_month"):
            if month == 1:
                st.session_state["calendar_month"] = 12
                st.session_state["calendar_year"] = year - 1
            else:
                st.session_state["calendar_month"] = month - 1
                st.session_state["calendar_year"] = year
            st.rerun()

    with col_title:
        today_hint = (
            f"Hoy: {today.day}"
            if (year == today.year and month == today.month)
            else ""
        )
        st.markdown(
            f"<div class='cal-month-title'>{MONTH_NAMES_ES[month]} {year}</div>"
            f"<div class='cal-today-hint'>{today_hint}</div>",
            unsafe_allow_html=True,
        )

    with col_next:
        if st.button("▶", key="cal_next_month"):
            if month == 12:
                st.session_state["calendar_month"] = 1
                st.session_state["calendar_year"] = year + 1
            else:
                st.session_state["calendar_month"] = month + 1
                st.session_state["calendar_year"] = year
            st.rerun()

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
                    # Marcador visual para el día de hoy
                    label = f"· {day} ·" if date_str == today_str else str(day)
                    if st.button(label, key=f"cal_d_{date_str}"):
                        st.session_state["selected_date"] = date_str
                        st.session_state["screen"] = "calendar_day"
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


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
    render_calendar()

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
                    src="{embed_url}"
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


def render_video_card(video) -> None:
    st.markdown("<div class='video-card'>", unsafe_allow_html=True)

    if video["thumbnail_url"]:
        st.image(video["thumbnail_url"], use_container_width=True)

    st.markdown(
        f"<div class='video-title'>{video['title']}</div>",
        unsafe_allow_html=True,
    )

    upload_date = video["upload_date"] or "Fecha no disponible"

    st.markdown(
        f"<div class='video-meta'>{video['category_name']} · {video['level_name']} · {upload_date}</div>",
        unsafe_allow_html=True,
    )

    if video["description"]:
        st.write(video["description"])

    render_video_player(video)
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

    thumbnail_url = st.text_input(
        "Miniatura (opcional)",
        value=DEFAULT_THUMBNAIL,
        key="video_thumbnail",
    )

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
        clean_thumbnail = sanitize_text(thumbnail_url) if thumbnail_url else DEFAULT_THUMBNAIL

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

            if selected_slot_id is not None:
                execute_query(
                    "INSERT OR IGNORE INTO slot_videos (slot_id, video_id) VALUES (?, ?)",
                    (selected_slot_id, video_id),
                )

            st.success("Vídeo creado y permisos asignados correctamente.")

        except ValueError as exc:
            st.error(str(exc))


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

    tab1, tab2, tab3 = st.tabs(["Usuarios", "Vídeos", "Resumen"])

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
