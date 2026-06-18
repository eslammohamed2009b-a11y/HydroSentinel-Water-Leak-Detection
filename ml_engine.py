"""HydroSentinel ML engine.

This module contains the production-facing machine-learning utilities used by
the Streamlit UI. It handles data validation, model persistence, training, and
leak scoring so the UI layer can stay focused on interaction and reporting.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


REQUIRED_COLUMNS = ["Timestamp", "Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]
MODEL_FEATURES = ["Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]
VALID_OCCUPANCY_STATUSES = {"Class_Hours", "After_Hours", "Vacation", "Event"}
MAX_FLOW_LPM = 500.0
MAX_PRESSURE_PSI = 150.0
WATER_COST_PER_LITER = 0.007
DENSITY_WATER = 1000
DISCHARGE_COEFF = 0.62
PSI_TO_PASCAL = 6894.76
DAILY_DRINKING_LITERS_PER_STUDENT = 2.5


def find_sample_file(filename_options):
    """Return the first existing sample path from a list of candidate paths.

    Args:
        filename_options: Iterable of candidate file paths.

    Returns:
        A resolved Path if one of the candidates exists, otherwise None.
    """
    for filename in filename_options:
        path = Path(filename)
        if path.exists():
            return path
    return None


def add_time_features(df):
    """Add basic time-derived features used for reporting and context.

    Args:
        df: Input telemetry DataFrame with a Timestamp column.

    Returns:
        A copy of the DataFrame enriched with Hour, Is_Weekend, and
        _time_parsed columns.
    """
    enriched = df.copy()
    try:
        dt = pd.to_datetime(enriched["Timestamp"])
        enriched["Hour"] = dt.dt.hour
        enriched["Is_Weekend"] = (dt.dt.dayofweek >= 5).astype(int)
        enriched["_time_parsed"] = True
    except Exception:
        enriched["Hour"] = 0
        enriched["Is_Weekend"] = 0
        enriched["_time_parsed"] = False
    return enriched


def validate_required_columns(df):
    """Validate that all required HydroSentinel columns exist.

    Args:
        df: DataFrame to validate.

    Raises:
        ValueError: If one or more required columns are missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def validate_and_clean_data(df, dataset_name):
    """Remove invalid telemetry rows and return a clean DataFrame.

    Args:
        df: Raw input DataFrame.
        dataset_name: Human-readable dataset label for error messages.

    Returns:
        A tuple of (cleaned_dataframe, validation_summary_dict).

    Raises:
        ValueError: If validation removes every row.
    """
    validate_required_columns(df)
    cleaned = df.copy()
    cleaned["Timestamp"] = cleaned["Timestamp"].astype(str).str.strip()
    cleaned["Flow_Rate_LPM"] = pd.to_numeric(cleaned["Flow_Rate_LPM"], errors="coerce")
    cleaned["Avg_Pressure_PSI"] = pd.to_numeric(cleaned["Avg_Pressure_PSI"], errors="coerce")
    cleaned["Occupancy_Status"] = cleaned["Occupancy_Status"].astype(str).str.strip()

    invalid_mask = (
        cleaned["Timestamp"].eq("")
        | cleaned["Flow_Rate_LPM"].isna()
        | cleaned["Avg_Pressure_PSI"].isna()
        | (cleaned["Flow_Rate_LPM"] < 0)
        | (cleaned["Flow_Rate_LPM"] > MAX_FLOW_LPM)
        | (cleaned["Avg_Pressure_PSI"] <= 0)
        | (cleaned["Avg_Pressure_PSI"] > MAX_PRESSURE_PSI)
        | (~cleaned["Occupancy_Status"].isin(VALID_OCCUPANCY_STATUSES))
    )

    invalid_rows = int(invalid_mask.sum())
    cleaned = cleaned.loc[~invalid_mask].copy()
    if cleaned.empty:
        raise ValueError(
            f"{dataset_name} has no usable rows after validation. Check timestamps, occupancy labels, and sensor values."
        )

    summary = {
        "dataset_name": dataset_name,
        "total_rows": int(len(df)),
        "invalid_rows": invalid_rows,
        "valid_rows": int(len(cleaned)),
    }
    cleaned.attrs["validation_summary"] = summary
    return cleaned, summary


def load_default_training_data(sample_groups):
    """Load bundled no-leak training data from one or more sample groups.

    Args:
        sample_groups: Iterable of path-option iterables, such as normal-day and
            event-day sample path lists.

    Returns:
        A concatenated DataFrame of all discovered sample files, or None if no
        samples are available.
    """
    frames = []
    for group in sample_groups:
        sample_path = find_sample_file(group)
        if sample_path is not None:
            frames.append(pd.read_csv(sample_path))

    if not frames:
        return None

    return pd.concat(frames, ignore_index=True)


def build_training_fingerprint(df):
    """Build a stable fingerprint for a cleaned training dataset.

    Args:
        df: Cleaned training DataFrame.

    Returns:
        A short SHA-256 fingerprint string derived from required columns.
    """
    canonical = df[REQUIRED_COLUMNS].copy()
    canonical["Timestamp"] = canonical["Timestamp"].astype(str)
    return hashlib.sha256(canonical.to_csv(index=False).encode("utf-8")).hexdigest()


def build_feature_pipeline():
    """Create the IsolationForest preprocessing and model pipeline.

    Returns:
        A scikit-learn Pipeline that encodes occupancy context and fits the
        anomaly-detection model.
    """
    return Pipeline([
        ("preprocess", ColumnTransformer([
            ("numeric", "passthrough", ["Flow_Rate_LPM", "Avg_Pressure_PSI"]),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Occupancy_Status"]),
        ])),
        ("model", IsolationForest(contamination=0.01, random_state=42)),
    ])


def load_model_bundle(model_path):
    """Load a persisted HydroSentinel model bundle from disk.

    Args:
        model_path: Path to the joblib file.

    Returns:
        The deserialized model payload dictionary.

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)


def train_model(df_normal, model_path):
    """Train and persist the IsolationForest model using clean no-leak data.

    Args:
        df_normal: Training DataFrame containing normal and optionally event-day
            no-leak telemetry.
        model_path: Destination path for the persisted model bundle.

    Returns:
        A payload dictionary containing the trained pipeline and reference
        statistics.
    """
    training_df, validation_summary = validate_and_clean_data(df_normal, "training data")
    training_df = add_time_features(training_df)
    feature_frame = training_df[MODEL_FEATURES].copy()
    pipeline = build_feature_pipeline()
    pipeline.fit(feature_frame)

    training_scores = -pipeline.score_samples(feature_frame)
    profile = training_df.groupby("Occupancy_Status")[["Flow_Rate_LPM", "Avg_Pressure_PSI"]].median()
    payload = {
        "pipeline": pipeline,
        "feature_columns": MODEL_FEATURES,
        "training_fingerprint": build_training_fingerprint(training_df),
        "anomaly_threshold": float(np.quantile(training_scores, 0.98)),
        "score_floor": float(np.quantile(training_scores, 0.05)),
        "score_ceiling": float(np.quantile(training_scores, 0.95)),
        "flow_profile": profile["Flow_Rate_LPM"].to_dict(),
        "pressure_profile": profile["Avg_Pressure_PSI"].to_dict(),
        "overall_flow": float(training_df["Flow_Rate_LPM"].median()),
        "overall_pressure": float(training_df["Avg_Pressure_PSI"].median()),
        "validation_summary": validation_summary,
    }
    joblib.dump(payload, model_path)
    return payload


def ensure_model(df_normal, model_path):
    """Reuse an existing model when its training fingerprint still matches.

    Args:
        df_normal: Training DataFrame used to verify or rebuild the model.
        model_path: Path to the persisted joblib bundle.

    Returns:
        A tuple of (model_payload, reused_existing_model_boolean).
    """
    cleaned_training_df, _ = validate_and_clean_data(df_normal, "training data")
    training_fingerprint = build_training_fingerprint(cleaned_training_df)
    path = Path(model_path)

    if path.exists():
        payload = joblib.load(path)
        if payload.get("training_fingerprint") == training_fingerprint:
            return payload, True

    payload = train_model(cleaned_training_df, model_path)
    return payload, False


def predict_leak(df_new, model_path):
    """Score new telemetry rows for anomaly strength and leak probability.

    Args:
        df_new: DataFrame of new telemetry rows to score.
        model_path: Path to the persisted joblib bundle.

    Returns:
        A scored DataFrame with anomaly score, leak probability, and leak flag.
    """
    scored_df, validation_summary = validate_and_clean_data(df_new, "analysis data")
    payload = load_model_bundle(model_path)
    scored_df = add_time_features(scored_df)
    feature_frame = scored_df[payload["feature_columns"]].copy()
    anomaly_score = -payload["pipeline"].score_samples(feature_frame)
    score_span = np.maximum(payload["score_ceiling"] - payload["score_floor"], 1e-6)
    leak_probability = np.clip((anomaly_score - payload["score_floor"]) / score_span, 0.0, 1.0) * 100

    scored_df["Anomaly_Score"] = anomaly_score.round(4)
    scored_df["Leak_Probability"] = leak_probability.round(1)
    scored_df["Leak_Flag"] = anomaly_score >= payload["anomaly_threshold"]
    scored_df.attrs["validation_summary"] = validation_summary
    return scored_df


def evaluate_telemetry(data, model_path):
    """Summarize leak analysis results from a scored telemetry DataFrame.

    Args:
        data: Raw telemetry DataFrame to analyze.
        model_path: Path to the persisted joblib bundle.

    Returns:
        A metrics dictionary used by the Streamlit UI.
    """
    payload = load_model_bundle(model_path)
    scored = predict_leak(data, model_path)
    scored["Baseline_Flow"] = scored["Occupancy_Status"].map(payload["flow_profile"]).fillna(payload["overall_flow"])
    scored["Baseline_Pressure"] = scored["Occupancy_Status"].map(payload["pressure_profile"]).fillna(payload["overall_pressure"])

    flow_ratio = scored["Flow_Rate_LPM"] / scored["Baseline_Flow"].replace(0, np.nan)
    pressure_drop_ratio = ((scored["Baseline_Pressure"] - scored["Avg_Pressure_PSI"]) / scored["Baseline_Pressure"].replace(0, np.nan)).clip(lower=0)
    scored["Confidence"] = scored["Leak_Probability"]
    scored["Pressure_Drop_Pct"] = (pressure_drop_ratio.fillna(0) * 100).round(1)
    scored["Deviation_Pct"] = ((flow_ratio.replace([np.inf, -np.inf], np.nan).fillna(1.0) - 1.0) * 100).round(1)

    anomalies = scored[scored["Leak_Flag"]]
    has_leak = len(anomalies) > 0
    metrics = {
        "has_leak": has_leak,
        "anomalies": anomalies,
        "df": scored,
        "leak_lpm": 0.0,
        "diameter_mm": 0.0,
        "cost_min": 0.0,
        "total_liters": 0.0,
        "metaphor": "No leak detected",
        "students_count": 0,
        "time_parsed": bool(scored["_time_parsed"].iloc[0]),
        "validation_summary": scored.attrs.get("validation_summary", {}),
        "max_leak_probability": float(scored["Leak_Probability"].max()),
    }

    if not has_leak:
        return metrics

    top_row = anomalies.loc[anomalies["Anomaly_Score"].idxmax()]
    max_anomaly = top_row["Flow_Rate_LPM"]
    baseline_flow_for_row = top_row["Baseline_Flow"]
    baseline_pressure_for_row = top_row["Baseline_Pressure"]
    leak_lpm = round(np.maximum(max_anomaly - baseline_flow_for_row, max_anomaly * 0.25), 1)

    flow_m3_s = (leak_lpm / 1000) / 60
    press_pascal = max(top_row["Avg_Pressure_PSI"] * PSI_TO_PASCAL, 1.0)
    velocity = np.sqrt((2 * press_pascal) / DENSITY_WATER)
    area_m2 = flow_m3_s / (DISCHARGE_COEFF * max(velocity, 0.01))
    diameter_mm = round((2 * np.sqrt(area_m2 / np.pi)) * 1000, 2)

    metrics.update({
        "leak_lpm": leak_lpm,
        "diameter_mm": diameter_mm,
        "cost_min": round(leak_lpm * WATER_COST_PER_LITER, 2),
        "total_liters": round(anomalies["Flow_Rate_LPM"].sum(), 1),
        "students_count": int(anomalies["Flow_Rate_LPM"].sum() / DAILY_DRINKING_LITERS_PER_STUDENT),
        "top_row": top_row,
        "base_flow": round(baseline_flow_for_row, 1),
        "base_pressure": round(baseline_pressure_for_row, 1),
        "confidence": float(top_row["Confidence"]),
        "deviation_pct": float(top_row["Deviation_Pct"]),
        "pressure_drop_pct": float(top_row["Pressure_Drop_Pct"]),
    })

    if leak_lpm < 12:
        metrics["metaphor"] = "a faucet left fully running"
    elif leak_lpm <= 35:
        metrics["metaphor"] = "a toilet valve stuck open and constantly refilling"
    else:
        metrics["metaphor"] = "a broken pipe releasing water under pressure"

    return metrics