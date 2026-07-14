"""Database bootstrap and seed helpers."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.security import get_password_hash
from backend.core.config import settings
from backend.database.base import Base
from backend.database.session import engine
from backend.models.scenario import Scenario
from backend.models.scenario import ScenarioRow
from backend.models.user import User
from backend.services.analysis_service import SCENARIO_SEED_METADATA


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def seed_default_data(session: Session) -> None:
    _seed_scenarios(session)
    _seed_admin_user(session)


def _seed_scenarios(session: Session) -> None:
    existing = session.scalar(select(Scenario.id).limit(1))
    if existing is not None:
        return

    for filename, metadata in SCENARIO_SEED_METADATA.items():
        source_path = settings.resolved_data_root / filename
        if not source_path.exists():
            continue

        frame = pd.read_csv(source_path)
        scenario = Scenario(
            slug=filename.replace(".csv", ""),
            label=metadata["label"],
            description=metadata["description"],
            file_name=filename,
            occupancy_mode=metadata["occupancy_mode"],
            expected_has_leak=bool(metadata["expected_has_leak"]),
        )
        session.add(scenario)
        session.flush()

        for row_index, row in frame.iterrows():
            session.add(
                ScenarioRow(
                    scenario_id=scenario.id,
                    row_index=int(row_index),
                    timestamp=str(row["Timestamp"]),
                    flow_rate_lpm=float(row["Flow_Rate_LPM"]),
                    avg_pressure_psi=float(row["Avg_Pressure_PSI"]),
                    occupancy_status=str(row["Occupancy_Status"]),
                )
            )

    session.commit()


def _seed_admin_user(session: Session) -> None:
    if not settings.bootstrap_admin_email:
        return

    existing_user = session.scalar(select(User).where(User.email == settings.bootstrap_admin_email))
    if existing_user is not None:
        return

    session.add(
        User(
            email=settings.bootstrap_admin_email,
            full_name=settings.bootstrap_admin_name,
            password_hash=get_password_hash(settings.bootstrap_admin_password),
            role="admin",
            is_active=True,
            is_superuser=True,
        )
    )
    session.commit()
