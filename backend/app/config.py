"""Application settings, loaded from environment / .env (pydantic-settings).

Privacy note: ``demo_mode`` defaults to True. Nothing touches a real inbox until
the operator explicitly opts in by setting ``DEMO_MODE=false`` and supplying
Gmail credentials.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    # Absolute path so backend/.env is found no matter which directory the server
    # is launched from (e.g. `make api` runs from the repo root).
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_prefix="", case_sensitive=False, extra="ignore"
    )

    app_name: str = "Inbox Intelligence"
    environment: str = "development"

    # --- Privacy / mode ---
    demo_mode: bool = Field(
        default=True, description="Use synthetic data only; never touch real mail."
    )

    # --- Database ---
    database_url: str = Field(default=f"sqlite:///{DATA_DIR / 'inbox.db'}")

    # --- Categorization engine ---
    # Confidence at/above which a deterministic rule short-circuits the ML stage.
    # Tuned so precise rules (known senders, corroborated signals) win, while
    # weaker keyword-only hints defer to the model.
    rule_confidence_threshold: float = 0.85
    # sentence-transformers model id; falls back to a deterministic hash embedder
    # if the optional [ml] extra is not installed.
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    knn_neighbors: int = 5

    # --- Frontend CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]

    # --- Optional Gmail (only read when demo_mode is False) ---
    gmail_address: str | None = None
    gmail_app_password: str | None = None
    gmail_fetch_limit: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()
