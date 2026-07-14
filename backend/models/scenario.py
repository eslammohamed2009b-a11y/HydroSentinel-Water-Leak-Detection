"""Scenario models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255), unique=True)
    occupancy_mode: Mapped[str] = mapped_column(String(64), default="normal")
    expected_has_leak: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    rows: Mapped[list["ScenarioRow"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")


class ScenarioRow(Base):
    __tablename__ = "scenario_rows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    row_index: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[str] = mapped_column(String(120))
    flow_rate_lpm: Mapped[float] = mapped_column(Float)
    avg_pressure_psi: Mapped[float] = mapped_column(Float)
    occupancy_status: Mapped[str] = mapped_column(String(64))
    scenario: Mapped[Scenario] = relationship(back_populates="rows")