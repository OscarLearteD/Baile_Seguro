from pathlib import Path

APP_NAME = "Escuela de Baile"
PAGE_ICON = "💃"
PAGE_LAYOUT = "centered"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dance_school.db"
UPLOADS_DIR = DATA_DIR / "uploads"

CATEGORIES = [
    "Salsa",
    "Bachata",
    "Otros",
]

LEVELS = [
    "Nivel básico",
    "Nivel básico medio",
    "Nivel intermedio",
    "Nivel avanzado",
]

# Franjas horarias fijas para las clases del calendario
# Default (lunes, miércoles, jueves, viernes, domingo)
TIME_BLOCKS = [
    "19:00-20:00",
    "20:00-21:00",
    "21:00-22:00",
]

# Franjas por día de la semana (0=lunes … 6=domingo).
# Solo se definen los días que difieren del default.
_TIME_BLOCKS_BY_WEEKDAY: dict[int, list[str]] = {
    1: [  # Martes
        "10:30-11:30",
        "11:30-12:30",
        "19:00-20:00",
        "20:00-21:00",
        "21:00-22:00",
    ],
    5: [  # Sábado
        "17:30-18:30",
        "18:30-19:30",
    ],
}


def get_time_blocks_for_weekday(weekday: int) -> list[str]:
    """Devuelve la lista de franjas horarias para el día de la semana dado (0=lunes)."""
    return _TIME_BLOCKS_BY_WEEKDAY.get(weekday, TIME_BLOCKS)

# Nombres de meses en español (índice 1-12, el 0 es vacío)
MONTH_NAMES_ES = [
    "",
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Nombres de días de la semana en español (índice 0 = lunes, 6 = domingo)
DAY_NAMES_ES = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo",
]

DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1519925610903-381054cc2a1c?auto=format&fit=crop&w=1200&q=80"
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "m4v", "webm"}
MAX_UPLOAD_MB = 200
