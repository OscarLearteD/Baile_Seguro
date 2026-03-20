import sqlite3
from contextlib import contextmanager
from typing import Any, Generator

from src.config import DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Devuelve una conexión SQLite con row_factory tipo diccionario
    y claves foráneas activadas.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    """
    Crea todas las tablas necesarias si no existen.
    Las nuevas tablas (class_slots, slot_videos) se añaden sin romper las existentes.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sort_order INTEGER NOT NULL UNIQUE
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                video_url TEXT NOT NULL,
                video_source_type TEXT NOT NULL DEFAULT 'youtube',
                thumbnail_url TEXT,
                upload_date TEXT,
                category_id INTEGER NOT NULL,
                level_id INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (level_id) REFERENCES levels(id)
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_video_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                UNIQUE(user_id, video_id)
            );
            """
        )

        # --- Nuevas tablas para el calendario ---

        # class_slots: cada fila representa una clase concreta en un día,
        # franja horaria y nombre de tarjeta.
        # Modelo elegido: slot = fecha + franja + nombre_de_clase.
        # Los vídeos se enlazan al slot mediante slot_videos (N:N).
        # El control de acceso por usuario sigue en user_video_permissions.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS class_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_block TEXT NOT NULL,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # slot_videos: relación N:N entre class_slots y videos.
        # Un vídeo puede pertenecer a varios slots y un slot puede tener varios vídeos.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS slot_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                FOREIGN KEY (slot_id) REFERENCES class_slots(id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                UNIQUE(slot_id, video_id)
            );
            """
        )

        # Migración: añadir show_in_library si no existe todavía.
        # Los vídeos existentes mantienen show_in_library = 1 (visible en biblioteca).
        try:
            cursor.execute(
                "ALTER TABLE videos ADD COLUMN show_in_library INTEGER NOT NULL DEFAULT 1"
            )
        except Exception:
            pass  # La columna ya existe

        # vacation_days: fechas marcadas como vacaciones/sin clase.
        # date es la clave primaria (una entrada por día).
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vacation_days (
                date  TEXT PRIMARY KEY,
                label TEXT NOT NULL DEFAULT ''
            );
            """
        )

        # Migración: campo profesores en class_slots
        try:
            cursor.execute(
                "ALTER TABLE class_slots ADD COLUMN profesores TEXT"
            )
        except Exception:
            pass  # La columna ya existe

        # Migración: campos extra de perfil de usuario
        for migration in [
            "ALTER TABLE users ADD COLUMN first_surname TEXT",
            "ALTER TABLE users ADD COLUMN phone TEXT",
            "ALTER TABLE users ADD COLUMN dance_role TEXT",
        ]:
            try:
                cursor.execute(migration)
            except Exception:
                pass  # La columna ya existe


# ---------------------------------------------------------------------------
# Helpers genéricos
# ---------------------------------------------------------------------------

def fetch_one(query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    """Devuelve una sola fila o None."""
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchone()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    """Devuelve una lista de filas."""
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def execute_query(query: str, params: tuple[Any, ...] = ()) -> None:
    """Ejecuta una query de escritura sin devolver id."""
    with get_connection() as conn:
        conn.execute(query, params)


def execute_insert(query: str, params: tuple[Any, ...] = ()) -> int:
    """Ejecuta un INSERT y devuelve el id de la fila creada."""
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return int(cursor.lastrowid)


# ---------------------------------------------------------------------------
# Queries específicas del calendario
# ---------------------------------------------------------------------------

def create_slot(date: str, time_block: str, name: str, sort_order: int, profesores: str = "") -> tuple[bool, str]:
    """
    Crea un nuevo slot en el calendario.
    Devuelve (True, "") si OK o (False, mensaje) si ya existe o falla.
    """
    try:
        execute_insert(
            """
            INSERT INTO class_slots (date, time_block, name, sort_order, profesores, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (date, time_block, name, sort_order, profesores or ""),
        )
        return True, ""
    except Exception:
        return False, "Ya existe una clase con ese nombre en esa franja y fecha."


def delete_slot(slot_id: int) -> None:
    """Elimina un slot y sus vínculos de slot_videos por CASCADE."""
    execute_query("DELETE FROM class_slots WHERE id = ?", (slot_id,))


def update_slot(slot_id: int, name: str, time_block: str, sort_order: int, profesores: str = "") -> None:
    """Actualiza nombre, franja horaria, orden y profesores de un slot existente."""
    execute_query(
        "UPDATE class_slots SET name=?, time_block=?, sort_order=?, profesores=? WHERE id=?",
        (name, time_block, sort_order, profesores or "", slot_id),
    )


def fetch_slot_counts_for_month(year: int, month: int) -> dict:
    """
    Devuelve un dict {date_str: count} con el número de slots activos
    por día para el mes indicado.
    """
    rows = fetch_all(
        """
        SELECT date, COUNT(*) AS cnt
        FROM class_slots
        WHERE date LIKE ? AND is_active = 1
        GROUP BY date
        """,
        (f"{year}-{month:02d}-%",),
    )
    return {row["date"]: row["cnt"] for row in rows}


def fetch_upcoming_slots(days: int = 30) -> list[sqlite3.Row]:
    """Devuelve los slots activos de hoy en adelante (hasta `days` días)."""
    return fetch_all(
        """
        SELECT id, date, time_block, name, sort_order
        FROM class_slots
        WHERE date >= date('now')
          AND date <= date('now', ? || ' days')
          AND is_active = 1
        ORDER BY date ASC, time_block ASC, sort_order ASC
        """,
        (str(days),),
    )


def fetch_slots_for_date(date_str: str) -> list[sqlite3.Row]:
    """
    Devuelve todos los slots activos de una fecha concreta,
    ordenados por franja horaria y sort_order.
    """
    return fetch_all(
        """
        SELECT id, date, time_block, name, sort_order, profesores
        FROM class_slots
        WHERE date = ? AND is_active = 1
        ORDER BY time_block ASC, sort_order ASC
        """,
        (date_str,),
    )


def register_user(
    username: str,
    full_name: str,
    first_surname: str,
    phone: str,
    dance_role: str,
    dance_styles: list,
    level_id: int,
    password_hash: str,
) -> int:
    """
    Inserta un nuevo usuario (role='student') y asigna automáticamente permisos
    sobre todos los vídeos activos que coincidan con los estilos y nivel elegidos.
    Devuelve el id del usuario creado.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, full_name, first_surname, phone, dance_role, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 'student', 1)
            """,
            (username, full_name, first_surname, phone, dance_role, password_hash),
        )
        user_id = int(cursor.lastrowid)

        if dance_styles and level_id:
            placeholders = ",".join("?" * len(dance_styles))
            category_rows = conn.execute(
                f"SELECT id FROM categories WHERE name IN ({placeholders})",
                dance_styles,
            ).fetchall()
            category_ids = [row["id"] for row in category_rows]

            if category_ids:
                cat_placeholders = ",".join("?" * len(category_ids))
                video_rows = conn.execute(
                    f"""
                    SELECT id FROM videos
                    WHERE category_id IN ({cat_placeholders})
                      AND level_id = ?
                      AND is_active = 1
                    """,
                    (*category_ids, level_id),
                ).fetchall()

                for video_row in video_rows:
                    try:
                        conn.execute(
                            "INSERT INTO user_video_permissions (user_id, video_id) VALUES (?, ?)",
                            (user_id, video_row["id"]),
                        )
                    except Exception:
                        pass  # Permiso ya existía (UNIQUE constraint)

        return user_id


# ---------------------------------------------------------------------------
# Queries de días de vacaciones
# ---------------------------------------------------------------------------

def fetch_vacation_days() -> list[sqlite3.Row]:
    """Devuelve todas las entradas de vacation_days ordenadas por fecha."""
    return fetch_all("SELECT date, label FROM vacation_days ORDER BY date ASC")


def fetch_vacation_map() -> dict[str, str]:
    """Devuelve un dict {date_str: label} con todos los días de vacaciones."""
    return {row["date"]: row["label"] for row in fetch_vacation_days()}


def set_vacation_days(entries: list[tuple[str, str]]) -> None:
    """
    Reemplaza atómicamente la tabla vacation_days con la lista dada.
    Cada entry es (date_str, label).
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM vacation_days")
        for date_str, label in entries:
            conn.execute(
                "INSERT INTO vacation_days (date, label) VALUES (?, ?)",
                (date_str, label or ""),
            )


def fetch_slot_videos_for_user(slot_id: int, user_id: int) -> list[sqlite3.Row]:
    """
    Devuelve los vídeos de un slot concreto que el usuario tiene permiso para ver.
    La autorización se verifica contra user_video_permissions.
    """
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
        INNER JOIN slot_videos sv ON sv.video_id = v.id
        INNER JOIN categories c ON c.id = v.category_id
        INNER JOIN levels l ON l.id = v.level_id
        INNER JOIN user_video_permissions uvp ON uvp.video_id = v.id
        WHERE sv.slot_id = ?
          AND uvp.user_id = ?
          AND v.is_active = 1
        ORDER BY v.upload_date DESC, v.title ASC
        """,
        (slot_id, user_id),
    )
