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
    Crea las tablas necesarias si no existen.
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


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    """
    Devuelve una sola fila o None.
    """
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchone()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    """
    Devuelve una lista de filas.
    """
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def execute_query(query: str, params: tuple[Any, ...] = ()) -> None:
    """
    Ejecuta una query de escritura sin devolver id.
    """
    with get_connection() as conn:
        conn.execute(query, params)


def execute_insert(query: str, params: tuple[Any, ...] = ()) -> int:
    """
    Ejecuta un INSERT y devuelve el id de la fila creada.
    """
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return int(cursor.lastrowid)