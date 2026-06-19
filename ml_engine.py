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
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


REQUIRED_COLUMNS = ["Timestamp", "Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]
MODEL_FEATURES = ["Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]
DIAGNOSTIC_FEATURES = ["Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status", "Hour", "Is_Weekend"]
VALID_OCCUPANCY_STATUSES = {"Class_Hours", "After_Hours", "Vacation", "Event"}
EVENT_OCCUPANCY_STATUS = "Event"
MAX_FLOW_LPM = 500.0
MAX_PRESSURE_PSI = 150.0
WATER_COST_PER_M3 = 0.50
WATER_COST_PER_LITER = WATER_COST_PER_M3 / 1000.0
DENSITY_WATER = 1000
DISCHARGE_COEFF = 0.62
PSI_TO_PASCAL = 6894.76
DAILY_DRINKING_LITERS_PER_STUDENT = 2.5
WATER_TREATMENT_ENERGY_KWH_PER_M3 = 0.45
GRID_EMISSION_KGCO2_PER_KWH = 0.42
LABELS_PATH = Path(__file__).resolve().parent / "training_labels.csv"
LEAK_TYPE_LABELS = ["fixture_leak", "valve_failure", "mainline_break"]


def calculate_financial_loss(lpm):
    """Estimate the hourly financial loss for a given leak rate in L/min."""
    liters_per_hour = max(float(lpm), 0.0) * 60.0
    cubic_meters_per_hour = liters_per_hour / 1000.0
    return round(cubic_meters_per_hour * WATER_COST_PER_M3, 2)


def calculate_carbon_footprint(liters):
    """Estimate the water-related carbon footprint associated with wasted liters."""
    cubic_meters = max(float(liters), 0.0) / 1000.0
    treatment_footprint = cubic_meters * 0.19
    energy_footprint = (cubic_meters * WATER_TREATMENT_ENERGY_KWH_PER_M3) * GRID_EMISSION_KGCO2_PER_KWH
    return round(treatment_footprint + energy_footprint, 2)


def build_reasoning_summary(result, payload):
    """Create a direct reasoning sentence for external UIs."""
    if not result.get("has_leak"):
        return "النظام لم يرصد شذوذاً واضحاً؛ قراءات التدفق والضغط بقيت ضمن خط الأساس المتوقع للفترة الحالية."

    top_row = result.get("top_row")
    if top_row is None:
        return "النظام رصد شذوذاً في البيانات، لكن تفاصيل الإشارة غير كافية لصياغة تفسير كامل."

    status = str(top_row.get("Occupancy_Status", "Unknown"))
    period_label = {
        "Event": "فترة الفعاليات المدرسية",
        "Class_Hours": "فترة الحصص الدراسية",
        "After_Hours": "فترة خارج الدوام",
        "Vacation": "فترة الإجازة",
    }.get(status, f"فترة {status}")
    leak_label = {
        "fixture_leak": "تسريب في أحد التجهيزات",
        "valve_failure": "فشل في الصمام",
        "mainline_break": "كسر في الخط الرئيسي",
    }.get(str(result.get("leak_type", "")), "تسريب محتمل")
    anomaly_pct = float(result.get("Leak_Probability", result.get("confidence", 0.0)))

    return (
        f"النظام رصد شذوذاً بنسبة {anomaly_pct:.0f}% في معدل التدفق خلال {period_label}، "
        f"مما يشير إلى {leak_label} نتيجة عدم تطابق واضح بين التدفق والضغط مقارنة بخط الأساس."
    )


class InsightEngine:
    """Transform raw leak metrics into decision-friendly stories."""

    @staticmethod
    def build_financial_insight(leak_lpm, current_total_liters):
        current_m3_per_hour = max(float(leak_lpm), 0.0) * 60.0 / 1000.0
        current_financial_loss = current_m3_per_hour * WATER_COST_PER_M3
        monthly_financial_loss = current_financial_loss * 24.0 * 30.0
        monthly_water_loss_liters = max(float(current_total_liters), 0.0) * 30.0

        return {
            "current_loss_usd_per_hour": round(current_financial_loss, 2),
            "monthly_loss_usd": round(monthly_financial_loss, 2),
            "current_loss_label": f"${current_financial_loss:.2f}/hour",
            "monthly_loss_label": f"${monthly_financial_loss:,.2f}/month",
            "narrative": (
                f"Current financial loss is approximately ${current_financial_loss:.2f} per hour. "
                f"If ignored for a month, the loss can reach about ${monthly_financial_loss:,.2f}. "
                f"That also corresponds to roughly {monthly_water_loss_liters:,.0f} liters of avoidable water waste."
            ),
        }

    @staticmethod
    def build_environmental_insight(total_liters):
        liters_saved = max(float(total_liters), 0.0)
        m3_saved = liters_saved / 1000.0
        energy_saved_kwh = m3_saved * WATER_TREATMENT_ENERGY_KWH_PER_M3
        treatment_carbon_kg = m3_saved * 0.19
        energy_carbon_kg = energy_saved_kwh * GRID_EMISSION_KGCO2_PER_KWH
        carbon_saved_kg = calculate_carbon_footprint(liters_saved)

        return {
            "liters_saved": round(liters_saved, 1),
            "energy_saved_kwh": round(energy_saved_kwh, 2),
            "carbon_saved_kgco2e": round(carbon_saved_kg, 2),
            "treatment_carbon_kgco2e": round(treatment_carbon_kg, 2),
            "energy_carbon_kgco2e": round(energy_carbon_kg, 2),
            "narrative": (
                f"Fixing this leak preserves about {liters_saved:,.0f} liters. "
                f"That avoids roughly {energy_saved_kwh:.2f} kWh of pumping/treatment energy and "
                f"prevents about {carbon_saved_kg:.2f} kgCO2e of associated emissions "
                f"({treatment_carbon_kg:.2f} from treatment + {energy_carbon_kg:.2f} from grid energy)."
            ),
        }

    @staticmethod
    def build_reasoning_insight(result, payload):
        if not result.get("has_leak"):
            return {
                "headline": "The system stayed within the learned baseline.",
                "narrative": "Flow, pressure, and occupancy remained close to the expected school-day pattern, so the model did not flag a leak.",
                "drivers": [],
            }

        top_row = result.get("top_row")
        feature_importance = result.get("feature_importance", [])
        leak_type = str(result.get("leak_type", "unknown")).replace("_", " ").title()
        confidence = float(result.get("confidence", 0.0))

        status = str(top_row["Occupancy_Status"]) if top_row is not None and "Occupancy_Status" in top_row else "Unknown"
        current_flow = float(top_row["Flow_Rate_LPM"]) if top_row is not None else 0.0
        current_pressure = float(top_row["Avg_Pressure_PSI"]) if top_row is not None else 0.0
        baseline_flow = float(payload.get("flow_profile", {}).get(status, payload.get("overall_flow", current_flow)))
        baseline_pressure = float(payload.get("pressure_profile", {}).get(status, payload.get("overall_pressure", current_pressure)))
        flow_delta_pct = ((current_flow - baseline_flow) / max(baseline_flow, 1e-6)) * 100.0
        pressure_drop_pct = ((baseline_pressure - current_pressure) / max(baseline_pressure, 1e-6)) * 100.0

        driver_bits = []
        if feature_importance:
            driver_bits = [f"{name.replace('numeric__', '').replace('categorical__', '').replace('_', ' ')}" for name, _ in feature_importance[:3]]

        narrative = (
            f"The model is {confidence:.0f}% confident because current flow reached {current_flow:.1f} L/min, "
            f"which is {flow_delta_pct:.0f}% above the learned baseline for {status}, while pressure fell to {current_pressure:.1f} PSI "
            f"({pressure_drop_pct:.0f}% below baseline). {('Top drivers: ' + ', '.join(driver_bits) + '.' if driver_bits else '')}"
        ).strip()

        return {
            "headline": f"{leak_type} pattern detected with a flow/pressure mismatch.",
            "narrative": narrative,
            "drivers": feature_importance[:3],
            "flow_delta_pct": round(flow_delta_pct, 1),
            "pressure_drop_pct": round(pressure_drop_pct, 1),
            "baseline_flow": round(baseline_flow, 1),
            "baseline_pressure": round(baseline_pressure, 1),
            "current_flow": round(current_flow, 1),
            "current_pressure": round(current_pressure, 1),
        }

    @classmethod
    def build_insights(cls, result, payload):
        return {
            "financial": cls.build_financial_insight(result.get("leak_lpm", 0.0), result.get("total_liters", 0.0)),
            "environmental": cls.build_environmental_insight(result.get("total_liters", 0.0)),
            "reasoning": cls.build_reasoning_insight(result, payload),
        }


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


def build_synthetic_training_labels(sample_groups, output_path=LABELS_PATH, rows_per_sample=120):
    """Build a labeled training set from bundled telemetry samples.

    Args:
        sample_groups: Iterable of sample-path iterables used to seed the
            synthetic labeled set.
        output_path: Where to persist the generated CSV file.
        rows_per_sample: Number of synthetic rows to produce per source row.

    Returns:
        A DataFrame with Flow, Pressure, Occupancy, Leak_Type, and Leak_Loss_LPM
        columns.
    """
    frames = []
    rng = np.random.default_rng(42)
    for group in sample_groups:
        sample_path = find_sample_file(group)
        if sample_path is None:
            continue
        base_df = pd.read_csv(sample_path)
        base_df, _ = validate_and_clean_data(base_df, f"seed data from {sample_path.name}")
        base_df = add_time_features(base_df)
        for _, row in base_df.iterrows():
            for _ in range(rows_per_sample):
                leak_type = rng.choice(["no_leak"] + LEAK_TYPE_LABELS, p=[0.46, 0.24, 0.16, 0.14])
                if leak_type == "no_leak":
                    flow_shift = rng.uniform(-1.5, 1.8)
                    pressure_shift = rng.uniform(-1.0, 1.2)
                    loss_lpm = 0.0
                else:
                    leak_scale = {
                        "fixture_leak": rng.uniform(4.0, 18.0),
                        "valve_failure": rng.uniform(14.0, 40.0),
                        "mainline_break": rng.uniform(35.0, 95.0),
                    }[leak_type]
                    flow_shift = leak_scale + rng.normal(0.0, leak_scale * 0.1)
                    pressure_shift = {
                        "fixture_leak": rng.uniform(1.0, 6.0),
                        "valve_failure": rng.uniform(4.0, 12.0),
                        "mainline_break": rng.uniform(10.0, 28.0),
                    }[leak_type]
                    loss_lpm = round(max(flow_shift * rng.uniform(1.05, 1.35), 0.1), 1)
                is_weekend = int(row["Is_Weekend"])
                hour = int(row["Hour"])
                base_flow = float(row["Flow_Rate_LPM"])
                base_pressure = float(row["Avg_Pressure_PSI"])
                label_row = {
                    "Timestamp": row["Timestamp"],
                    "Hour": hour,
                    "Is_Weekend": is_weekend,
                    "Flow_Rate_LPM": round(max(base_flow + flow_shift + rng.normal(0.0, 2.0), 0.1), 1),
                    "Avg_Pressure_PSI": round(max(base_pressure - pressure_shift + rng.normal(0.0, 1.5), 1.0), 1),
                    "Occupancy_Status": row["Occupancy_Status"],
                    "Leak_Type": leak_type,
                    "Leak_Loss_LPM": loss_lpm,
                }
                frames.append(label_row)
    labeled_df = pd.DataFrame(frames)
    if labeled_df.empty:
        raise FileNotFoundError("No sample files were available to build synthetic training labels.")
    labeled_df.to_csv(output_path, index=False)
    return labeled_df


def load_training_labels(sample_groups):
    """Load or synthesize the labeled diagnostics dataset.

    Args:
        sample_groups: Bundled sample path groups used to synthesize labels if
            no explicit labels file exists.

    Returns:
        A DataFrame with diagnostic labels and validation summary stored in attrs.
    """
    if LABELS_PATH.exists():
        labeled_df = pd.read_csv(LABELS_PATH)
    else:
        labeled_df = build_synthetic_training_labels(sample_groups)

    required = REQUIRED_COLUMNS + ["Leak_Type", "Leak_Loss_LPM"]
    missing = [col for col in required if col not in labeled_df.columns]
    if missing:
        raise ValueError(f"training labels are missing required columns: {', '.join(missing)}")

    cleaned_base, summary = validate_and_clean_data(labeled_df[REQUIRED_COLUMNS], "training labels base")
    cleaned_labels = labeled_df.loc[cleaned_base.index, required].copy()
    cleaned_labels["Leak_Type"] = cleaned_labels["Leak_Type"].astype(str)
    cleaned_labels["Leak_Loss_LPM"] = pd.to_numeric(cleaned_labels["Leak_Loss_LPM"], errors="coerce").fillna(0.0)
    cleaned_labels.attrs["validation_summary"] = summary
    return cleaned_labels


def load_training_labels_for_mode(normal_sample_group, event_sample_group=None, event_mode=False):
    """Load labels using normal-only or normal+event samples based on mode.

    Args:
        normal_sample_group: Candidate paths for normal no-leak samples.
        event_sample_group: Candidate paths for event no-leak samples.
        event_mode: When True, include event no-leak samples in training.

    Returns:
        A cleaned labeled DataFrame with mode metadata in attrs.
    """
    sample_groups = [normal_sample_group]
    if event_mode and event_sample_group is not None:
        sample_groups.append(event_sample_group)

    labels = load_training_labels(sample_groups)
    labels.attrs["event_mode"] = bool(event_mode)
    return labels


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


def build_diagnostic_feature_frame(df):
    """Create the feature matrix used by the diagnostic classifier/regressor."""
    enriched = add_time_features(df)
    return enriched[DIAGNOSTIC_FEATURES].copy()


def build_diagnostic_pipeline_classifier():
    """Create the RandomForest classifier used for leak type prediction."""
    return Pipeline([
        ("preprocess", ColumnTransformer([
            ("numeric", "passthrough", ["Flow_Rate_LPM", "Avg_Pressure_PSI", "Hour", "Is_Weekend"]),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Occupancy_Status"]),
        ])),
        ("model", RandomForestClassifier(n_estimators=250, random_state=42, class_weight="balanced")),
    ])


def build_diagnostic_pipeline_regressor():
    """Create the LinearRegression model used for loss estimation."""
    return Pipeline([
        ("preprocess", ColumnTransformer([
            ("numeric", "passthrough", ["Flow_Rate_LPM", "Avg_Pressure_PSI", "Hour", "Is_Weekend"]),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Occupancy_Status"]),
        ])),
        ("model", LinearRegression()),
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


def train_diagnostic_model(df_normal, model_path):
    """Train the diagnostic classifier and regressor from labeled data."""
    training_df, validation_summary = validate_and_clean_data(df_normal, "diagnostic training data")
    training_df = add_time_features(training_df)
    feature_frame = build_diagnostic_feature_frame(training_df)
    leak_type_target = training_df["Leak_Type"].astype(str)
    loss_target = pd.to_numeric(training_df["Leak_Loss_LPM"], errors="coerce").fillna(0.0)

    classifier = build_diagnostic_pipeline_classifier()
    regressor = build_diagnostic_pipeline_regressor()
    classifier.fit(feature_frame, leak_type_target)
    regressor.fit(feature_frame, loss_target)

    payload = {
        "classifier": classifier,
        "regressor": regressor,
        "feature_columns": DIAGNOSTIC_FEATURES,
        "training_fingerprint": build_training_fingerprint(training_df),
        "validation_summary": validation_summary,
        "feature_names": classifier.named_steps["preprocess"].get_feature_names_out().tolist(),
        "classifier_classes": classifier.named_steps["model"].classes_.tolist(),
        "regressor_target_mean": float(loss_target.mean()),
        "diagnostic_mode": True,
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


def ensure_diagnostic_model(df_labeled, model_path):
    """Reuse or retrain the diagnostic classifier/regressor bundle."""
    training_df, _ = validate_and_clean_data(df_labeled, "diagnostic training data")
    training_fingerprint = build_training_fingerprint(training_df)
    path = Path(model_path)

    if path.exists():
        payload = joblib.load(path)
        if payload.get("diagnostic_mode") and payload.get("training_fingerprint") == training_fingerprint:
            return payload, True

    payload = train_diagnostic_model(training_df, model_path)
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


def predict_diagnostic_labels(df_new, model_path, event_mode=False):
    """Predict leak type and loss from the labeled diagnostic model."""
    scored_df, validation_summary = validate_and_clean_data(df_new, "diagnostic inference data")
    payload = load_model_bundle(model_path)
    scored_df = add_time_features(scored_df)
    feature_frame = build_diagnostic_feature_frame(scored_df)
    predicted_type = payload["classifier"].predict(feature_frame)
    predicted_type_proba = payload["classifier"].predict_proba(feature_frame)
    predicted_loss = payload["regressor"].predict(feature_frame)
    class_names = list(payload["classifier_classes"])
    if "no_leak" in class_names:
        no_leak_index = class_names.index("no_leak")
        leak_probability = np.round((1.0 - predicted_type_proba[:, no_leak_index]) * 100, 1)
    else:
        leak_probability = np.round(predicted_type_proba.max(axis=1) * 100, 1)

    scored_df = scored_df.copy()
    scored_df["Predicted_Leak_Type"] = predicted_type
    scored_df["Leak_Type_Confidence"] = np.round(predicted_type_proba.max(axis=1) * 100, 1)
    scored_df["Predicted_Loss_LPM"] = np.round(np.maximum(predicted_loss, 0.0), 1)
    scored_df["Leak_Probability"] = leak_probability
    scored_df["Leak_Flag"] = scored_df["Predicted_Leak_Type"].astype(str).ne("no_leak")

    # When event mode is disabled, require higher confidence for Event rows
    # to reduce false positives from legitimately elevated event-time usage.
    if not event_mode:
        event_mask = scored_df["Occupancy_Status"].eq(EVENT_OCCUPANCY_STATUS)
        low_confidence_event = scored_df["Leak_Probability"] < 80.0
        scored_df.loc[event_mask & low_confidence_event, "Leak_Flag"] = False

    scored_df["Anomaly_Score"] = np.where(scored_df["Leak_Flag"], scored_df["Leak_Probability"], 0.0)
    scored_df.attrs["validation_summary"] = validation_summary
    return scored_df


def evaluate_telemetry(data, model_path, event_mode=False):
    """Summarize leak analysis results from a scored telemetry DataFrame.

    Args:
        data: Raw telemetry DataFrame to analyze.
        model_path: Path to the persisted joblib bundle.

    Returns:
        A metrics dictionary used by the Streamlit UI.
    """
    payload = load_model_bundle(model_path)
    scored = predict_diagnostic_labels(data, model_path, event_mode=event_mode)
    scored["Confidence"] = scored["Leak_Type_Confidence"]
    scored["Loss_LPM"] = scored["Predicted_Loss_LPM"]
    event_rows = int(scored["Occupancy_Status"].eq(EVENT_OCCUPANCY_STATUS).sum())

    anomalies = scored[scored["Leak_Flag"]]
    has_leak = len(anomalies) > 0
    metrics = {
        "has_leak": has_leak,
        "anomalies": anomalies,
        "df": scored,
        "leak_lpm": float(scored["Predicted_Loss_LPM"].max()) if has_leak else 0.0,
        "diameter_mm": 0.0,
        "cost_min": 0.0,
        "total_liters": float(scored["Predicted_Loss_LPM"].sum()) if has_leak else 0.0,
        "metaphor": "No leak detected",
        "students_count": 0,
        "time_parsed": bool(scored["_time_parsed"].iloc[0]),
        "event_mode": bool(event_mode),
        "event_rows": event_rows,
        "validation_summary": scored.attrs.get("validation_summary", {}),
        "max_leak_probability": float(scored["Leak_Probability"].max()) if has_leak else 0.0,
        "leak_type": None,
        "leak_type_confidence": 0.0,
        "feature_importance": [],
    }

    if not has_leak:
        metrics["insights"] = InsightEngine.build_insights(metrics, payload)
        metrics["reasoning_string"] = build_reasoning_summary(metrics, payload)
        metrics["financial_loss"] = {
            "current_loss_usd_per_hour": 0.0,
            "monthly_loss_usd": 0.0,
        }
        metrics["environmental_impact"] = {
            "carbon_footprint_kgco2e": 0.0,
        }
        return metrics

    top_row = anomalies.loc[anomalies["Anomaly_Score"].idxmax()]
    leak_lpm = round(float(top_row["Predicted_Loss_LPM"]), 1)
    leak_type = str(top_row["Predicted_Leak_Type"])
    leak_type_confidence = float(top_row["Leak_Type_Confidence"])

    feature_names = payload["feature_names"]
    importances = payload["classifier"].named_steps["model"].feature_importances_
    feature_importance = sorted(zip(feature_names, importances), key=lambda item: item[1], reverse=True)[:5]

    metrics.update({
        "leak_lpm": leak_lpm,
        "diameter_mm": round(leak_lpm * 0.6, 2),
        "cost_min": round(leak_lpm * WATER_COST_PER_LITER, 2),
        "total_liters": round(anomalies["Predicted_Loss_LPM"].sum(), 1),
        "students_count": int(anomalies["Predicted_Loss_LPM"].sum() / DAILY_DRINKING_LITERS_PER_STUDENT),
        "top_row": top_row,
        "base_flow": float(top_row["Flow_Rate_LPM"]),
        "base_pressure": float(top_row["Avg_Pressure_PSI"]),
        "confidence": leak_type_confidence,
        "deviation_pct": 0.0,
        "pressure_drop_pct": 0.0,
        "leak_type": leak_type,
        "leak_type_confidence": leak_type_confidence,
        "feature_importance": feature_importance,
        "predicted_loss_lpm": leak_lpm,
    })

    metrics["metaphor"] = leak_type.replace("_", " ")
    metrics["insights"] = InsightEngine.build_insights(metrics, payload)
    metrics["reasoning_string"] = build_reasoning_summary(metrics, payload)
    metrics["financial_loss"] = {
        "current_loss_usd_per_hour": calculate_financial_loss(leak_lpm),
        "monthly_loss_usd": round(calculate_financial_loss(leak_lpm) * 24.0 * 30.0, 2),
    }
    metrics["environmental_impact"] = {
        "carbon_footprint_kgco2e": calculate_carbon_footprint(metrics["total_liters"]),
    }

    return metrics