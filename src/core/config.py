import os
from pathlib import Path


def _load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    # Load backend/.env (but never override real env vars).
    backend_dir = Path(__file__).resolve().parents[2]
    load_dotenv(backend_dir / ".env", override=False)


_load_dotenv_if_present()

class Settings:
    """
    Settings holder. Consumes environment variables if present.
    """
    APP_NAME: str = os.getenv("APP_NAME", "boilerplate-fastapi-app")
    # Prefer DATABASE_URL, but support Railway's public URL too.
    # For local dev, Railway's internal `DATABASE_URL` is unreachable; prefer the public URL if present.
    DATABASE_URL: str = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL") or "sqlite:///./app.db"

settings = Settings()