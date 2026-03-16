from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.auth import hash_password, is_admin
from src.config import CATEGORIES, DEFAULT_THUMBNAIL, LEVELS
from src.db import execute_insert, execute_query, fetch_all
from src.utils import (
    get_video_source_type,
    is_valid_url,
    navigate_to,
    sanitize_text,
    save_uploaded_video,
    youtube_embed_url,
)


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


def render_dashboard(on_logout) -> None:
    render_top_bar(on_logout=on_logout)

    render_app_header(
        "Selecciona tu estilo",
        "Accede a tus contenidos por carpeta. Elige una categoría para ver sus niveles.",
    )

    st.markdown("<div class='section-label'>Categorías</div>", unsafe_allow_html=True)

    for category in CATEGORIES:
        if st.button(category, key=f"cat_{category}"):
            navigate_to("levels", category=category, level=None)


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
        value="2026-03-16",
        key="video_upload_date",
    )

    category_name = st.selectbox("Categoría", category_names, key="video_category")
    level_name = st.selectbox("Nivel", level_names, key="video_level")
    selected_students = st.multiselect(
        "Usuarios con acceso",
        student_labels,
        key="video_students",
    )

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
                    level_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

            for label in selected_students:
                execute_query(
                    "INSERT INTO user_video_permissions (user_id, video_id) VALUES (?, ?)",
                    (student_map[label], video_id),
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