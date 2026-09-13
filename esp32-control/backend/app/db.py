"""SQLAlchemy engine/session setup for the `DB_URL` SQLite database."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


def _ensure_sqlite_parent_dir(db_url: str) -> None:
    """Create the parent directory for a sqlite:/// file, if needed."""
    prefix = "sqlite:///"
    if not db_url.startswith(prefix):
        return
    db_path = db_url[len(prefix) :]
    if db_path in (":memory:", ""):
        return
    Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent_dir(settings.db_url)

_connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
engine = create_engine(settings.db_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables that don't exist yet. Safe to call repeatedly."""
    from . import models  # noqa: F401  (ensures models are registered on Base)

    Base.metadata.create_all(bind=engine)
