"""Readiness checks for dependencies required by the API."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models.scenario import Scenario
from backend.services.analysis_service import SCENARIO_SEED_METADATA


def database_is_ready(session: Session) -> bool:
    """Verify database connectivity and the complete seeded demo scenario set."""
    session.execute(text("SELECT 1"))
    available = set(session.scalars(select(Scenario.file_name)).all())
    return set(SCENARIO_SEED_METADATA).issubset(available)
