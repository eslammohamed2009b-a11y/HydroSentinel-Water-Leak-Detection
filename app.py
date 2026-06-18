import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import hashlib
from pathlib import Path
from ml_engine import (
    REQUIRED_COLUMNS,
    WATER_COST_PER_LITER,
    ensure_model,
    evaluate_telemetry,
    find_sample_file,
    load_default_training_data,
    validate_and_clean_data,
)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="HydroSentinel — Water Infrastructure Decision Support for Schools",
    page_icon="💧",
    layout="wide",
)

# =============================================================================
# DESIGN SYSTEM
# A calm, trustworthy "field report" look for a decision-support tool that
# school maintenance teams will actually use — not a security-ops or hacker dashboard.
# =============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ink: #1B2A28;
        --ink-soft: #4B5D59;
        --paper: #F6F8F7;
        --panel: #FFFFFF;
        --border: #DDE5E2;
        --teal: #146C5F;
        --teal-soft: #E3F0EC;
        --leaf: #3F8F5F;
        --leaf-soft: #EAF6EE;
        --amber: #B9791A;
        --amber-soft: #FCF1DE;
        --coral: #B03A2E;
        --coral-soft: #FBEAE7;
    }

    html, body, .main, [data-testid="stAppViewContainer"] {
        background-color: var(--paper);
        color: var(--ink);
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    }

    h1, h2, h3, .serif {
        font-family: 'Lora', Georgia, serif;
        color: var(--ink);
        letter-spacing: -0.2px;
    }

    p, span, div, label { color: var(--ink); }

    [data-testid="stSidebar"] {
        background-color: var(--panel);
        border-right: 1px solid var(--border);
    }

    /* Top banner / wordmark */
    .app-title { font-family: 'Lora', Georgia, serif; font-weight: 700; font-size: 2rem; color: var(--ink); margin-bottom: 2px; }
    .app-subtitle { font-family: 'Inter', sans-serif; color: var(--ink-soft); font-size: 1rem; margin-bottom: 22px; }

    /* Mission pipeline strip — literal sequence: data in -> analysis -> insight -> action */
    .pipeline-wrap { display: flex; align-items: center; gap: 10px; margin: 6px 0 26px 0; flex-wrap: wrap; }
    .pipeline-step {
        background-color: var(--panel); border: 1px solid var(--border); border-radius: 8px;
        padding: 10px 16px; font-size: 0.88rem; font-weight: 600; color: var(--ink);
        display: flex; align-items: center; gap: 8px; flex: 1; min-width: 150px;
    }
    .pipeline-step .num { color: var(--teal); font-family: 'Lora', serif; font-weight: 700; }
    .pipeline-arrow { color: var(--ink-soft); font-size: 1.1rem; }

    /* Context notice */
    .context-note {
        background-color: var(--panel); border: 1px solid var(--border); border-left: 4px solid var(--teal);
        padding: 14px 18px; border-radius: 6px; color: var(--ink-soft); font-size: 0.88rem;
        margin-bottom: 26px; line-height: 1.5;
    }

    /* Status banners */
    .status-banner {
        border-radius: 8px; padding: 18px 22px; margin-bottom: 24px; border: 1px solid;
    }
    .status-banner.critical { background-color: var(--coral-soft); border-color: var(--coral); }
    .status-banner.ok { background-color: var(--leaf-soft); border-color: var(--leaf); }
    .status-headline { font-family: 'Lora', serif; font-weight: 700; font-size: 1.25rem; margin-bottom: 4px; }
    .status-banner.critical .status-headline { color: var(--coral); }
    .status-banner.ok .status-headline { color: var(--leaf); }
    .status-sub { font-size: 0.92rem; color: var(--ink-soft); }

    /* At-a-glance answer cards (shown before charts) */
    .answer-card {
        background-color: var(--panel); border: 1px solid var(--border); border-radius: 8px;
        padding: 16px 18px; height: 100%;
    }
    .answer-card .label { font-size: 0.78rem; color: var(--ink-soft); font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }
    .answer-card .value { font-family: 'Lora', serif; font-size: 1.45rem; font-weight: 700; color: var(--ink); line-height: 1.25; }
    .answer-card .footnote { font-size: 0.78rem; color: var(--ink-soft); margin-top: 6px; }
    .answer-card.accent-critical { border-left: 4px solid var(--coral); }
    .answer-card.accent-warning { border-left: 4px solid var(--amber); }
    .answer-card.accent-ok { border-left: 4px solid var(--leaf); }
    .answer-card.accent-info { border-left: 4px solid var(--teal); }

    /* Streamlit metric overrides (used inside tabs) */
    div[data-testid="stMetricValue"] { font-family: 'Lora', serif; font-size: 1.9rem; font-weight: 700; color: var(--ink); }
    div[data-testid="stMetricLabel"] { color: var(--ink-soft); font-weight: 600; }

    /* Explainability ("why") cards */
    .why-card {
        background-color: var(--panel); border: 1px solid var(--border); border-left: 4px solid var(--teal);
        border-radius: 8px; padding: 18px 20px; margin-bottom: 16px;
    }
    .why-title { font-family: 'Lora', serif; font-weight: 700; color: var(--ink); font-size: 1.05rem; margin-bottom: 10px; }
    .why-compare { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 10px; }
    .why-compare .pair { font-size: 0.88rem; color: var(--ink-soft); }
    .why-compare .pair b { color: var(--ink); font-size: 0.95rem; }
    .why-reason { font-size: 0.92rem; color: var(--ink); margin-bottom: 8px; line-height: 1.5; }
    .why-evidence { font-size: 0.82rem; color: var(--ink-soft); background: var(--paper); padding: 8px 10px; border-radius: 4px; display: block; }
    .confidence-tag { display: inline-block; background: var(--teal-soft); color: var(--teal); font-size: 0.78rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; margin-bottom: 10px; }

    /* Recommendation cards (action / reason / evidence) */
    .action-card {
        background-color: var(--panel); border: 1px solid var(--border); border-radius: 8px;
        padding: 18px 20px; margin-bottom: 16px;
    }
    .action-card.priority-high { border-left: 4px solid var(--coral); }
    .action-card.priority-medium { border-left: 4px solid var(--amber); }
    .action-card.priority-low { border-left: 4px solid var(--teal); }
    .action-tag { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 9px; border-radius: 20px; }
    .action-tag.high { background: var(--coral-soft); color: var(--coral); }
    .action-tag.medium { background: var(--amber-soft); color: var(--amber); }
    .action-tag.low { background: var(--teal-soft); color: var(--teal); }
    .action-title { font-family: 'Lora', serif; font-weight: 700; font-size: 1.05rem; margin: 8px 0 10px 0; }
    .action-row { font-size: 0.9rem; margin-bottom: 6px; line-height: 1.5; }
    .action-row b { color: var(--ink); }

    /* Environmental impact panel */
    .env-card {
        background-color: var(--leaf-soft); border: 1px solid var(--leaf); border-radius: 8px;
        padding: 20px 22px; margin-bottom: 24px;
    }
    .env-card h4 { font-family: 'Lora', serif; color: var(--leaf); margin: 0 0 12px 0; font-size: 1.1rem; }
    .env-stat { display: inline-block; margin-right: 32px; margin-bottom: 8px; }
    .env-stat .num { font-family: 'Lora', serif; font-weight: 700; font-size: 1.3rem; color: var(--ink); }
    .env-stat .lbl { font-size: 0.8rem; color: var(--ink-soft); }

    /* Responsible AI panel */
    .rai-card {
        background-color: var(--panel); border: 1px solid var(--border); border-radius: 8px;
        padding: 20px 22px; margin-top: 28px;
    }
    .rai-card h4 { font-family: 'Lora', serif; margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
    .rai-item { font-size: 0.88rem; color: var(--ink-soft); line-height: 1.6; margin-bottom: 10px; }
    .rai-item b { color: var(--ink); }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================
LARGE_LEAK_DIAMETER_MM = 15.0    # above this estimated opening size, treat as a structural leak

# =============================================================================
# SIDEBAR — DATA INPUT & DETECTION CONTEXT
# =============================================================================

# Determine the directory where sample files are located
# Use the app file location so Streamlit Cloud and local execution both find the CSVs.
app_dir = Path(__file__).resolve().parent
sample_files = {
    "normal": [app_dir / "normal.csv", app_dir / "example_normal_day_2026-10-05.csv"],
    "leak": [app_dir / "leak.csv"],
    "event": [app_dir / "event.csv"],
    "event_leak": [app_dir / "event_leak.csv"]
}
MODEL_PATH = app_dir / "hydrosentinel_isolation_forest.joblib"
FEEDBACK_PATH = app_dir / "feedback.csv"
LOGS_PATH = app_dir / "logs.csv"

with st.sidebar:
    st.subheader("📥 Download Samples")
    try:
        normal_file = find_sample_file(sample_files["normal"])
        leak_file = find_sample_file(sample_files["leak"])
        event_file = find_sample_file(sample_files["event"])
        event_leak_file = find_sample_file(sample_files["event_leak"])
        
        if normal_file:
            with open(normal_file, "rb") as f:
                st.download_button("📥 Normal Day Data", f, "normal.csv")
        else:
            st.warning("Normal Day Data file not found in project")
            
        if leak_file:
            with open(leak_file, "rb") as f:
                st.download_button("⚠️ Leak Day Data", f, "leak.csv")
        else:
            st.warning("Leak Day Data file not found in project")
            
        if event_file:
            with open(event_file, "rb") as f:
                st.download_button("📈 Event Day Data", f, "event.csv")
        else:
            st.warning("Event Day Data file not found in project")
            
        if event_leak_file:
            with open(event_leak_file, "rb") as f:
                st.download_button("🚨 Event + Leak Day Data", f, "event_leak.csv")
        else:
            st.warning("Event + Leak Day Data file not found in project")
    except Exception as e:
        st.warning(f"Error loading sample files: {str(e)}")

    st.markdown("---")
    st.markdown(
        "<div class='serif' style='font-size:1.4rem; font-weight:700; color:#146C5F; margin-bottom:0;'>💧 HydroSentinel AI</div>"
        "<div style='color:#4B5D59; font-size:0.85rem; margin-bottom:16px;'>Water Infrastructure Decision Support</div>",
        unsafe_allow_html=True,
    )
    st.caption("USAII Global AI Hackathon 2026")
    st.markdown("---")

    st.subheader("📥 Your Data")
    training_file = st.file_uploader(
        "Upload normal-day training readings",
        type=["csv"],
        key="training_file",
        help="Use clean no-leak data. If you have event-day readings without leaks, include them too so the model learns that those patterns are still normal.",
    )
    st.caption("If you skip this, HydroSentinel trains from the bundled normal-day and event-day no-leak samples.")

    mode = st.radio(
        "How should we get sensor readings?",
        ["Upload a CSV file", "Run a live demo (simulated)"],
        help="In a real school, this data would stream automatically from smart water meters. For this prototype, use a CSV or watch the simulated demo.",
    )

    uploaded_file = None
    stream_trigger = False
    if mode == "Upload a CSV file":
        uploaded_file = st.file_uploader("Upload campus water readings", type=["csv"])
        st.caption("Needs columns: Timestamp, Flow_Rate_LPM, Avg_Pressure_PSI, Occupancy_Status")
    else:
        st.caption("This simulates a normal morning that develops into a leak later in the day.")
        stream_trigger = st.button("▶ Run live demo")

    st.markdown("---")
    st.subheader("🤖 Detection Model")
    st.caption("HydroSentinel trains an IsolationForest model on normal-day readings, then assigns an anomaly score and leak probability to every new row.")

    st.markdown("---")
    st.markdown(
        "<span style='color:#4B5D59; font-size:0.85rem;'>Built by</span><br>"
        "<b style='color:#146C5F; font-size:1.05rem;'>Team EAT</b>",
        unsafe_allow_html=True,
    )

# =============================================================================
# HEADER
# =============================================================================
st.markdown('<div class="app-title">HydroSentinel AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">A real-world decision-support system for school water infrastructure — '
    'helping maintenance teams catch hidden leaks early, understand why they happened, and decide what to do next.</div>',
    unsafe_allow_html=True,
)

st.markdown("""
    <div class="pipeline-wrap">
        <div class="pipeline-step"><span class="num">1</span> 📥 Sensor Readings</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-step"><span class="num">2</span> 🔎 Pattern Analysis</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-step"><span class="num">3</span> 🌍 Environmental Insight</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-step"><span class="num">4</span> ✅ Recommended Action</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="context-note">
        <b>About this system:</b> HydroSentinel AI is a decision-support system for school water infrastructure,
        built to give maintenance teams clear, auditable evidence for acting on leaks by learning the normal
        relationship between flow, pressure, and occupancy from normal-day data with an IsolationForest model. This version reads water-use data from
        a CSV file (or a simulated live demo) to stand in for direct sensor integration, which wasn't available to
        test during development. In a real school deployment, HydroSentinel AI would connect directly to smart water
        meters and pressure sensors, watching them continuously day and night to support the maintenance team's
        day-to-day decisions.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# HELPERS
# =============================================================================
def build_analysis_id(df):
    """Build a stable identifier for one analysis run.

    Args:
        df: Clean input telemetry DataFrame.

    Returns:
        A short hash string used to deduplicate log entries.
    """
    signature_df = df[REQUIRED_COLUMNS].copy()
    signature_df["Timestamp"] = signature_df["Timestamp"].astype(str)
    digest = hashlib.sha256(signature_df.to_csv(index=False).encode("utf-8")).hexdigest()
    return digest[:16]


def append_record(path, record, unique_key=None):
    """Append one record to a CSV file with optional deduplication.

    Args:
        path: Destination CSV path.
        record: Dictionary to serialize as one CSV row.
        unique_key: Optional column name used to prevent duplicate writes.

    Returns:
        True when a row is written, otherwise False if deduplicated.
    """
    record_df = pd.DataFrame([record])
    if path.exists():
        if unique_key is not None:
            existing = pd.read_csv(path)
            if unique_key in existing.columns and str(record[unique_key]) in existing[unique_key].astype(str).values:
                return False
        record_df.to_csv(path, mode="a", header=False, index=False)
        return True

    record_df.to_csv(path, index=False)
    return True


def log_analysis_result(analysis_id, result, training_summary, target_summary):
    """Persist one analysis summary row to logs.csv.

    Args:
        analysis_id: Stable identifier for the analyzed dataset.
        result: Metrics dictionary returned by the ML engine.
        training_summary: Validation summary for the training dataset.
        target_summary: Validation summary for the analyzed dataset.

    Returns:
        True when a new log row is written, otherwise False.
    """
    top_timestamp = ""
    if result.get("has_leak"):
        top_timestamp = str(result["top_row"]["Timestamp"])

    log_record = {
        "logged_at": pd.Timestamp.now().isoformat(),
        "analysis_id": analysis_id,
        "has_leak": bool(result["has_leak"]),
        "anomaly_rows": int(len(result["anomalies"])),
        "confidence": float(result.get("confidence", 0.0)),
        "leak_lpm": float(result.get("leak_lpm", 0.0)),
        "total_liters": float(result.get("total_liters", 0.0)),
        "top_timestamp": top_timestamp,
        "training_valid_rows": int(training_summary.get("valid_rows", 0)),
        "training_invalid_rows": int(training_summary.get("invalid_rows", 0)),
        "target_valid_rows": int(target_summary.get("valid_rows", 0)),
        "target_invalid_rows": int(target_summary.get("invalid_rows", 0)),
    }
    return append_record(LOGS_PATH, log_record, unique_key="analysis_id")


def save_feedback(analysis_id, verdict, result):
    """Persist one user verdict for an alert into feedback.csv.

    Args:
        analysis_id: Stable identifier for the analyzed dataset.
        verdict: User-provided review label such as correct_alert.
        result: Metrics dictionary returned by the ML engine.

    Returns:
        True when the feedback row is written.
    """
    top_timestamp = ""
    if result.get("has_leak"):
        top_timestamp = str(result["top_row"]["Timestamp"])

    feedback_record = {
        "submitted_at": pd.Timestamp.now().isoformat(),
        "analysis_id": analysis_id,
        "feedback": verdict,
        "predicted_leak": bool(result["has_leak"]),
        "confidence": float(result.get("confidence", 0.0)),
        "top_timestamp": top_timestamp,
    }
    return append_record(FEEDBACK_PATH, feedback_record)


def load_training_dataframe(training_file):
    """Load and validate the training dataset used by the UI.

    Args:
        training_file: Optional uploaded training file from Streamlit.

    Returns:
        A tuple of (training_dataframe, validation_summary).
    """
    if training_file is not None:
        raw_training_df = pd.read_csv(training_file)
        return validate_and_clean_data(raw_training_df, "training data")

    default_training_df = load_default_training_data([sample_files["normal"], sample_files["event"]])
    if default_training_df is None:
        raise FileNotFoundError("No bundled no-leak training samples are available.")
    return validate_and_clean_data(default_training_df, "default training data")


def load_target_dataframe(uploaded_file):
    """Load and validate an uploaded telemetry file from the UI.

    Args:
        uploaded_file: Streamlit uploaded file object.

    Returns:
        A tuple of (target_dataframe, validation_summary).
    """
    raw_df = pd.read_csv(uploaded_file)
    return validate_and_clean_data(raw_df, "uploaded sensor data")


def severity_level(leak_lpm):
    """Map leak intensity to a display severity label.

    Args:
        leak_lpm: Estimated leak rate in liters per minute.

    Returns:
        A tuple of (label, css_class).
    """
    if leak_lpm < 12:
        return "Minor", "warning"
    elif leak_lpm <= 35:
        return "Moderate", "warning"
    else:
        return "Severe", "critical"


def significance_level(total_liters):
    """Map cumulative water loss to an impact label.

    Args:
        total_liters: Total anomalous liters observed in the dataset.

    Returns:
        A human-readable impact tier string.
    """
    if total_liters < 300:
        return "Low"
    elif total_liters < 1500:
        return "Moderate"
    elif total_liters < 4000:
        return "High"
    else:
        return "Severe"


def probability_status(probability):
    """Convert leak probability into a color-coded status label.

    Args:
        probability: Maximum leak probability percentage.

    Returns:
        A tuple of (status_label, css_color).
    """
    if probability < 35:
        return "Stable", "#3F8F5F"
    elif probability < 70:
        return "Needs Review", "#B9791A"
    return "High Risk", "#B03A2E"


def build_recommendations(res):
    """Rule-based recommendation engine: always returns exactly 3 prioritized
    actions (critical / important / preventive), each with an action, reason,
    likely location, fix, and the rule that set its priority."""
    diameter = res["diameter_mm"]
    large_leak = diameter > LARGE_LEAK_DIAMETER_MM

    if large_leak:
        priority_1 = {
            "tag": "Priority 1 — Critical", "tag_class": "high",
            "title": "Shut off the main water valve and call a licensed plumber",
            "reason": "Flow this high, combined with a pressure drop at the same time, points to a broken pipe or major fitting failure rather than a single fixture.",
            "location": "Main supply line or underground pipe network near the affected meter.",
            "fix": "A plumber needs to locate and repair the ruptured section; shutting the main valve stops the loss until the repair is scheduled.",
            "why_priority": f"The estimated opening size (Ø {diameter} mm) and the size of the flow spike mean this keeps wasting large volumes of water every hour it runs.",
        }
    else:
        priority_1 = {
            "tag": "Priority 1 — Critical", "tag_class": "high",
            "title": "Send a maintenance technician to inspect nearby restrooms and fixtures",
            "reason": "The flow jumped once and then held steady at a high level, which matches a stuck valve or a running toilet rather than a structural failure.",
            "location": "Restroom fixtures (toilet flush valve, urinal sensor, or sink faucet) closest to the flagged meter.",
            "fix": "Replace or adjust the stuck flapper/valve, or tighten a faucet that isn't shutting off completely.",
            "why_priority": "This is the most likely source of the flagged flow and is usually a quick, low-cost fix once located.",
        }

    priority_2 = {
        "tag": "Priority 2 — Important", "tag_class": "medium",
        "title": "Isolate the affected zone while the repair is scheduled",
        "reason": "Closing the nearest branch valve narrows the search and limits water loss without shutting off water to the whole school.",
        "location": "Branch shutoff valve serving the zone or wing closest to the flagged meter.",
        "fix": "Close the zone valve, then re-check the flow reading — if it drops back to baseline, the leak is confirmed to be in that zone.",
        "why_priority": "This doesn't fix the root cause, but it stops ongoing waste and helps the technician find the leak faster once they arrive.",
    }

    priority_3 = {
        "tag": "Priority 3 — Preventive", "tag_class": "low",
        "title": "Check outdoor irrigation and HVAC/mechanical equipment",
        "reason": "Some flagged readings occurred outside normal occupancy hours, which points to automated equipment rather than people using water.",
        "location": "Irrigation controller valves or the HVAC cooling system's water makeup valve.",
        "fix": "Inspect solenoid valves and makeup-water controls for a stuck-open condition; recalibrate or replace as needed.",
        "why_priority": "This isn't necessarily today's leak, but stuck irrigation or HVAC valves are a common, recurring source of school water waste worth ruling out.",
    }

    return [priority_1, priority_2, priority_3]


def generate_demo_row(hour, baseline_flow, inject_leak=False):
    """Generate one simulated telemetry row for the Streamlit live demo.

    Args:
        hour: Integer hour used in the synthetic timestamp.
        baseline_flow: Expected baseline flow value.
        inject_leak: Whether to simulate a leak pattern for this row.

    Returns:
        A dictionary representing one telemetry row.
    """
    timestamp = f"2026-06-17 {hour:02d}:00:00"
    status = "Class_Hours" if 8 <= hour <= 15 else "After_Hours"
    if inject_leak and hour >= 12:
        flow = baseline_flow + np.random.uniform(35.0, 50.0)
        pressure = np.random.uniform(32.0, 38.0)
    else:
        flow = baseline_flow + np.random.uniform(-2.0, 2.0)
        pressure = np.random.uniform(50.0, 55.0)
    return {"Timestamp": timestamp, "Flow_Rate_LPM": round(flow, 1), "Avg_Pressure_PSI": round(pressure, 1), "Occupancy_Status": status}


# =============================================================================
# LOAD DATA
# =============================================================================
target_df = None
training_df = None
training_summary = None
target_summary = None

try:
    training_df, training_summary = load_training_dataframe(training_file)
except Exception as e:
    st.error(f"We couldn't prepare the training data: {e}")

if mode == "Upload a CSV file" and uploaded_file is not None:
    try:
        target_df, target_summary = load_target_dataframe(uploaded_file)
    except Exception as e:
        st.error(f"We couldn't prepare the uploaded telemetry: {e}")

elif mode == "Run a live demo (simulated)":
    if "demo_rows" not in st.session_state:
        st.session_state.demo_rows = [generate_demo_row(h, 15.0, inject_leak=False) for h in range(12)]
    if "demo_running" not in st.session_state:
        st.session_state.demo_running = False
    if stream_trigger:
        st.session_state.demo_running = True

    if st.session_state.demo_running:
        placeholder = st.empty()
        for hour in range(12, 24):
            new_row = generate_demo_row(hour, 15.0, inject_leak=True)
            st.session_state.demo_rows.append(new_row)
            try:
                target_df, target_summary = validate_and_clean_data(pd.DataFrame(st.session_state.demo_rows), "live demo data")
            except Exception as e:
                st.error(f"Live demo data became invalid: {e}")
                target_df = None
                target_summary = None
                break
            with placeholder.container():
                st.info(f"📡 Receiving reading for {new_row['Timestamp']} ...")
            time.sleep(0.15)
        st.session_state.demo_running = False
    else:
        try:
            target_df, target_summary = validate_and_clean_data(pd.DataFrame(st.session_state.demo_rows), "live demo data")
        except Exception as e:
            st.error(f"Live demo data is invalid: {e}")
            target_df = None
            target_summary = None

# =============================================================================
# DASHBOARD
# =============================================================================
if target_df is not None and training_df is not None:
    res = None
    recs = []
    analysis_id = None
    model_reused = None
    ml_error = None

    with st.spinner("Analyzing telemetry with HydroSentinel AI..."):
        try:
            _, model_reused = ensure_model(training_df, MODEL_PATH)
        except Exception as e:
            ml_error = f"We couldn't prepare the leak model: {e}"

        if ml_error is None:
            try:
                res = evaluate_telemetry(target_df, MODEL_PATH)
            except Exception as e:
                ml_error = f"We couldn't analyze the telemetry: {e}"

        if ml_error is None:
            analysis_id = build_analysis_id(target_df)
            try:
                log_analysis_result(analysis_id, res, training_summary or {}, target_summary or {})
            except Exception as e:
                st.warning(f"Analysis completed, but we couldn't write logs.csv: {e}")

    if ml_error is not None:
        st.error(ml_error)
    elif res is not None:
        recs = build_recommendations(res) if res["has_leak"] else []

        if training_summary and training_summary["invalid_rows"] > 0:
            st.warning(
                f"Training validation removed {training_summary['invalid_rows']} invalid row(s) and kept {training_summary['valid_rows']} row(s)."
            )
        if target_summary and target_summary["invalid_rows"] > 0:
            st.warning(
                f"Input validation removed {target_summary['invalid_rows']} invalid row(s) and kept {target_summary['valid_rows']} row(s)."
            )

        if model_reused is True:
            st.caption("Model cache: reused the persisted IsolationForest model because the training data signature did not change.")
        elif model_reused is False:
            st.caption("Model cache: training data changed, so HydroSentinel retrained and updated the persisted model.")

        if not res["time_parsed"]:
            st.caption("Note: we couldn't read dates/times from the Timestamp column, so time-of-day context wasn't used in this analysis.")

        probability_value = float(res.get("confidence", res.get("max_leak_probability", 0.0))) if res["has_leak"] else float(res.get("max_leak_probability", 0.0))
        status_label, status_color = probability_status(probability_value)
        metric_col, status_col = st.columns([1, 2])
        with metric_col:
            st.metric("Leak Probability", f"{probability_value:.1f}%")
        with status_col:
            st.markdown(
                f"<div style='padding-top:1.7rem; font-weight:700; color:{status_color};'>System status: {status_label}</div>",
                unsafe_allow_html=True,
            )

        if res["has_leak"]:
            sev_label, _ = severity_level(res["leak_lpm"])
            st.markdown(f"""
            <div class="status-banner critical">
                <div class="status-headline">🚨 Leak Detected — {sev_label} severity</div>
                <div class="status-sub">A water-use pattern diverged from the normal profile learned by the IsolationForest model. Review the details below before taking action.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-banner ok">
                <div class="status-headline">✅ No Leak Detected</div>
                <div class="status-sub">Water use across the readings we checked stayed close to the learned normal consumption pattern.</div>
            </div>
            """, unsafe_allow_html=True)

        if res["has_leak"]:
            sev_label, sev_class = severity_level(res["leak_lpm"])
            sig_label = significance_level(res["total_liters"])
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.markdown(f"""<div class="answer-card accent-critical">
                    <div class="label">Leak status</div><div class="value">Detected</div>
                    <div class="footnote">{res['confidence']:.0f}% detection confidence</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="answer-card accent-{sev_class}">
                    <div class="label">Severity</div><div class="value">{sev_label}</div>
                    <div class="footnote">Ø {res['diameter_mm']} mm estimated opening</div></div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="answer-card accent-warning">
                    <div class="label">Water being lost</div><div class="value">{res['leak_lpm']} L/min</div>
                    <div class="footnote">${res['cost_min']}/min in cost</div></div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class="answer-card accent-info">
                    <div class="label">Environmental impact</div><div class="value">{sig_label}</div>
                    <div class="footnote">Drinking water for {res['students_count']} students lost</div></div>""", unsafe_allow_html=True)
            with c5:
                quick_action = recs[0]["title"] if recs else "No action needed"
                st.markdown(f"""<div class="answer-card accent-ok">
                    <div class="label">Priority 1 action</div><div class="value" style="font-size:1.05rem;">{quick_action}</div>
                    <div class="footnote">See all 3 recommended actions below</div></div>""", unsafe_allow_html=True)
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="answer-card accent-ok"><div class="label">Leak status</div>
                    <div class="value">None</div><div class="footnote">All clear</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="answer-card accent-info"><div class="label">Typical flow</div>
                    <div class="value">{round(target_df['Flow_Rate_LPM'].median(), 1)} L/min</div>
                    <div class="footnote">Stable baseline</div></div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="answer-card accent-info"><div class="label">Typical pressure</div>
                    <div class="value">{round(target_df['Avg_Pressure_PSI'].mean(), 1)} PSI</div>
                    <div class="footnote">Within safe range</div></div>""", unsafe_allow_html=True)

        st.write("")
        tab1, tab2 = st.tabs(["📈 Trend Chart", "🛠️ Recommended Actions"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=target_df["Timestamp"], y=target_df["Flow_Rate_LPM"],
                mode="lines", name="Water flow",
                line=dict(color="#146C5F", width=3),
            ))
            if res["has_leak"]:
                fig.add_trace(go.Scatter(
                    x=res["anomalies"]["Timestamp"], y=res["anomalies"]["Flow_Rate_LPM"],
                    mode="markers", name="Flagged as unusual",
                    marker=dict(color="#B03A2E", size=10, symbol="circle", line=dict(color="#FFFFFF", width=1)),
                ))
                fig.add_annotation(
                    x=res["anomalies"]["Timestamp"].iloc[0], y=res["anomalies"]["Flow_Rate_LPM"].iloc[0],
                    text="Unusual reading", showarrow=True, arrowhead=2,
                    arrowcolor="#B03A2E", bgcolor="#FBEAE7", bordercolor="#B03A2E", font=dict(color="#B03A2E"),
                )
            fig.update_layout(
                template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                margin=dict(l=40, r=40, t=20, b=40), height=400,
                font=dict(family="Inter, sans-serif", color="#4B5D59"),
                xaxis=dict(gridcolor="#EEF2F1", title="Time"),
                yaxis=dict(gridcolor="#EEF2F1", title="Flow (L/min)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Each dot marks a reading that the IsolationForest model scored as anomalous relative to the normal-day training pattern.")

        with tab2:
            if res["has_leak"]:
                top_row = res["top_row"]
                st.markdown(f"""
                <div class="why-card">
                    <span class="confidence-tag">{res['confidence']:.0f}% detection confidence</span>
                    <div class="why-title">Why the system flagged this</div>
                    <div class="why-compare">
                        <div class="pair">Baseline flow: <b>{res['base_flow']} L/min</b> → Current flow: <b>{top_row['Flow_Rate_LPM']} L/min</b> ({res['deviation_pct']:.0f}% above baseline)</div>
                        <div class="pair">Baseline pressure: <b>{res['base_pressure']} PSI</b> → Current pressure: <b>{top_row['Avg_Pressure_PSI']} PSI</b> ({res['pressure_drop_pct']:.0f}% drop)</div>
                    </div>
                    <div class="why-reason">This reading received one of the highest anomaly scores from the IsolationForest model after it learned the normal relationship between flow, pressure, and occupancy status. Rising flow paired with falling pressure still matches the physical signature of water escaping through an unintended opening: when a fixture is used normally, flow and pressure tend to move together, but a leak pulls flow up while pressure drops.</div>
                    <span class="why-evidence">To put it in perspective: this is roughly the same rate as {res['metaphor']}.</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("##### What to do next")
                for rec in recs:
                    st.markdown(f"""
                    <div class="action-card priority-{rec['tag_class']}">
                        <span class="action-tag {rec['tag_class']}">{rec['tag']}</span>
                        <div class="action-title">{rec['title']}</div>
                        <div class="action-row"><b>Reason:</b> {rec['reason']}</div>
                        <div class="action-row"><b>Likely location:</b> {rec['location']}</div>
                        <div class="action-row"><b>How to fix:</b> {rec['fix']}</div>
                        <div class="action-row"><b>Why this priority:</b> {rec['why_priority']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("##### Alert review")
                review_col1, review_col2 = st.columns(2)
                if review_col1.button("Mark alert as correct", key=f"feedback_true_{analysis_id}"):
                    try:
                        save_feedback(analysis_id, "correct_alert", res)
                        st.success("Feedback saved to feedback.csv")
                    except Exception as e:
                        st.error(f"We couldn't save positive feedback: {e}")
                if review_col2.button("Mark alert as false alarm", key=f"feedback_false_{analysis_id}"):
                    try:
                        save_feedback(analysis_id, "false_alarm", res)
                        st.success("Feedback saved to feedback.csv")
                    except Exception as e:
                        st.error(f"We couldn't save false-alarm feedback: {e}")

                liters_per_hour = round(res["leak_lpm"] * 60)
                liters_per_day = round(res["leak_lpm"] * 60 * 24)
                liters_per_month = round(res["leak_lpm"] * 60 * 24 * 30)
                liters_per_year = round(res["leak_lpm"] * 60 * 24 * 365)
                cost_per_day = round(res["leak_lpm"] * WATER_COST_PER_LITER * 60 * 24, 2)
                cost_per_month = round(res["leak_lpm"] * WATER_COST_PER_LITER * 60 * 24 * 30)
                cost_per_year = round(res["leak_lpm"] * WATER_COST_PER_LITER * 60 * 24 * 365)
                sig_label = significance_level(res["total_liters"])
                st.markdown(f"""
                <div class="env-card">
                    <h4>🌍 Environmental & financial impact</h4>
                    <div class="env-stat"><div class="num">{res['students_count']}</div><div class="lbl">students' daily drinking water lost so far</div></div>
                    <div class="env-stat"><div class="num">{liters_per_hour:,} L</div><div class="lbl">lost per hour if left unfixed</div></div>
                    <div class="env-stat"><div class="num">{liters_per_day:,} L</div><div class="lbl">lost per day if left unfixed</div></div>
                    <div class="env-stat"><div class="num">{liters_per_month:,} L</div><div class="lbl">lost per month if left unfixed</div></div>
                    <div class="env-stat"><div class="num">{liters_per_year:,} L</div><div class="lbl">lost per year if left unfixed</div></div>
                    <div class="env-stat"><div class="num">${cost_per_day:,}</div><div class="lbl">cost per day if ignored</div></div>
                    <div class="env-stat"><div class="num">${cost_per_month:,}</div><div class="lbl">cost per month if ignored</div></div>
                    <div class="env-stat"><div class="num">${cost_per_year:,}</div><div class="lbl">cost per year if ignored</div></div>
                    <div class="env-stat"><div class="num">{sig_label}</div><div class="lbl">environmental significance level</div></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="action-card" style="border-left:4px solid #3F8F5F;">
                    <div class="action-title">No action needed right now</div>
                    <div class="action-row">Water use stayed close to the learned normal profile. We'll keep watching and let you know if anything changes.</div>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# RESPONSIBLE AI NOTICE
# =============================================================================
st.markdown("""
    <div class="rai-card">
        <h4>⚖️ What this decision-support system can and can't do</h4>
        <div class="rai-item"><b>A model-based score, not a guess.</b> The confidence percentage is derived from the anomaly score produced by the IsolationForest model after it learns normal no-leak patterns across flow, pressure, and occupancy context.</div>
        <div class="rai-item"><b>A person always decides.</b> This system never shuts off water or contacts anyone automatically. Every alert needs a maintenance team member to review it and choose what to do — shutting off water during school hours can create its own safety and sanitation risks.</div>
        <div class="rai-item"><b>Known limitation.</b> Unusual but legitimate events can still look abnormal if the training data did not include similar no-leak examples. The model becomes more reliable as you retrain it on clean normal and event-day data.</div>
        <div class="rai-item"><b>How this prototype was validated.</b> This version trains on the bundled clean normal and event-day samples unless you provide your own no-leak training file. Every run is also written to logs.csv, and user reviews of alerts are written to feedback.csv to support future tuning.</div>
    </div>
    """, unsafe_allow_html=True)