from __future__ import annotations

import json
import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from ml_engine import (
    DAILY_DRINKING_LITERS_PER_STUDENT,
    WATER_COST_PER_LITER,
    ensure_diagnostic_model,
    evaluate_telemetry,
    load_training_labels_for_mode,
    validate_and_clean_data,
)


st.set_page_config(
    page_title="HydroSentinel — Water Infrastructure Decision Support for Schools",
    page_icon="💧",
    layout="wide",
)


APP_DIR = CURRENT_DIR
SAMPLE_FILES = {
    "normal": [APP_DIR / "normal.csv", APP_DIR / "example_normal_day_2026-10-05.csv"],
    "event": [APP_DIR / "event.csv"],
}
MODEL_PATH = APP_DIR / "hydrosentinel_isolation_forest.joblib"
FEEDBACK_PATH = APP_DIR / "feedback.csv"
LOGS_PATH = APP_DIR / "logs.csv"


def init_state() -> None:
    defaults = {
        "view_mode": "Operational",
        "event_mode": False,
        "source_mode": "Upload CSV",
        "analysis_requested": False,
        "analysis_result": None,
        "analysis_error": None,
        "uploaded_file_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

        :root {
            --bg: #f8f9ff;
            --panel: #ffffff;
            --ink: #121c28;
            --ink-soft: #414750;
            --outline: #c1c7d2;
            --primary: #004275;
            --primary-2: #005a9c;
            --teal: #006a61;
            --teal-soft: #e3f0ec;
            --amber: #d97706;
            --amber-soft: #fcf1de;
            --red: #dc2626;
            --red-soft: #ffdad6;
        }

        html, body, .main, [data-testid="stAppViewContainer"] {
            background: var(--bg);
            color: var(--ink);
            font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        }

        [data-testid="stHeader"], #MainMenu, footer { display: none; }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid rgba(193,199,210,0.45);
        }

        [data-testid="stSidebar"] * { color: var(--ink); }

        [data-testid="stSidebar"] .stButton > button {
            width: 100%; background: var(--primary); color: #fff; border-radius: 12px;
            border: 1px solid rgba(0,66,117,0.2); padding: 0.85rem 1rem; font-weight: 700;
        }

        [data-testid="stSidebar"] .stButton > button:hover { background: var(--primary-2); }

        .brand { margin-bottom: 1rem; }
        .brand h1 {
            font-size: 2rem; line-height: 1.0; font-weight: 800; color: var(--primary);
            letter-spacing: -0.04em; margin: 0;
        }
        .brand p { margin: 0.5rem 0 0; color: var(--ink-soft); font-size: 0.98rem; }

        .sidebar-section-title {
            font-size: 0.72rem; letter-spacing: 0.11em; text-transform: uppercase;
            color: var(--ink-soft); font-weight: 800; margin: 1.25rem 0 0.55rem;
        }

        .sidebar-card {
            border: 1px solid rgba(193,199,210,0.7); border-radius: 14px; padding: 0.9rem;
            background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
        }
        .sidebar-card.event-on { border-left: 4px solid var(--teal); background: #f4fbf9; }
        .sidebar-card.event-off { border-left: 4px solid var(--outline); background: #fafbfd; }

        .sidebar-chip {
            display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.22rem 0.7rem;
            border-radius: 999px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
            letter-spacing: 0.07em;
        }
        .chip-primary { background: #dbeafe; color: var(--primary); }
        .chip-success { background: var(--teal-soft); color: var(--teal); }
        .chip-warning { background: var(--amber-soft); color: var(--amber); }
        .chip-danger { background: var(--red-soft); color: var(--red); }
        .chip-muted { background: #edf2f7; color: #5b6471; }

        .hero-title {
            font-size: 2.2rem; line-height: 1.05; font-weight: 800; color: var(--primary);
            letter-spacing: -0.04em; margin-bottom: 0.35rem;
        }
        .hero-subtitle {
            color: var(--ink-soft); font-size: 1rem; line-height: 1.55; margin-bottom: 1rem;
        }

        .switcher {
            background: #eef3fb; padding: 0.35rem; border-radius: 14px; display: inline-flex;
            border: 1px solid rgba(193,199,210,0.55);
        }

        .banner-critical, .banner-safe {
            border-radius: 18px; padding: 1rem 1.15rem; margin-bottom: 1.15rem; display: flex;
            align-items: center; justify-content: space-between; gap: 1rem;
        }
        .banner-critical { background: var(--red); color: #fff; }
        .banner-safe { background: var(--teal); color: #fff; }
        .banner-title { font-size: 1.15rem; font-weight: 800; margin: 0; }
        .banner-copy { margin: 0.15rem 0 0; opacity: 0.96; line-height: 1.45; }
        .banner-action {
            background: rgba(255,255,255,0.16); color: #fff; border: 1px solid rgba(255,255,255,0.26);
            border-radius: 12px; padding: 0.7rem 1rem; font-weight: 800; white-space: nowrap;
        }

        .stepper {
            display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.9rem;
            align-items: center; margin: 1rem 0 1.15rem;
        }
        .step { display: flex; align-items: center; gap: 0.85rem; min-height: 72px; }
        .step-badge {
            width: 52px; height: 52px; border-radius: 999px; display: flex; align-items: center;
            justify-content: center; font-weight: 800; font-size: 1.05rem; color: var(--primary);
            background: #dbeafe;
            border: 2px solid #c7d7ef;
            box-shadow: 0 0 0 4px rgba(0,66,117,0.04);
        }
        .step.active .step-badge { background: var(--primary-2); color: #fff; }
        .step .meta {
            margin: 0; color: var(--ink-soft); text-transform: uppercase; letter-spacing: 0.08em;
            font-size: 0.7rem; font-weight: 800;
        }
        .step .label { margin: 0.1rem 0 0; font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); }
        .step.dimmed { opacity: 0.9; }

        .step.dimmed .step-badge {
            opacity: 1;
            background: #eef4ff;
            color: var(--primary);
        }

        .kpi-grid {
            display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 1rem; margin-bottom: 1rem;
        }
        .kpi-card {
            background: var(--panel); border: 1px solid rgba(193,199,210,0.8); border-radius: 18px;
            padding: 1.1rem 1.1rem 1rem; min-height: 148px; display: flex; flex-direction: column; justify-content: space-between;
        }
        .kpi-card .title {
            font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.09em;
            color: var(--ink-soft); margin-bottom: 0.6rem;
        }
        .kpi-card .value {
            font-size: 2rem; font-weight: 800; line-height: 1.04; color: var(--primary); letter-spacing: -0.04em;
        }
        .kpi-card .value.small { font-size: 1.45rem; }
        .kpi-card .foot { margin-top: 0.55rem; font-size: 0.82rem; color: var(--ink-soft); }
        .accent-critical { border-left: 4px solid var(--red); }
        .accent-warning { border-left: 4px solid var(--amber); }
        .accent-ok { border-left: 4px solid var(--teal); }
        .accent-info { border-left: 4px solid var(--primary); }

        .panel {
            background: var(--panel); border: 1px solid rgba(193,199,210,0.8); border-radius: 18px; padding: 1rem;
        }
        .panel h3 { margin: 0 0 0.2rem; font-size: 1.15rem; font-weight: 800; color: var(--ink); }
        .panel .sub { margin: 0 0 0.9rem; color: var(--ink-soft); font-size: 0.92rem; }

        .why-box {
            background: linear-gradient(180deg, #eef6ff 0%, #f8fbff 100%);
            border-left: 4px solid var(--primary); border-radius: 18px; padding: 1rem; height: 100%;
        }
        .note-box {
            background: #dff6f1; border: 1px solid rgba(0,106,97,0.2); border-radius: 18px; padding: 1rem; height: 100%;
        }
        .why-box .title, .note-box .title, .gov-box .title {
            margin: 0 0 0.7rem; font-size: 0.78rem; font-weight: 800; text-transform: uppercase;
            letter-spacing: 0.09em; color: var(--ink-soft);
        }
        .why-box .headline { margin: 0 0 0.8rem; font-size: 1.45rem; font-weight: 800; color: var(--ink); line-height: 1.2; }
        .why-box .body, .note-box .body, .gov-box .body { margin: 0; color: var(--ink); line-height: 1.6; }
        .gov-box {
            background: var(--panel); border: 1px solid rgba(193,199,210,0.8); border-radius: 18px; padding: 1rem;
        }

        .recommend-card {
            background: var(--panel); border: 1px solid rgba(193,199,210,0.8); border-radius: 18px; padding: 1rem; height: 100%;
        }
        .recommend-card.high { border-left: 4px solid var(--red); }
        .recommend-card.medium { border-left: 4px solid var(--amber); }
        .recommend-card.low { border-left: 4px solid var(--teal); }
        .recommend-card .badge {
            display: inline-flex; align-items: center; padding: 0.25rem 0.65rem; border-radius: 999px; font-size: 0.72rem;
            font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;
        }
        .recommend-card h4 { margin: 0 0 0.6rem; font-size: 1.02rem; font-weight: 800; color: var(--ink); }
        .recommend-card .row { margin: 0 0 0.35rem; color: var(--ink-soft); line-height: 1.5; font-size: 0.92rem; }
        .recommend-card .row b { color: var(--ink); }

        .ai-notice {
            margin-top: 1rem; background: #f3f7fb; border: 1px solid rgba(193,199,210,0.8); border-radius: 18px; padding: 1rem 1rem 0.95rem;
        }
        .ai-notice h3 { margin: 0 0 0.7rem; font-size: 1.02rem; font-weight: 800; }
        .ai-notice p { margin: 0 0 0.55rem; color: var(--ink-soft); line-height: 1.6; }

        .exec-hero {
            background: linear-gradient(135deg, #004275 0%, #005a9c 100%); color: #fff; border-radius: 22px;
            padding: 1.7rem 1.8rem; margin-bottom: 1rem; position: relative; overflow: hidden;
            border: 1px solid rgba(255,255,255,0.15);
        }
        .exec-hero h2 { margin: 0 0 0.5rem; font-size: 2.4rem; line-height: 1.05; font-weight: 800; letter-spacing: -0.04em; }
        .exec-hero p { margin: 0; max-width: 760px; font-size: 1.05rem; line-height: 1.55; opacity: 0.96; }
        .exec-hero .action {
            background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2); border-radius: 16px;
            padding: 0.95rem 1.25rem; font-weight: 800; color: #fff; white-space: nowrap;
        }

        .exec-card {
            background: var(--panel); border: 1px solid rgba(193,199,210,0.8); border-radius: 18px; padding: 1rem; height: 100%;
        }
        .exec-card .label {
            color: var(--ink-soft); font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 0.6rem;
        }
        .exec-card .value { color: var(--primary); font-size: 2rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1.05; }
        .exec-card .value.small { font-size: 1.4rem; }
        .exec-card .desc { margin-top: 0.55rem; color: var(--ink-soft); line-height: 1.55; }

        .divider { height: 1px; background: rgba(193,199,210,0.8); margin: 0.9rem 0; }

        div[data-testid="stMetricValue"] {
            font-size: 1.8rem; font-weight: 800; color: var(--primary);
        }
        div[data-testid="stMetricLabel"] {
            color: var(--ink-soft); font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.72rem;
        }

        @media (max-width: 1180px) {
            .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .stepper { grid-template-columns: 1fr 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def append_csv_record(path: Path, record: dict, unique_key: str | None = None) -> bool:
    frame = pd.DataFrame([record])
    if path.exists():
        if unique_key and unique_key in frame.columns:
            existing = pd.read_csv(path)
            if unique_key in existing.columns and str(record[unique_key]) in existing[unique_key].astype(str).values:
                return False
        frame.to_csv(path, mode="a", header=False, index=False)
        return True

    frame.to_csv(path, index=False)
    return True


def get_ui_data(as_json: bool = False, result: dict | None = None):
    """Return the latest HydroSentinel analysis in an API-ready structure.

    Args:
        as_json: When True, returns a JSON string. Otherwise returns a dict.
        result: Optional analysis payload. Defaults to the current session state.

    Returns:
        A JSON-serializable dict or JSON string containing the latest results.
    """
    if result is None:
        try:
            data = st.session_state.get("analysis_result") or {}
        except Exception:
            data = {}
    else:
        data = result
    insights = data.get("insights", {}) or {}
    financial = data.get("financial_loss", {}) or {}
    environmental = data.get("environmental_impact", {}) or {}

    try:
        session_event_mode = bool(st.session_state.get("event_mode", False))
        session_source_mode = st.session_state.get("source_mode", "Upload CSV")
    except Exception:
        session_event_mode = False
        session_source_mode = "Upload CSV"

    payload = {
        "has_leak": bool(data.get("has_leak", False)),
        "leak_lpm": float(data.get("leak_lpm", 0.0)),
        "total_liters": float(data.get("total_liters", 0.0)),
        "leak_type": data.get("leak_type"),
        "confidence": float(data.get("confidence", 0.0)),
        "event_mode": bool(data.get("event_mode", session_event_mode)),
        "event_rows": int(data.get("event_rows", 0)),
        "analysis_id": data.get("analysis_id"),
        "source_mode": data.get("source_mode", session_source_mode),
        "validation_summary": data.get("validation_summary", {}),
        "reasoning_string": data.get("reasoning_string") or insights.get("reasoning", {}).get("reasoning_string", ""),
        "environmental_impact": {
            "carbon_footprint_kgco2e": float(environmental.get("carbon_footprint_kgco2e", 0.0)),
            "liters_saved": float(insights.get("environmental", {}).get("liters_saved", data.get("total_liters", 0.0))),
            "energy_saved_kwh": float(insights.get("environmental", {}).get("energy_saved_kwh", 0.0)),
            "narrative": insights.get("environmental", {}).get("narrative", ""),
        },
        "financial_loss": {
            "current_loss_usd_per_hour": float(financial.get("current_loss_usd_per_hour", 0.0)),
            "monthly_loss_usd": float(financial.get("monthly_loss_usd", 0.0)),
            "current_loss_label": insights.get("financial", {}).get("current_loss_label", "$0.00/hour"),
            "monthly_loss_label": insights.get("financial", {}).get("monthly_loss_label", "$0.00/month"),
            "narrative": insights.get("financial", {}).get("narrative", ""),
        },
        "insights": insights,
    }

    if as_json:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return payload


def build_analysis_id(df: pd.DataFrame) -> str:
    canonical = df[["Timestamp", "Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]].copy()
    canonical["Timestamp"] = canonical["Timestamp"].astype(str)
    return hashlib.sha256(canonical.to_csv(index=False).encode("utf-8")).hexdigest()[:16]


def save_feedback(analysis_id: str, verdict: str, result: dict) -> bool:
    top_timestamp = ""
    if result.get("has_leak") and result.get("top_row") is not None:
        top_timestamp = str(result["top_row"]["Timestamp"])

    feedback_record = {
        "submitted_at": pd.Timestamp.now().isoformat(),
        "analysis_id": analysis_id,
        "feedback": verdict,
        "predicted_leak": bool(result.get("has_leak")),
        "confidence": float(result.get("confidence", 0.0)),
        "top_timestamp": top_timestamp,
    }
    return append_csv_record(FEEDBACK_PATH, feedback_record)


def log_analysis_result(analysis_id: str, result: dict, training_summary: dict, target_summary: dict) -> bool:
    top_timestamp = ""
    if result.get("has_leak") and result.get("top_row") is not None:
        top_timestamp = str(result["top_row"]["Timestamp"])

    record = {
        "logged_at": pd.Timestamp.now().isoformat(),
        "analysis_id": analysis_id,
        "has_leak": bool(result.get("has_leak")),
        "anomaly_rows": int(len(result.get("anomalies", []))),
        "confidence": float(result.get("confidence", 0.0)),
        "leak_lpm": float(result.get("leak_lpm", 0.0)),
        "total_liters": float(result.get("total_liters", 0.0)),
        "top_timestamp": top_timestamp,
        "training_valid_rows": int(training_summary.get("valid_rows", 0)),
        "training_invalid_rows": int(training_summary.get("invalid_rows", 0)),
        "target_valid_rows": int(target_summary.get("valid_rows", 0)),
        "target_invalid_rows": int(target_summary.get("invalid_rows", 0)),
    }
    return append_csv_record(LOGS_PATH, record, unique_key="analysis_id")


def severity_level(leak_lpm: float) -> tuple[str, str]:
    if leak_lpm < 12:
        return "Minor", "warning"
    if leak_lpm <= 35:
        return "Moderate", "warning"
    return "Severe", "critical"


def significance_level(total_liters: float) -> str:
    if total_liters < 300:
        return "Low"
    if total_liters < 1500:
        return "Moderate"
    if total_liters < 4000:
        return "High"
    return "Severe"


def generate_demo_data(event_mode: bool) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    timestamps = pd.date_range("2026-06-18 08:00:00", periods=12, freq="h")
    rows = []
    for idx, timestamp in enumerate(timestamps):
        if idx < 5:
            status = "Class_Hours"
            flow = 14.7 + rng.normal(0, 0.7)
            pressure = 52.0 + rng.normal(0, 0.6)
        elif idx < 8:
            status = "Event" if event_mode else "Class_Hours"
            flow = (18.0 if event_mode else 16.0) + rng.normal(0, 0.8)
            pressure = (50.2 if event_mode else 51.2) + rng.normal(0, 0.6)
        else:
            status = "After_Hours"
            flow = 14.5 + (22 if idx >= 10 else 10) + rng.normal(0, 1.0)
            pressure = 52.0 - (11 if idx >= 10 else 4) + rng.normal(0, 0.8)

        rows.append(
            {
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Flow_Rate_LPM": round(max(flow, 0.1), 1),
                "Avg_Pressure_PSI": round(max(pressure, 1.0), 1),
                "Occupancy_Status": status,
            }
        )
    return pd.DataFrame(rows)


def load_target_dataframe(source_mode: str, uploaded_file, event_mode: bool) -> tuple[pd.DataFrame, dict]:
    if source_mode == "Live Demo":
        raw_df = generate_demo_data(event_mode)
    else:
        if uploaded_file is None:
            raise ValueError("Please upload a CSV file before analyzing.")
        raw_df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
    return validate_and_clean_data(raw_df, "analysis data")


def load_training_dataframe(event_mode: bool) -> tuple[pd.DataFrame, dict]:
    training_df = load_training_labels_for_mode(SAMPLE_FILES["normal"], SAMPLE_FILES["event"], event_mode=event_mode)
    return training_df, training_df.attrs.get("validation_summary", {})


def build_recommendations(result: dict) -> list[dict]:
    leak_type = str(result.get("leak_type", "fixture_leak"))
    label = leak_type.replace("_", " ").title()
    confidence = float(result.get("leak_type_confidence", 0.0))
    leak_lpm = float(result.get("leak_lpm", 0.0))

    templates = {
        "fixture_leak": (
            "Inspect the nearest fixture or valve assembly",
            f"The classifier predicts {label} with {confidence:.0f}% confidence.",
            "Check flappers, cartridges, and shutoff seals. Run a follow-up flow check after repair.",
        ),
        "valve_failure": (
            "Isolate the affected valve branch",
            f"The classifier predicts {label} with {confidence:.0f}% confidence.",
            "Inspect actuator, spring, and seat. Confirm the valve closes fully after repair.",
        ),
        "mainline_break": (
            "Escalate to urgent plumbing response",
            f"The classifier predicts {label} with {confidence:.0f}% confidence.",
            "Shut the affected section, inspect the main supply line, and repair immediately.",
        ),
    }
    first, second, third = templates.get(leak_type, templates["fixture_leak"])
    return [
        {"tag": "Priority 1", "tag_class": "high", "title": first, "reason": second, "location": "Flagged zone or nearest control point", "fix": third, "why": f"The model estimates {leak_lpm:.1f} L/min of loss, so this is the fastest way to stop waste."},
        {"tag": "Priority 2", "tag_class": "medium", "title": "Verify the repair with a second reading", "reason": "Prevent partial fixes from being mistaken for full resolution.", "location": "Same branch or fixture.", "fix": "Repeat the telemetry check after the corrective action.", "why": "A confirmation pass reduces false closure on unresolved leaks."},
        {"tag": "Priority 3", "tag_class": "low", "title": "Inspect neighboring fixtures or joints", "reason": "Wear often appears in nearby components after one failure.", "location": "Adjacent restrooms or branch lines.", "fix": "Review for slow drips or pressure instability nearby.", "why": "Preventive checks reduce repeat maintenance later in the term."},
    ]


def render_sidebar() -> tuple[str, bool, str, object | None, bool]:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <h1>HydroSentinel AI</h1>
                <p>Precision maintenance for school water infrastructure</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-title">Data Source</div>', unsafe_allow_html=True)
        source_mode = st.radio(
            "Data Source",
            ["Upload CSV", "Live Demo"],
            label_visibility="collapsed",
            key="source_mode_radio",
        )

        uploaded_file = None
        if source_mode == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload water telemetry CSV",
                type=["csv"],
                label_visibility="collapsed",
                key="telemetry_uploader",
            )
            if uploaded_file is not None:
                st.session_state["uploaded_file_name"] = uploaded_file.name

        st.markdown('<div class="sidebar-section-title">Event Mode</div>', unsafe_allow_html=True)
        st.session_state["event_mode"] = st.toggle(
            "Event Mode",
            value=bool(st.session_state["event_mode"]),
            help="Enable this for assemblies, sports days, celebrations, and other planned school events.",
        )

        event_card_class = "event-on" if st.session_state["event_mode"] else "event-off"
        event_label = "ON" if st.session_state["event_mode"] else "OFF"
        event_copy = (
            "Event-aware analysis is active. Legitimate crowd-driven usage is interpreted with event context."
            if st.session_state["event_mode"]
            else "Standard school-day usage is the default. Turn Event Mode on when event traffic is expected."
        )
        st.markdown(
            f"""
            <div class="sidebar-card {event_card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; margin-bottom:0.45rem;">
                    <div style="font-weight:800;">Event Mode</div>
                    <span class="sidebar-chip {'chip-success' if st.session_state['event_mode'] else 'chip-muted'}">{event_label}</span>
                </div>
                <div style="color:#4b5563; line-height:1.55; font-size:0.92rem;">{event_copy}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-title">Analysis</div>', unsafe_allow_html=True)
        if st.button("Analyze", use_container_width=True):
            st.session_state["analysis_requested"] = True

        st.markdown('<div class="sidebar-section-title">Action</div>', unsafe_allow_html=True)
        st.button("Upload CSV", use_container_width=True, disabled=True)

    return source_mode, st.session_state["event_mode"], st.session_state["view_mode"], uploaded_file, bool(st.session_state.get("analysis_requested"))


def perform_analysis(source_mode: str, uploaded_file, event_mode: bool) -> None:
    st.session_state["analysis_error"] = None
    try:
        training_df, training_summary = load_training_dataframe(event_mode)
        target_df, target_summary = load_target_dataframe(source_mode, uploaded_file, event_mode)
        _, model_reused = ensure_diagnostic_model(training_df, MODEL_PATH)
        result = evaluate_telemetry(target_df, MODEL_PATH, event_mode=event_mode)
        analysis_id = build_analysis_id(target_df)
        result["analysis_id"] = analysis_id
        result["model_reused"] = model_reused
        result["source_mode"] = source_mode
        result["event_mode"] = event_mode
        result["training_summary"] = training_summary
        result["target_summary"] = target_summary
        st.session_state["analysis_result"] = result
        st.session_state["analysis_id"] = analysis_id
        log_analysis_result(analysis_id, result, training_summary, target_summary)
    except Exception as exc:
        st.session_state["analysis_error"] = str(exc)


def render_header(event_mode: bool) -> None:
    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.0, 0.8])
    with col1:
        st.markdown('<div class="hero-title">HydroSentinel AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">School water monitoring that flags suspicious usage, explains why it happened, and helps teams respond with confidence.</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="sidebar-section-title" style="margin-top:0; margin-bottom:0.4rem;">View Mode</div>', unsafe_allow_html=True)
        st.radio(
            "View Mode",
            ["Operational clarity", "Executive summary"],
            horizontal=True,
            label_visibility="collapsed",
            key="view_mode_radio",
        )
        st.session_state["view_mode"] = st.session_state["view_mode_radio"]
    with col3:
        badge = "chip-success" if event_mode else "chip-muted"
        text = "Event Mode: ON" if event_mode else "Event Mode: OFF"
        st.markdown(f'<div style="padding-top:1.15rem;"><span class="sidebar-chip {badge}">{text}</span></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div style="padding-top:1.15rem; text-align:right;"><span class="sidebar-chip chip-primary">Admin Access</span></div>', unsafe_allow_html=True)


def render_loading_hint() -> None:
    st.markdown(
        """
        <div style="background:rgba(255,255,255,0.72); border:1px solid rgba(193,199,210,0.55); border-radius:18px; padding:1rem 1.1rem; margin-bottom:1rem;">
            <div style="color:#4b5563; line-height:1.6;">
                HydroSentinel learns normal flow, pressure, and occupancy patterns from labeled telemetry. Use <b>Event Mode</b> when the school has planned activities so the model respects legitimate usage spikes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_documentation() -> None:
    """Display information about the sample CSV files used for demonstration and training."""
    st.markdown('<h3 style="font-size:1.2rem; font-weight:800; margin:1.5rem 0 0.75rem; color:#121c28;">📊 Simulated Data Files</h3>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="background:#f9fafb; border:1px solid rgba(193,199,210,0.6); border-radius:16px; padding:1.15rem; margin-bottom:1.5rem;">
            <p style="color:#414750; line-height:1.65; margin:0;">
                <b style="color:#004275;">⚠️ Simulation Notice:</b> The following CSV files represent simulated IoT sensor data created for demonstration and testing purposes only. 
                These files model the behavior of flow rates and pressure readings in a school water infrastructure environment, compensating for the absence of real sensor hardware during this pilot phase.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    data_files = [
        {
            "name": "normal.csv",
            "description": "Baseline normal water usage during typical school days",
            "simulation": "Models regular flow and pressure patterns during Class Hours, After Hours, and Vacation periods",
            "path": APP_DIR / "normal.csv",
        },
        {
            "name": "example_normal_day_2026-10-05.csv",
            "description": "Example of a single day's normal operations",
            "simulation": "Simulates hourly telemetry for a complete school day with realistic occupancy transitions",
            "path": APP_DIR / "example_normal_day_2026-10-05.csv",
        },
        {
            "name": "event.csv",
            "description": "Water usage patterns during planned school events",
            "simulation": "Simulates elevated flow and pressure readings during assemblies, sports days, and celebrations",
            "path": APP_DIR / "event.csv",
        },
        {
            "name": "event_leak.csv",
            "description": "Sample data with anomalies for leak detection validation",
            "simulation": "Simulates leak scenarios combined with event activity to test model reliability",
            "path": APP_DIR / "event_leak.csv",
        },
    ]

    for i, file_info in enumerate(data_files, 1):
        st.markdown(
            f"""
            <div style="background:#ffffff; border:1px solid rgba(193,199,210,0.7); border-radius:14px; padding:1rem; margin-bottom:0.85rem;">
                <div style="display:flex; align-items:flex-start; gap:1rem;">
                    <div style="background:#dbeafe; color:#004275; width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; flex-shrink:0;">{i}</div>
                    <div style="flex:1;">
                        <div style="font-weight:800; color:#121c28; font-size:1rem; margin-bottom:0.3rem;">📄 {file_info['name']}</div>
                        <p style="color:#414750; margin:0.4rem 0 0; line-height:1.55; font-size:0.95rem;">
                            <b>Purpose:</b> {file_info['description']}
                        </p>
                        <p style="color:#5b6471; margin:0.4rem 0 0; line-height:1.55; font-size:0.92rem;">
                            <b>Simulation:</b> {file_info['simulation']}
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        file_path = file_info["path"]
        if file_path.exists():
            with file_path.open("rb") as csv_file:
                st.download_button(
                    label=f"Download {file_info['name']} (Simulation Data)",
                    data=csv_file.read(),
                    file_name=file_info["name"],
                    mime="text/csv",
                    key=f"download_sim_csv_{i}",
                    use_container_width=True,
                    help="Simulation Data: Synthetic IoT-style telemetry used for HydroSentinel demo and validation.",
                )
        else:
            st.warning(f"Simulation file not found: {file_info['name']}")


def render_operational(result: dict) -> None:
    has_leak = bool(result["has_leak"])
    target_df = result["df"]
    event_mode = bool(result.get("event_mode", False))
    event_rows = int(result.get("event_rows", 0))

    if has_leak:
        sev_label, _ = severity_level(float(result["leak_lpm"]))
        st.markdown(
            f"""
            <div class="banner-critical">
                <div>
                    <p class="banner-title">Critical Leak Detected</p>
                    <p class="banner-copy">{str(result.get('leak_type', 'Unknown')).replace('_', ' ').title()} pattern found with {result.get('confidence', 0.0):.1f}% confidence. Review the telemetry and respond before waste escalates.</p>
                </div>
                <div class="banner-action">{sev_label} severity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="banner-safe">
                <div>
                    <p class="banner-title">No Leak Detected</p>
                    <p class="banner-copy">The analysis stayed close to normal usage patterns. Keep monitoring, and re-run with Event Mode when planned activities change occupancy.</p>
                </div>
                <div class="banner-action">Stable</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="stepper">
            <div class="step active"><div class="step-badge">1</div><div><p class="meta">Step 1</p><p class="label">Sensor Readings</p></div></div>
            <div class="step active"><div class="step-badge">2</div><div><p class="meta">Step 2</p><p class="label">Pattern Analysis</p></div></div>
            <div class="step dimmed"><div class="step-badge">3</div><div><p class="meta">Step 3</p><p class="label">Env. Insight</p></div></div>
            <div class="step dimmed"><div class="step-badge">4</div><div><p class="meta">Step 4</p><p class="label">Action</p></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_text = "Active Leak" if has_leak else "Normal Flow"
    leak_type = str(result.get("leak_type", "No leak")).replace("_", " ").title()
    confidence = float(result.get("confidence", 0.0)) if has_leak else 0.0
    cost_per_day = float(result.get("leak_lpm", 0.0)) * WATER_COST_PER_LITER * 60 * 24 if has_leak else 0.0
    total_liters = float(result.get("total_liters", 0.0))
    impact = significance_level(total_liters)

    kpi_cols = st.columns(5)
    cards = [
        ("Status", status_text, f"{confidence:.1f}% detection confidence" if has_leak else "Stable baseline", "accent-critical" if has_leak else "accent-ok"),
        ("Type", leak_type, f"{float(result.get('leak_type_confidence', 0.0)):.1f}% classifier confidence" if has_leak else "No leak pattern", "accent-info"),
        ("Water Loss", f"{float(result.get('leak_lpm', 0.0)):.1f} L/m", f"{total_liters:.1f} L total anomalous water" if has_leak else "No abnormal loss", "accent-warning"),
        ("Cost Impact", f"${cost_per_day:,.0f}/hr", "Projected operating cost" if has_leak else "No added cost", "accent-warning"),
        ("Env Impact", impact, f"{int(total_liters / DAILY_DRINKING_LITERS_PER_STUDENT)} students' drinking water" if has_leak else "No environmental impact", "accent-ok"),
    ]
    for col, (title, value, foot, accent) in zip(kpi_cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card {accent}">
                    <div>
                        <div class="title">{title}</div>
                        <div class="value {'small' if len(value) > 12 else ''}">{value}</div>
                    </div>
                    <div class="foot">{foot}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    main_cols = st.columns([2.15, 1])
    with main_cols[0]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3>Flow Over Time</h3>', unsafe_allow_html=True)
        st.markdown('<p class="sub">Real-time telemetry versus anomaly markers</p>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=target_df["Timestamp"], y=target_df["Flow_Rate_LPM"], mode="lines", name="Flow", line=dict(color="#004275", width=3), fill="tozeroy", fillcolor="rgba(0, 66, 117, 0.06)"))
        if has_leak and len(result["anomalies"]) > 0:
            fig.add_trace(go.Scatter(x=result["anomalies"]["Timestamp"], y=result["anomalies"]["Flow_Rate_LPM"], mode="markers", name="Anomaly", marker=dict(color="#dc2626", size=10, symbol="circle")))
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), height=420, showlegend=False, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", xaxis=dict(title="Time", gridcolor="#edf2f7"), yaxis=dict(title="Flow (L/min)", gridcolor="#edf2f7"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with main_cols[1]:
        insights = result.get("insights", {}) or {}
        financial = insights.get("financial", {}) or {}
        environmental = insights.get("environmental", {}) or {}
        reasoning = insights.get("reasoning", {}) or {}
        feature_drivers = reasoning.get("drivers", []) or []
        driver_names = [str(item[0]).replace("numeric__", "").replace("categorical__", "").replace("_", " ") for item in feature_drivers]

        st.markdown(
            f"""
            <div class="why-box">
                <div class="title">Explainability Card</div>
                <div class="headline">{reasoning.get('headline', ('High confidence leak signature' if has_leak else 'Usage stayed within normal bounds'))}</div>
                <p class="body">{reasoning.get('narrative', ('The model compared current flow and pressure against the learned baseline. Rising flow paired with falling pressure matched a leak pattern.' if has_leak else 'The current readings stayed close to the learned school-day profile, so the system did not flag a leak.'))}</p>
                <div class="divider"></div>
                <div class="exec-card" style="padding:0.85rem; margin-bottom:0.65rem;">
                    <div class="label">Financial</div>
                    <div class="value small">{financial.get('current_loss_label', '$0.00/hour')}</div>
                    <div class="desc">{financial.get('narrative', 'No financial loss detected.')}</div>
                    <div style="display:flex; gap:0.45rem; flex-wrap:wrap; margin-top:0.55rem;">
                        <span class="sidebar-chip chip-warning">Monthly: {financial.get('monthly_loss_label', '$0.00/month')}</span>
                    </div>
                </div>
                <div class="exec-card" style="padding:0.85rem; margin-bottom:0.65rem;">
                    <div class="label">Environmental</div>
                    <div class="value small">{environmental.get('liters_saved', 0.0):,.1f} L</div>
                    <div class="desc">{environmental.get('narrative', 'No environmental impact detected.')}</div>
                    <div style="display:flex; gap:0.45rem; flex-wrap:wrap; margin-top:0.55rem;">
                        <span class="sidebar-chip chip-success">Energy: {environmental.get('energy_saved_kwh', 0.0):,.2f} kWh</span>
                        <span class="sidebar-chip chip-muted">Carbon: {environmental.get('carbon_saved_kgco2e', 0.0):,.2f} kgCO2e</span>
                    </div>
                </div>
                <div class="exec-card" style="padding:0.85rem;">
                    <div class="label">Reasoning</div>
                    <div class="desc" style="margin-top:0;">{reasoning.get('narrative', '')}</div>
                    <div style="display:flex; gap:0.45rem; flex-wrap:wrap; margin-top:0.6rem;">
                        {''.join([f'<span class="sidebar-chip chip-primary">{name}</span>' for name in driver_names]) if driver_names else '<span class="sidebar-chip chip-muted">Baseline comparison</span>'}
                    </div>
                    <div class="divider"></div>
                    <p class="body" style="margin-bottom:0.35rem;"><b>Event mode:</b> {'Event-aware analysis is active.' if event_mode else 'Off. Turn it on when school events are expected.'}</p>
                    <p class="body" style="margin-bottom:0.35rem;"><b>Event rows:</b> {event_rows}</p>
                    <p class="body"><b>Data validity:</b> {result.get('validation_summary', {}).get('valid_rows', len(target_df))} valid rows used.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="note-box" style="margin-top:1rem;">
                <div class="title">Contextual Event Note</div>
                <p class="body">{('Event-aware context is protecting the analysis from planned-activity false positives.' if event_mode else 'If a school event is underway, turn Event Mode on for a more realistic baseline.')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:1.2rem; font-weight:800; margin:0 0 0.75rem; color:#121c28;">Recommended Next Steps</h3>', unsafe_allow_html=True)
    if has_leak:
        recs = build_recommendations(result)
        rec_cols = st.columns(3)
        for col, rec in zip(rec_cols, recs):
            with col:
                badge_class = "chip-danger" if rec["tag_class"] == "high" else "chip-warning" if rec["tag_class"] == "medium" else "chip-success"
                st.markdown(
                    f"""
                    <div class="recommend-card {rec['tag_class']}">
                        <span class="badge {badge_class}">{rec['tag']}</span>
                        <h4>{rec['title']}</h4>
                        <p class="row"><b>Reason:</b> {rec['reason']}</p>
                        <p class="row"><b>Likely location:</b> {rec['location']}</p>
                        <p class="row"><b>How to fix:</b> {rec['fix']}</p>
                        <p class="row"><b>Why this priority:</b> {rec['why']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            """
            <div class="recommend-card low">
                <span class="badge chip-success">No Action Required</span>
                <h4>Keep Monitoring</h4>
                <p class="row">The current telemetry stayed within the learned normal profile. Continue routine observation and re-run with Event Mode if occupancy changes.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="ai-notice">
            <h3>Responsible AI Notice</h3>
            <p><b>Human-in-the-loop required.</b> HydroSentinel supports maintenance decisions; it does not perform automatic shutoff or autonomous control.</p>
            <p><b>Event Mode matters.</b> It helps the model interpret planned school activity so legitimate usage is not mistaken for a leak.</p>
            <p><b>Known limitation.</b> Unusual but legitimate patterns can still look suspicious if the model has not seen similar examples before.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_executive(result: dict) -> None:
    has_leak = bool(result["has_leak"])
    event_mode = bool(result.get("event_mode", False))
    event_rows = int(result.get("event_rows", 0))
    total_liters = float(result.get("total_liters", 0.0))
    peak_probability = float(result.get("max_leak_probability", 0.0))
    confidence = float(result.get("confidence", 0.0)) if has_leak else 0.0
    cost_per_day = float(result.get("leak_lpm", 0.0)) * WATER_COST_PER_LITER * 60 * 24 if has_leak else 0.0
    risk_label = significance_level(total_liters)
    status_text = "Critical" if has_leak else "Stable"

    st.markdown(
        """
        <div class="exec-hero">
            <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; flex-wrap:wrap; position:relative; z-index:1;">
                <div>
                    <h2>Institutional Safety Overview</h2>
                    <p>A high-level synthesis of water risk, response readiness, and operational impact across the current analysis run.</p>
                </div>
                <div class="action">Download Executive Summary</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    exec_cards = st.columns(4)
    payload = [
        ("Total Water at Risk", f"{total_liters:,.1f} L", "Estimated anomalous water in this run" if has_leak else "No abnormal water loss detected", "accent-info"),
        ("Peak Leak Probability", f"{peak_probability:.1f}%", "Highest anomaly likelihood in the current analysis", "accent-warning"),
        ("Event Context", "ON" if event_mode else "OFF", f"Event rows observed: {event_rows}", "accent-ok" if event_mode else "accent-info"),
        ("Executive Status", status_text, f"Confidence: {confidence:.1f}%" if has_leak else "Normal operating state", "accent-critical" if has_leak else "accent-ok"),
    ]
    for col, (label, value, foot, accent) in zip(exec_cards, payload):
        with col:
            st.markdown(
                f"""
                <div class="exec-card {accent}">
                    <div class="label">{label}</div>
                    <div class="value {'small' if len(value) > 12 else ''}">{value}</div>
                    <div class="desc">{foot}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    grid = st.columns([1.2, 1])
    with grid[0]:
        st.markdown('<div class="exec-card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Water Usage Efficiency</div>', unsafe_allow_html=True)
        st.markdown('<div class="desc" style="margin-top:0;">Operational usage versus projected baseline for this analysis run.</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=result["df"]["Timestamp"], y=result["df"]["Flow_Rate_LPM"], mode="lines", name="Usage", line=dict(color="#004275", width=3), fill="tozeroy", fillcolor="rgba(0,66,117,0.06)"))
        if has_leak:
            fig.add_trace(go.Scatter(x=result["anomalies"]["Timestamp"], y=result["anomalies"]["Flow_Rate_LPM"], mode="markers", marker=dict(color="#dc2626", size=10), name="Anomaly"))
        fig.update_layout(template="plotly_white", height=360, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", xaxis=dict(title="Time", gridcolor="#edf2f7"), yaxis=dict(title="Flow (L/min)", gridcolor="#edf2f7"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="exec-card" style="margin-top:1rem;">
                <div class="label">Budget Allocation</div>
                <div style="display:grid; gap:0.8rem; margin-top:0.55rem;">
                    <div>
                        <div class="desc" style="display:flex; justify-content:space-between; margin-top:0; font-size:0.9rem;"><span>Manual inspection exposure</span><span style="font-family:JetBrains Mono, monospace; font-weight:700;">${cost_per_day:,.0f}/day</span></div>
                        <div style="height:10px; background:#eef4ff; border-radius:999px; overflow:hidden;"><div style="width:{min(100, max(8, total_liters / 60))}%; height:100%; background:#004275;"></div></div>
                    </div>
                    <div>
                        <div class="desc" style="display:flex; justify-content:space-between; margin-top:0; font-size:0.9rem;"><span>Event-aware confidence</span><span style="font-family:JetBrains Mono, monospace; font-weight:700;">{event_mode and 'ON' or 'OFF'}</span></div>
                        <div style="height:10px; background:#eef4ff; border-radius:999px; overflow:hidden;"><div style="width:{peak_probability if peak_probability > 1 else 1}%; height:100%; background:#006a61;"></div></div>
                    </div>
                </div>
                <div class="divider"></div>
                <p class="desc" style="font-style:italic; margin-bottom:0;">"HydroSentinel helps leadership prioritize response by showing the current risk in plain language, without hiding the operational evidence."</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with grid[1]:
        executive_reasoning = ((result.get("insights", {}) or {}).get("reasoning", {}) or {}).get("narrative", "")
        st.markdown(
            f"""
            <div class="exec-card" style="margin-bottom:1rem;">
                <div class="label">Sustainability Score</div>
                <div class="value">{'A+' if not has_leak else 'B'}</div>
                <div class="desc">{('Healthy operating profile' if not has_leak else 'Leak impact should be resolved to preserve resources')}</div>
            </div>
            <div class="exec-card" style="margin-bottom:1rem;">
                <div class="label">Risk Tier</div>
                <div class="value small">{risk_label}</div>
                <div class="desc">Leadership-friendly severity summary based on the current telemetry run.</div>
            </div>
            <div class="exec-card gov-box">
                <div class="title">AI Governance & Logic</div>
                <div class="body">{executive_reasoning or 'HydroSentinel compares live telemetry with its learned baseline and uses Event Mode when school activity is expected. Human review remains required before any action.'}</div>
                <div class="divider"></div>
                <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                    <span class="sidebar-chip chip-primary">Human-in-the-loop</span>
                    <span class="sidebar-chip chip-muted">Event-aware</span>
                    <span class="sidebar-chip chip-muted">Decision Support</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="ai-notice">
            <h3>Responsible AI Notice</h3>
            <p>HydroSentinel provides advisory scoring only. It does not shut off water, trigger automation, or replace human judgment.</p>
            <p>Event Mode is essential during assemblies, sports days, and other planned activities because occupancy patterns change without implying a leak.</p>
            <p>Model confidence depends on the quality of the uploaded or simulated telemetry and the current training context.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    init_state()
    inject_styles()

    source_mode, event_mode, view_mode, uploaded_file, analyze_requested = render_sidebar()
    st.session_state["source_mode"] = source_mode
    st.session_state["view_mode"] = view_mode

    render_header(event_mode)
    view_mode = st.session_state["view_mode"]
    render_loading_hint()
    render_data_documentation()

    if analyze_requested:
        perform_analysis(source_mode, uploaded_file, event_mode)
        st.session_state["analysis_requested"] = False

    result = st.session_state.get("analysis_result")
    analysis_error = st.session_state.get("analysis_error")

    if analysis_error:
        st.error(f"We couldn't run the analysis: {analysis_error}")

    if result is None and not analysis_error:
        st.info("Upload a telemetry CSV or run the live demo, then press Analyze to see the dashboard.")
        return

    if result is not None:
        if view_mode == "Operational clarity":
            render_operational(result)
        else:
            render_executive(result)


if __name__ == "__main__":
    main()