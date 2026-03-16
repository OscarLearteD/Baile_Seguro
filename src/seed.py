from src.auth import hash_password
from src.config import CATEGORIES, DEFAULT_THUMBNAIL, LEVELS
from src.db import execute_insert, execute_query, fetch_all, fetch_one


def seed_database_if_needed() -> None:
    """
    Inserta datos iniciales solo si la base de datos está vacía.
    """
    existing_user = fetch_one("SELECT id FROM users LIMIT 1")
    if existing_user:
        return

    # Categorías
    for category in CATEGORIES:
        execute_query(
            "INSERT INTO categories (name) VALUES (?)",
            (category,),
        )

    # Niveles
    for index, level in enumerate(LEVELS, start=1):
        execute_query(
            "INSERT INTO levels (name, sort_order) VALUES (?, ?)",
            (level, index),
        )

    # Usuarios iniciales
    users = [
        ("admin", "Administrador Escuela", hash_password("AdminDance2026!"), "admin"),
        ("maria", "María López", hash_password("Dance2026!"), "student"),
        ("oscar", "Óscar Lejarte", hash_password("BailaSeguro2026!"), "student"),
    ]

    for username, full_name, password_hash, role in users:
        execute_query(
            "INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, full_name, password_hash, role),
        )

    category_map = {
        row["name"]: row["id"]
        for row in fetch_all("SELECT id, name FROM categories")
    }

    level_map = {
        row["name"]: row["id"]
        for row in fetch_all("SELECT id, name FROM levels")
    }

    user_map = {
        row["username"]: row["id"]
        for row in fetch_all("SELECT id, username FROM users")
    }

    # Vídeos de ejemplo funcionales
    videos = [
        {
            "title": "Vídeo de práctica 1",
            "description": "Ejemplo funcional usando un enlace de YouTube válido.",
            "video_url": "https://www.youtube.com/watch?v=M7lc1UVf-VE",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-10",
            "category": "Salsa",
            "level": "Nivel básico",
            "allowed_users": ["maria", "oscar"],
        },
        {
            "title": "Vídeo de práctica 2",
            "description": "Ejemplo funcional para nivel medio.",
            "video_url": "https://www.youtube.com/watch?v=ScMzIvxBSi4",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-11",
            "category": "Bachata",
            "level": "Nivel básico medio",
            "allowed_users": ["maria"],
        },
        {
            "title": "Vídeo de práctica 3",
            "description": "Ejemplo funcional para usuario Óscar.",
            "video_url": "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-12",
            "category": "Salsa",
            "level": "Nivel intermedio",
            "allowed_users": ["oscar"],
        },
        {
            "title": "Body movement avanzado",
            "description": "Ejemplo adicional para la categoría Otros.",
            "video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-13",
            "category": "Otros",
            "level": "Nivel avanzado",
            "allowed_users": ["maria", "oscar"],
        },
    ]

    for video in videos:
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
                video["title"],
                video["description"],
                video["video_url"],
                video["video_source_type"],
                video["thumbnail_url"],
                video["upload_date"],
                category_map[video["category"]],
                level_map[video["level"]],
            ),
        )

        for username in video["allowed_users"]:
            execute_query(
                "INSERT INTO user_video_permissions (user_id, video_id) VALUES (?, ?)",
                (user_map[username], video_id),
            )