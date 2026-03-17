from datetime import date, timedelta

from src.auth import hash_password
from src.config import CATEGORIES, DEFAULT_THUMBNAIL, LEVELS, TIME_BLOCKS
from src.db import execute_insert, execute_query, fetch_all, fetch_one


def seed_database_if_needed() -> None:
    """
    Inserta datos iniciales solo si la base de datos está vacía.
    Incluye usuarios, categorías, niveles, vídeos, slots de calendario
    y relaciones slot_videos con permisos de usuario.
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
            "title": "Salsa básica — pasos fundamentales",
            "description": "Clase de iniciación: postura, peso del cuerpo y pasos básicos en salsa.",
            "video_url": "https://www.youtube.com/watch?v=M7lc1UVf-VE",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-10",
            "category": "Salsa",
            "level": "Nivel básico",
            "allowed_users": ["maria", "oscar"],
        },
        {
            "title": "Bachata — movimiento de caderas",
            "description": "Técnica de caderas y coordinación para bachata.",
            "video_url": "https://www.youtube.com/watch?v=ScMzIvxBSi4",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-11",
            "category": "Bachata",
            "level": "Nivel básico medio",
            "allowed_users": ["maria"],
        },
        {
            "title": "Salsa intermedia — giros y figuras",
            "description": "Giros en pareja, conexión y dinámica de figuras.",
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
            "description": "Aislaciones corporales y expresividad para nivel avanzado.",
            "video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "video_source_type": "youtube",
            "thumbnail_url": DEFAULT_THUMBNAIL,
            "upload_date": "2026-03-13",
            "category": "Otros",
            "level": "Nivel avanzado",
            "allowed_users": ["maria", "oscar"],
        },
    ]

    video_ids = []
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
        video_ids.append(video_id)

        for username in video["allowed_users"]:
            execute_query(
                "INSERT INTO user_video_permissions (user_id, video_id) VALUES (?, ?)",
                (user_map[username], video_id),
            )

    # ---------------------------------------------------------------------------
    # Seed del calendario: slots de clase para varios días del mes actual
    # ---------------------------------------------------------------------------

    # Nombres de las tarjetas por franja horaria (3 por franja = 9 por día)
    slot_names_by_block = {
        "19:00-20:00": [
            ("Salsa Básica", 1),
            ("Bachata Iniciación", 2),
            ("Ritmos Caribeños", 3),
        ],
        "20:00-21:00": [
            ("Salsa Intermedia", 1),
            ("Bachata Sensual", 2),
            ("Rumba", 3),
        ],
        "21:00-22:00": [
            ("Salsa Avanzada", 1),
            ("Bachata Avanzada", 2),
            ("Cha-cha-chá", 3),
        ],
    }

    today = date.today()

    # Generar 6 fechas con clases: el día actual y los 5 siguientes días pares
    class_dates: list[date] = []
    cursor_date = today
    while len(class_dates) < 6:
        if cursor_date.month == today.month:
            class_dates.append(cursor_date)
        cursor_date += timedelta(days=2)

    # Crear todos los slots y recoger sus ids agrupados por (date, time_block)
    # para luego asignar vídeos de ejemplo
    all_slots: list[dict] = []

    for class_date in class_dates:
        date_str = class_date.strftime("%Y-%m-%d")
        for time_block in TIME_BLOCKS:
            for name, sort_order in slot_names_by_block[time_block]:
                slot_id = execute_insert(
                    """
                    INSERT INTO class_slots (date, time_block, name, sort_order)
                    VALUES (?, ?, ?, ?)
                    """,
                    (date_str, time_block, name, sort_order),
                )
                all_slots.append({
                    "slot_id": slot_id,
                    "date": date_str,
                    "time_block": time_block,
                    "name": name,
                })

    # Vincular vídeos a slots de ejemplo.
    # Los primeros 9 slots (un día completo) reciben un vídeo rotando entre los 4 disponibles,
    # de modo que al entrar al primer día ya se ven vídeos en todas las tarjetas.
    for i, slot in enumerate(all_slots[:9]):
        video_id = video_ids[i % len(video_ids)]
        execute_query(
            "INSERT OR IGNORE INTO slot_videos (slot_id, video_id) VALUES (?, ?)",
            (slot["slot_id"], video_id),
        )

    # El segundo día también tiene vídeos en los primeros 3 slots (primera franja)
    for slot in all_slots[9:12]:
        execute_query(
            "INSERT OR IGNORE INTO slot_videos (slot_id, video_id) VALUES (?, ?)",
            (slot["slot_id"], video_ids[0]),
        )
