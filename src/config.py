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

DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1519925610903-381054cc2a1c?auto=format&fit=crop&w=1200&q=80"
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "m4v", "webm"}
MAX_UPLOAD_MB = 200