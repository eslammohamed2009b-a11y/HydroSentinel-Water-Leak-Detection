"""Database engine and session factories."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from threading import RLock

from backend.core.config import settings


engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
_bootstrapped = False
_bootstrap_lock = RLock()


def ensure_database_ready() -> None:
    global _bootstrapped
    with _bootstrap_lock:
        if _bootstrapped:
            return

        from backend.services.bootstrap_service import initialize_database
        from backend.services.bootstrap_service import seed_default_data

        # In production initialize_database is deliberately a no-op: Alembic
        # must have supplied the schema before this safe, idempotent seed step.
        initialize_database()
        session = SessionLocal()
        try:
            seed_default_data(session)
            _bootstrapped = True
        finally:
            session.close()


def get_db_session():
    ensure_database_ready()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
