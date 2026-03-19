import base64
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import streamlit as st

from src.config import ALLOWED_VIDEO_EXTENSIONS, MAX_UPLOAD_MB, UPLOADS_DIR

THUMBNAILS_DIR = UPLOADS_DIR / "thumbnails"
ALLOWED_THUMBNAIL_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}



def sanitize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())



def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False



def navigate_to(screen: str, category: str | None = None, level: str | None = None) -> None:
    st.session_state["screen"] = screen
    if category is not None:
        st.session_state["selected_category"] = category
    if level is not None:
        st.session_state["selected_level"] = level
    st.rerun()



def extract_youtube_id(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if "youtu.be" in host:
            return parsed.path.strip("/") or None

        if "youtube.com" in host:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [None])[0]
            if parsed.path.startswith("/embed/"):
                return parsed.path.split("/embed/")[-1]
            if parsed.path.startswith("/shorts/"):
                return parsed.path.split("/shorts/")[-1]
        return None
    except Exception:
        return None



def get_video_source_type(url: str) -> str:
    youtube_id = extract_youtube_id(url)
    if youtube_id:
        return "youtube"
    return "direct_url"



def youtube_embed_url(url: str) -> str | None:
    youtube_id = extract_youtube_id(url)
    if not youtube_id:
        return None
    return f"https://www.youtube-nocookie.com/embed/{youtube_id}"



def save_uploaded_thumbnail(uploaded_file) -> str:
    """Guarda una imagen de miniatura en THUMBNAILS_DIR y devuelve la ruta absoluta."""
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    suffix = uploaded_file.name.split(".")[-1].lower()
    if suffix not in ALLOWED_THUMBNAIL_EXTENSIONS:
        raise ValueError("Formato no permitido. Usa jpg, jpeg, png, gif o webp.")

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", uploaded_file.name)
    target_path = THUMBNAILS_DIR / safe_name

    counter = 1
    while target_path.exists():
        stem = Path(safe_name).stem
        suffix_ext = Path(safe_name).suffix
        target_path = THUMBNAILS_DIR / f"{stem}_{counter}{suffix_ext}"
        counter += 1

    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(target_path)


def get_thumbnail_src(thumbnail: str) -> str:
    """Devuelve un src usable en HTML: data URI para archivos locales, URL para remotos."""
    if not thumbnail:
        return ""
    path = Path(thumbnail)
    if path.exists() and path.is_file():
        ext = path.suffix.lstrip(".").lower()
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f"data:image/{mime};base64,{b64}"
    return thumbnail  # URL remota u otro valor


def save_uploaded_video(uploaded_file) -> str:
    if uploaded_file is None:
        raise ValueError("No se ha subido ningún archivo.")

    suffix = uploaded_file.name.split(".")[-1].lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError("Formato no permitido. Usa mp4, mov, m4v o webm.")

    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_MB:
        raise ValueError(f"El archivo supera el límite de {MAX_UPLOAD_MB} MB.")

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", uploaded_file.name)
    target_path = UPLOADS_DIR / safe_name

    counter = 1
    while target_path.exists():
        stem = Path(safe_name).stem
        suffix_ext = Path(safe_name).suffix
        target_path = UPLOADS_DIR / f"{stem}_{counter}{suffix_ext}"
        counter += 1

    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(target_path)