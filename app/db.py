"""Database engine, session factory and declarative base."""
from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker | None = None


def init_engine(url: str | None = None):
    global _engine, _SessionLocal
    url = url or config.settings.database_url
    kwargs = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    _engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def _fk_on(dbapi_conn, _):  # enforce foreign keys in SQLite
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.close()
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def engine():
    if _engine is None:
        init_engine()
    return _engine


def create_all() -> None:
    """Create tables (development / tests). Production uses `alembic upgrade head`."""
    from app import models  # noqa: F401  (register models)
    Base.metadata.create_all(engine())


def get_session() -> Iterator[Session]:
    if _SessionLocal is None:
        init_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session() -> Session:
    if _SessionLocal is None:
        init_engine()
    return _SessionLocal()


def migrate() -> None:
    """Bring the schema to the latest Alembic revision (used at application start)."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    cfg = Config(str(config.BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(config.BASE_DIR / "migrations"))
    insp = inspect(engine())
    tables = set(insp.get_table_names())
    if "project" in tables and "alembic_version" not in tables:
        command.stamp(cfg, "head")  # database created by create_all (tests/dev): adopt it
    command.upgrade(cfg, "head")
