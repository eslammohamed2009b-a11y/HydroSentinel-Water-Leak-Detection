"""Analysis-related models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from backend.database.base import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scenario_selected: Mapped[str] = mapped_column(String(255))
    event_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    has_leak: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    leak_lpm: Mapped[float] = mapped_column(Float, default=0.0)
    total_liters: Mapped[float] = mapped_column(Float, default=0.0)
    payload_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    feedback_items: Mapped[list["AnalysisFeedback"]] = relationship(back_populates="analysis_run", cascade="all, delete-orphan")


class AnalysisFeedback(Base):
    __tablename__ = "analysis_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True)
    analysis_id: Mapped[str] = mapped_column(String(64), index=True)
    feedback: Mapped[str] = mapped_column(String(120))
    predicted_leak: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    top_timestamp: Mapped[str] = mapped_column(String(120), default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    analysis_run: Mapped[AnalysisRun | None] = relationship(back_populates="feedback_items")