"""Analysis orchestration services for HydroSentinel."""

from __future__ import annotations

import hashlib
from threading import RLock
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.ai.ml_engine import build_synthetic_training_labels_from_frames
from backend.ai.ml_engine import ensure_diagnostic_model
from backend.ai.ml_engine import evaluate_telemetry
from backend.ai.ml_engine import validate_and_clean_data
from backend.core.config import settings
from backend.models.analysis import AnalysisFeedback
from backend.models.analysis import AnalysisRun
from backend.models.scenario import Scenario
from backend.models.scenario import ScenarioRow


SCENARIO_SEED_METADATA = {
    "normal.csv": {
        "label": "Scenario A - Baseline Normal Day",
        "description": "Baseline occupied building scenario without a leak.",
        "occupancy_mode": "normal",
        "expected_has_leak": False,
    },
    "normal_leak.csv": {
        "label": "Scenario B - Normal Day + Leak",
        "description": "Occupied building scenario with injected leak behavior.",
        "occupancy_mode": "normal",
        "expected_has_leak": True,
    },
    "event.csv": {
        "label": "Scenario C - Event Day (No Leak)",
        "description": "Legitimate high-activity demand without a leak.",
        "occupancy_mode": "event",
        "expected_has_leak": False,
    },
    "event_leak.csv": {
        "label": "Scenario D - Event Day + Leak",
        "description": "High-activity demand with injected leak behavior.",
        "occupancy_mode": "event",
        "expected_has_leak": True,
    },
}

_training_cache: dict[bool, tuple[str, pd.DataFrame, dict[str, Any]]] = {}
_diagnostic_model_cache: dict[bool, str] = {}
_training_cache_lock = RLock()


def build_analysis_id(df: pd.DataFrame) -> str:
    canonical = df[["Timestamp", "Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]].copy()
    canonical["Timestamp"] = canonical["Timestamp"].astype(str)
    return hashlib.sha256(canonical.to_csv(index=False).encode("utf-8")).hexdigest()[:16]


def _scenario_frame_from_rows(rows: list[ScenarioRow]) -> pd.DataFrame:
    ordered_rows = sorted(rows, key=lambda row: row.row_index)
    return pd.DataFrame(
        [
            {
                "Timestamp": row.timestamp,
                "Flow_Rate_LPM": row.flow_rate_lpm,
                "Avg_Pressure_PSI": row.avg_pressure_psi,
                "Occupancy_Status": row.occupancy_status,
            }
            for row in ordered_rows
        ]
    )


def _get_scenario(session: Session, scenario_selected: str) -> Scenario:
    scenario = session.scalar(select(Scenario).where(Scenario.file_name == scenario_selected))
    if scenario is None:
        raise ValueError(f"Unknown scenario selected: {scenario_selected}")
    return scenario


def load_target_dataframe(session: Session, scenario_selected: str) -> tuple[pd.DataFrame, dict[str, Any], Scenario]:
    scenario = _get_scenario(session, scenario_selected)
    raw_df = _scenario_frame_from_rows(scenario.rows)
    cleaned_df, summary = validate_and_clean_data(raw_df, f"analysis data ({scenario.file_name})")
    return cleaned_df, summary, scenario


def load_training_dataframe(session: Session, event_mode: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    scenarios = session.scalars(select(Scenario)).all()
    training_frames = []
    for scenario in scenarios:
        if scenario.expected_has_leak:
            continue
        if scenario.occupancy_mode == "event" and not event_mode:
            continue
        training_frames.append(_scenario_frame_from_rows(scenario.rows))

    source_fingerprint = hashlib.sha256(
        "".join(frame.to_csv(index=False) for frame in training_frames).encode("utf-8")
    ).hexdigest()
    with _training_cache_lock:
        cached = _training_cache.get(event_mode)
        if cached is not None and cached[0] == source_fingerprint:
            return cached[1], cached[2]

        training_df = build_synthetic_training_labels_from_frames(training_frames)
        training_df.attrs["source_fingerprint"] = source_fingerprint
        summary = training_df.attrs.get("validation_summary", {})
        _training_cache[event_mode] = (source_fingerprint, training_df, summary)
        return training_df, summary


def serialize_analysis_result(result: dict[str, Any]) -> dict[str, Any]:
    insights = result.get("insights", {}) or {}
    financial = result.get("financial_loss", {}) or {}
    environmental = result.get("environmental_impact", {}) or {}
    anomalies_df = result.get("anomalies")
    telemetry_df = result.get("df")

    anomalies = []
    if isinstance(anomalies_df, pd.DataFrame) and not anomalies_df.empty:
        anomaly_columns = [
            "Timestamp",
            "Flow_Rate_LPM",
            "Avg_Pressure_PSI",
            "Occupancy_Status",
            "Predicted_Leak_Type",
            "Predicted_Loss_LPM",
            "Leak_Probability",
        ]
        available_columns = [column for column in anomaly_columns if column in anomalies_df.columns]
        anomalies = anomalies_df[available_columns].to_dict(orient="records")

    telemetry_points = []
    if isinstance(telemetry_df, pd.DataFrame) and not telemetry_df.empty:
        telemetry_columns = [
            "Timestamp",
            "Flow_Rate_LPM",
            "Avg_Pressure_PSI",
            "Occupancy_Status",
            "Leak_Probability",
            "Leak_Flag",
        ]
        available_columns = [column for column in telemetry_columns if column in telemetry_df.columns]
        telemetry_points = telemetry_df[available_columns].to_dict(orient="records")

    return {
        "analysis_id": result.get("analysis_id"),
        "has_leak": bool(result.get("has_leak", False)),
        "leak_lpm": float(result.get("leak_lpm", 0.0)),
        "total_liters": float(result.get("total_liters", 0.0)),
        "leak_type": result.get("leak_type"),
        "confidence": float(result.get("confidence", 0.0)),
        "event_mode": bool(result.get("event_mode", False)),
        "event_rows": int(result.get("event_rows", 0)),
        "source_mode": result.get("source_mode", "PostgreSQL Seeded Scenarios"),
        "limitation_note": "Synthetic/simulated scenario result only; not validated on physical building or facility infrastructure. Human review is required.",
        "scenario_selected": result.get("scenario_selected"),
        "validation_summary": result.get("validation_summary", {}),
        "reasoning_string": result.get("reasoning_string") or insights.get("reasoning", {}).get("reasoning_string", ""),
        "financial_loss": {
            "current_loss_usd_per_hour": float(financial.get("current_loss_usd_per_hour", 0.0)),
            "monthly_loss_usd": float(financial.get("monthly_loss_usd", 0.0)),
            "current_loss_label": insights.get("financial", {}).get("current_loss_label", "$0.00/hour"),
            "monthly_loss_label": insights.get("financial", {}).get("monthly_loss_label", "$0.00/month"),
            "narrative": insights.get("financial", {}).get("narrative", ""),
        },
        "environmental_impact": {
            "carbon_footprint_kgco2e": float(environmental.get("carbon_footprint_kgco2e", 0.0)),
            "liters_saved": float(insights.get("environmental", {}).get("liters_saved", result.get("total_liters", 0.0))),
            "energy_saved_kwh": float(insights.get("environmental", {}).get("energy_saved_kwh", 0.0)),
            "narrative": insights.get("environmental", {}).get("narrative", ""),
        },
        "insights": insights,
        "anomalies": anomalies,
        "telemetry_points": telemetry_points,
    }


def _persist_analysis(session: Session, result: dict[str, Any], owner_user_id: int) -> AnalysisRun:
    payload = serialize_analysis_result(result)
    existing = session.scalar(
        select(AnalysisRun).where(
            AnalysisRun.analysis_id == str(result["analysis_id"]),
            AnalysisRun.owner_user_id == owner_user_id,
        )
    )
    if existing is not None:
        existing.payload_json = payload
        existing.confidence = float(result.get("confidence", 0.0))
        existing.leak_lpm = float(result.get("leak_lpm", 0.0))
        existing.total_liters = float(result.get("total_liters", 0.0))
        existing.has_leak = bool(result.get("has_leak", False))
        existing.event_mode = bool(result.get("event_mode", False))
        existing.scenario_selected = str(result.get("scenario_selected", existing.scenario_selected))
        session.commit()
        session.refresh(existing)
        return existing

    analysis_run = AnalysisRun(
        analysis_id=str(result["analysis_id"]),
        scenario_selected=str(result["scenario_selected"]),
        event_mode=bool(result["event_mode"]),
        has_leak=bool(result["has_leak"]),
        confidence=float(result.get("confidence", 0.0)),
        leak_lpm=float(result.get("leak_lpm", 0.0)),
        total_liters=float(result.get("total_liters", 0.0)),
        payload_json=payload,
        owner_user_id=owner_user_id,
    )
    session.add(analysis_run)
    session.commit()
    session.refresh(analysis_run)
    return analysis_run


def list_scenarios(session: Session) -> list[dict[str, Any]]:
    scenarios = session.scalars(select(Scenario).order_by(Scenario.id.asc())).all()
    return [
        {
            "slug": scenario.slug,
            "label": scenario.label,
            "filename": scenario.file_name,
            "description": scenario.description,
            "occupancy_mode": scenario.occupancy_mode,
            "expected_has_leak": scenario.expected_has_leak,
        }
        for scenario in scenarios
    ]


def get_analysis_history(session: Session, owner_user_id: int) -> list[AnalysisRun]:
    return session.scalars(
        select(AnalysisRun)
        .where(AnalysisRun.owner_user_id == owner_user_id)
        .order_by(AnalysisRun.created_at.desc())
    ).all()


def get_analysis_by_public_id(session: Session, analysis_id: str, owner_user_id: int) -> AnalysisRun | None:
    return session.scalar(
        select(AnalysisRun).where(
            AnalysisRun.analysis_id == analysis_id,
            AnalysisRun.owner_user_id == owner_user_id,
        )
    )


def create_feedback(session: Session, analysis_id: str, verdict: str, owner_user_id: int) -> AnalysisFeedback:
    analysis_run = get_analysis_by_public_id(session, analysis_id, owner_user_id)
    if analysis_run is None:
        raise ValueError(f"Analysis not found: {analysis_id}")

    payload = analysis_run.payload_json
    anomalies = payload.get("anomalies", [])
    top_timestamp = str(anomalies[0].get("Timestamp", "")) if anomalies else ""

    feedback = AnalysisFeedback(
        analysis_run_id=analysis_run.id,
        analysis_id=analysis_run.analysis_id,
        feedback=verdict,
        predicted_leak=bool(analysis_run.has_leak),
        confidence=float(analysis_run.confidence),
        top_timestamp=top_timestamp,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def run_analysis(session: Session, scenario_selected: str, event_mode: bool, owner_user_id: int) -> dict[str, Any]:
    training_df, training_summary = load_training_dataframe(session, event_mode)
    target_df, target_summary, scenario = load_target_dataframe(session, scenario_selected)
    source_fingerprint = str(training_df.attrs.get("source_fingerprint", ""))
    with _training_cache_lock:
        if _diagnostic_model_cache.get(event_mode) == source_fingerprint:
            model_reused = True
        else:
            _, model_reused = ensure_diagnostic_model(training_df, settings.resolved_model_path)
            _diagnostic_model_cache[event_mode] = source_fingerprint
    result = evaluate_telemetry(target_df, settings.resolved_model_path, event_mode=event_mode)
    # Scenario content is deterministic, but persisted runs must remain private
    # to the authenticated user who created them.
    analysis_id = hashlib.sha256(f"{owner_user_id}:{build_analysis_id(target_df)}".encode("utf-8")).hexdigest()[:16]
    result["analysis_id"] = analysis_id
    result["model_reused"] = model_reused
    result["source_mode"] = "PostgreSQL Seeded Scenarios"
    result["scenario_selected"] = scenario.file_name
    result["event_mode"] = event_mode
    result["training_summary"] = training_summary
    result["target_summary"] = target_summary
    _persist_analysis(session, result, owner_user_id)
    return result
