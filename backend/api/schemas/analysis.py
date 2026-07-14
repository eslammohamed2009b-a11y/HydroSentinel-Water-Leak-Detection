"""Analysis request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    scenario_selected: str = Field(default="normal.csv")
    event_mode: bool = Field(default=False)


class FeedbackRequest(BaseModel):
    verdict: str = Field(min_length=2, max_length=120)


class ScenarioSummary(BaseModel):
    slug: str
    label: str
    filename: str
    description: str
    occupancy_mode: str | None = None
    expected_has_leak: bool | None = None


class AnalysisResponse(BaseModel):
    analysis_id: str | None = None
    has_leak: bool
    leak_lpm: float
    total_liters: float
    leak_type: str | None = None
    confidence: float
    event_mode: bool
    event_rows: int
    source_mode: str
    scenario_selected: str | None = None
    validation_summary: dict[str, Any]
    reasoning_string: str
    financial_loss: dict[str, Any]
    environmental_impact: dict[str, Any]
    insights: dict[str, Any]
    anomalies: list[dict[str, Any]]
    telemetry_points: list[dict[str, Any]]


class AnalysisHistoryItem(BaseModel):
    analysis_id: str
    scenario_selected: str
    event_mode: bool
    has_leak: bool
    confidence: float
    leak_lpm: float
    total_liters: float
    created_at: str


class FeedbackResponse(BaseModel):
    analysis_id: str
    feedback: str
    confidence: float
    predicted_leak: bool
