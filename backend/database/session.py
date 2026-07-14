"""Database engine and session factories."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings


engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
_bootstrapped = False


def ensure_database_ready() -> None:
    global _bootstrapped
    if _bootstrapped:
        return

    from backend.services.bootstrap_service import initialize_database
    from backend.services.bootstrap_service import seed_default_data

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