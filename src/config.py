"""Centralized configuration loaded from environment variables."""

import os
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill in your values."
        )
    return value


@lru_cache
def get_db_config() -> dict:
    return {
        "host": _require_env("DB_HOST"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "database": _require_env("DB_NAME"),
        "user": _require_env("DB_USER"),
        "password": _require_env("DB_PASSWORD"),
    }


def get_output_dir() -> Path:
    path = Path(os.environ.get("OUTPUT_DIR", PROJECT_ROOT / "output"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_model_cache_dir() -> Path:
    custom = os.environ.get("MODEL_CACHE_DIR")
    if custom:
        path = Path(custom)
    else:
        path = PROJECT_ROOT / "src" / "model_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_hf_environment() -> None:
    if "HF_ENDPOINT" not in os.environ:
        os.environ["HF_ENDPOINT"] = os.environ.get(
            "HF_MIRROR", "https://hf-mirror.com"
        )
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")
    cache_dir = get_model_cache_dir()
    os.environ.setdefault("TRANSFORMERS_CACHE", str(cache_dir))
    os.environ.setdefault("HF_HOME", str(cache_dir))
