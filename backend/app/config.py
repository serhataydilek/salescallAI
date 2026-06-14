from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_UPLOAD_DIR = BACKEND_DIR / "storage" / "uploads"

_upload_dir = DEFAULT_UPLOAD_DIR


def get_upload_dir() -> Path:
    _upload_dir.mkdir(parents=True, exist_ok=True)
    return _upload_dir


def set_upload_dir(upload_dir: Path | str) -> None:
    global _upload_dir
    _upload_dir = Path(upload_dir)


def reset_upload_dir() -> None:
    global _upload_dir
    _upload_dir = DEFAULT_UPLOAD_DIR
