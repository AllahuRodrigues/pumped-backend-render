from __future__ import annotations

from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from core.config import settings


def _ensure_schema(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ab_exposures (
              test_id TEXT NOT NULL,
              user_id TEXT NOT NULL,
              variant TEXT NOT NULL,
              exposed_at TEXT NOT NULL,
              PRIMARY KEY (test_id, user_id)
            );
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY,
              event_name TEXT NOT NULL,
              user_id TEXT NOT NULL,
              test_id TEXT,
              variant TEXT,
              properties_json TEXT,
              created_at TEXT NOT NULL
            );
            """
        )
    )


def _normalize_database_url(database_url: str) -> str:
    # SQLAlchemy expects postgresql:// (Railway sometimes provides postgres://)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


@lru_cache(maxsize=4)
def _engine_for_url(database_url: str) -> Engine:
    url = _normalize_database_url(database_url)

    connect_args = {}
    if url.startswith("sqlite:///"):
        connect_args = {"check_same_thread": False}

    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True,
    )


def get_engine() -> Engine:
    return _engine_for_url(settings.DATABASE_URL)


def get_db() -> Iterator[Connection]:
    """
    FastAPI dependency that yields a SQLAlchemy Connection inside a transaction.
    """
    engine = get_engine()
    with engine.begin() as conn:
        _ensure_schema(conn)
        yield conn


def db_healthcheck() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return True
    except Exception:
        return False