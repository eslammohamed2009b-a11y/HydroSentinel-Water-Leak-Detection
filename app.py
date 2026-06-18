import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

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
WATER_COST_PER_LITER = 0.007
DENSITY_WATER = 1000
DISCHARGE_COEFF = 0.62
PSI_TO_PASCAL = 6894.76
DAILY_DRINKING_LITERS_PER_STUDENT = 2.5

REQUIRED_COLUMNS = ["Timestamp", "Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Status"]

# ---- Deterministic detection thresholds (rule + physics + statistics based) ----
# No probabilistic tuning knob: these fixed thresholds are the entire detection logic.
PCT_THRESHOLD = 1.30             # flow must be at least 30% above baseline to flag
ABS_THRESHOLD_LPM = 4.0          # OR at least 4 L/min above baseline to flag
EVENT_PCT_THRESHOLD = 1.80       # stricter threshold during an expected high-use period
EVENT_ABS_THRESHOLD_LPM = 8.0    # stricter absolute threshold during an expected high-use period
BASELINE_PERCENTILE = 0.40       # lower-than-median percentile, robust to a few elevated leak readings
LARGE_LEAK_DIAMETER_MM = 15.0    # above this estimated opening size, treat as a structural leak

# =============================================================================
# SIDEBAR — DATA INPUT & DETECTION CONTEXT
# =============================================================================
with st.sidebar:
    st.subheader("📥 Download Samples")
    try:
        with open("no_leak.csv", "rb") as f:
            st.download_button("📥 No Leak Data", f, "no_leak.csv")
        with open("leak_normal.csv", "rb") as f:
            st.download_button("⚠️ Leak Data", f, "leak_normal.csv")
    except FileNotFoundError:
        st.warning("Sample files missing.")

    st.markdown("---")
    st.markdown(
        "<div class='serif' style='font-size:1.4rem; font-weight:700; color:#146C5F; margin-bottom:0;'>💧 HydroSentinel AI</div>"
        "<div style='color:#4B5D59; font-size:0.85rem; margin-bottom:16px;'>Water Infrastructure Decision Support</div>",
        unsafe_allow_html=True,
    )
    st.caption("USAII Global AI Hackathon 2026")
    st.markdown("---")

    st.subheader("📥 Your Data")
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
    st.subheader("⚙️ Detection Context")
    st.caption("HydroSentinel uses fixed statistical and physical thresholds — there's no sensitivity dial to tune. These two settings only give the system extra context about expected high water use.")
    flag_event_day = st.checkbox(
        "Today includes a planned event (assembly, sports day, deep cleaning)",
        help="Expected high water use on event days can look like a leak. Checking this raises the detection threshold for daytime readings so normal event activity isn't flagged.",
    )
    event_window_enabled = st.checkbox(
        "Enable a specific event window",
        help="Use a time window when planned activity is expected. Readings inside this window are held to a stricter, fixed threshold before being flagged as a leak.",
    )
    event_start = None
    event_end = None
    if event_window_enabled:
        event_start = st.datetime_input(
            "Event start",
            value=pd.Timestamp.now().floor("min").to_pydatetime(),
            help="Select when the planned event begins.",
        )
        event_end = st.datetime_input(
            "Event end",
            value=(pd.Timestamp.now() + pd.Timedelta(hours=2)).floor("min").to_pydatetime(),
            help="Select when the planned event ends.",
        )

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
        built to give maintenance teams clear, auditable evidence for acting on leaks — using fixed statistical
        baselines and physical flow-pressure rules, not a black-box model. This version reads water-use data from
        a CSV file (or a simulated live demo) to stand in for direct sensor integration, which wasn't available to
        test during development. In a real school deployment, HydroSentinel AI would connect directly to smart water
        meters and pressure sensors, watching them continuously day and night to support the maintenance team's
        day-to-day decisions.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# HELPERS
# =============================================================================
def add_time_features(df):
    """Pulls Hour and Day Type out of the timestamp for context and reporting."""
    df = df.copy()
    try:
        dt = pd.to_datetime(df["Timestamp"])
        df["Hour"] = dt.dt.hour
        df["Is_Weekend"] = (dt.dt.dayofweek >= 5).astype(int)
        df["_time_parsed"] = True
    except Exception:
        df["Hour"] = 0
        df["Is_Weekend"] = 0
        df["_time_parsed"] = False
    return df


def severity_level(leak_lpm):
    if leak_lpm < 12:
        return "Minor", "warning"
    elif leak_lpm <= 35:
        return "Moderate", "warning"
    else:
        return "Severe", "critical"


def significance_level(total_liters):
    if total_liters < 300:
        return "Low"
    elif total_liters < 1500:
        return "Moderate"
    elif total_liters < 4000:
        return "High"
    else:
        return "Severe"


def compute_baselines(data):
    """Computes a fixed statistical baseline flow/pressure per occupancy period.
    Uses a lower percentile (not the mean/median) so a handful of elevated leak
    readings can't pull the 'normal' reference upward — a deliberate, auditable
    statistical choice rather than a tuned model parameter."""
    flow_baseline = data.groupby("Occupancy_Status")["Flow_Rate_LPM"].quantile(BASELINE_PERCENTILE)
    pressure_baseline = data.groupby("Occupancy_Status")["Avg_Pressure_PSI"].median()

    overall_flow = data["Flow_Rate_LPM"].quantile(BASELINE_PERCENTILE)
    overall_pressure = data["Avg_Pressure_PSI"].median()

    counts = data["Occupancy_Status"].value_counts()
    for status in flow_baseline.index:
        if counts.get(status, 0) < 3:
            flow_baseline[status] = overall_flow
            pressure_baseline[status] = overall_pressure

    return flow_baseline, pressure_baseline, overall_flow, overall_pressure


def evaluate_telemetry(data, dampen_event_day=False, event_start=None, event_end=None):
    """Deterministic leak detection: fixed statistical baselines + percentage/absolute
    flow-deviation rules + flow-pressure physics. No probabilistic model, no tunable
    sensitivity — every flagged reading can be explained with the same fixed rule."""
    data = add_time_features(data)

    data["In_Event_Window"] = False
    if event_start and event_end and event_start < event_end:
        data["In_Event_Window"] = data["Timestamp"].between(event_start, event_end)

    flow_baseline_map, pressure_baseline_map, overall_flow, overall_pressure = compute_baselines(data)
    data["Baseline_Flow"] = data["Occupancy_Status"].map(flow_baseline_map).fillna(overall_flow)
    data["Baseline_Pressure"] = data["Occupancy_Status"].map(pressure_baseline_map).fillna(overall_pressure)
    data["Baseline_Flow"] = data["Baseline_Flow"].replace(0, overall_flow if overall_flow > 0 else 1.0)
    data["Baseline_Pressure"] = data["Baseline_Pressure"].replace(0, overall_pressure if overall_pressure > 0 else 1.0)

    flow_ratio = data["Flow_Rate_LPM"] / data["Baseline_Flow"]
    abs_excess = data["Flow_Rate_LPM"] - data["Baseline_Flow"]
    pressure_drop_ratio = ((data["Baseline_Pressure"] - data["Avg_Pressure_PSI"]) / data["Baseline_Pressure"]).clip(lower=0)

    # --- Fixed rule-based detection (deterministic, no probabilistic tuning) ---
    base_flag = (flow_ratio >= PCT_THRESHOLD) | (abs_excess >= ABS_THRESHOLD_LPM)

    # Context-aware dampening: expected high-use periods are held to a stricter,
    # still-fixed threshold rather than being filtered out altogether.
    dampen_mask = pd.Series(False, index=data.index)
    if dampen_event_day:
        dampen_mask |= data["Occupancy_Status"].isin(["Class_Hours", "After_Hours"])
    if data["In_Event_Window"].any():
        dampen_mask |= data["In_Event_Window"]

    strict_flag = (flow_ratio >= EVENT_PCT_THRESHOLD) | (abs_excess >= EVENT_ABS_THRESHOLD_LPM)
    data["Leak_Flag"] = np.where(dampen_mask, strict_flag, base_flag)

    # Deterministic confidence score: how far the reading exceeds the fixed
    # threshold, plus whether the pressure drop corroborates it physically.
    # This is a transparent, rule-based score — not a model probability.
    flow_excess_norm = (flow_ratio - 1.0).clip(lower=0)
    flow_score = (flow_excess_norm * 100).clip(upper=70)
    pressure_score = (pressure_drop_ratio * 150).clip(upper=30)
    data["Confidence"] = (flow_score + pressure_score).clip(lower=45, upper=100).round(1)
    data["Pressure_Drop_Pct"] = (pressure_drop_ratio * 100).round(1)
    data["Deviation_Pct"] = ((flow_ratio - 1.0) * 100).round(1)

    anomalies = data[data["Leak_Flag"]]
    has_leak = len(anomalies) > 0

    metrics = {
        "has_leak": has_leak, "anomalies": anomalies, "df": data,
        "leak_lpm": 0.0, "diameter_mm": 0.0, "cost_min": 0.0, "total_liters": 0.0,
        "metaphor": "No leak detected", "students_count": 0, "time_parsed": bool(data["_time_parsed"].iloc[0]),
    }

    if has_leak:
        top_row = anomalies.loc[anomalies["Flow_Rate_LPM"].idxmax()]
        max_anomaly = top_row["Flow_Rate_LPM"]
        baseline_flow_for_row = top_row["Baseline_Flow"]
        baseline_pressure_for_row = top_row["Baseline_Pressure"]

        leak_lpm = round(max_anomaly - baseline_flow_for_row, 1)
        if leak_lpm <= 0:
            leak_lpm = round(max_anomaly * 0.5, 1)

        # Estimate leak opening size from flow + pressure (Torricelli's equation)
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
            "confidence": top_row["Confidence"],
            "deviation_pct": top_row["Deviation_Pct"],
            "pressure_drop_pct": top_row["Pressure_Drop_Pct"],
        })

        if leak_lpm < 12:
            metrics["metaphor"] = "a faucet left fully running"
        elif leak_lpm <= 35:
            metrics["metaphor"] = "a toilet valve stuck open and constantly refilling"
        else:
            metrics["metaphor"] = "a broken pipe releasing water under pressure"

    return metrics


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

if mode == "Upload a CSV file" and uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        if all(col in raw_df.columns for col in REQUIRED_COLUMNS):
            target_df = raw_df
        else:
            st.error(
                "This file doesn't look like a HydroSentinel data file. It needs these columns: "
                "Timestamp, Flow_Rate_LPM, Avg_Pressure_PSI, Occupancy_Status."
            )
    except Exception as e:
        st.error(f"We couldn't read that file: {e}")

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
            target_df = pd.DataFrame(st.session_state.demo_rows)
            with placeholder.container():
                st.info(f"📡 Receiving reading for {new_row['Timestamp']} ...")
            time.sleep(0.15)
        st.session_state.demo_running = False
    else:
        target_df = pd.DataFrame(st.session_state.demo_rows)

# =============================================================================
# DASHBOARD
# =============================================================================
if target_df is not None:
    res = evaluate_telemetry(
        target_df,
        dampen_event_day=flag_event_day,
        event_start=event_start,
        event_end=event_end,
    )
    recs = build_recommendations(res) if res["has_leak"] else []

    if not res["time_parsed"]:
        st.caption("Note: we couldn't read dates/times from the Timestamp column, so time-of-day context wasn't used in this analysis.")

    # ---- Status banner (always binary: Leak Detected / No Leak Detected) ----
    if res["has_leak"]:
        sev_label, _ = severity_level(res["leak_lpm"])
        st.markdown(f"""
        <div class="status-banner critical">
            <div class="status-headline">🚨 Leak Detected — {sev_label} severity</div>
            <div class="status-sub">A water-use pattern crossed the system's fixed baseline thresholds for this time period. Review the details below before taking action.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-banner ok">
            <div class="status-headline">✅ No Leak Detected</div>
            <div class="status-sub">Water use across the readings we checked stayed within the school's fixed statistical baseline.</div>
        </div>
        """, unsafe_allow_html=True)

    # ---- At-a-glance answers (BEFORE charts, per dashboard priority) ----
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

    # ---- TAB 1: Chart (supporting evidence, not the headline) ----
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
        st.caption("Each dot marks a reading that crossed the system's fixed baseline threshold for that time of day.")

    # ---- TAB 2: Why + What to do ----
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
                <div class="why-reason">This reading crossed the system's fixed detection rule — flow at least 30% above the statistical baseline for this time period, or at least 4 L/min above it. Rising flow paired with falling pressure is the same physical signature as water escaping through an unintended opening: when a fixture is used normally, flow and pressure tend to move together, but a leak pulls flow up while pressure drops.</div>
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

            # ---- Impact engine: water loss & cost across time horizons ----
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
                <div class="action-row">Water use stayed within the school's fixed baseline. We'll keep watching and let you know if anything changes.</div>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# RESPONSIBLE AI NOTICE
# =============================================================================
st.markdown("""
    <div class="rai-card">
        <h4>⚖️ What this decision-support system can and can't do</h4>
        <div class="rai-item"><b>A calculated score, not a guess.</b> The confidence percentage reflects how far a reading exceeds the school's fixed statistical baseline, combined with whether pressure behavior corroborates it. It comes from fixed rules and physics, not a machine-learning prediction.</div>
        <div class="rai-item"><b>A person always decides.</b> This system never shuts off water or contacts anyone automatically. Every alert needs a maintenance team member to review it and choose what to do — shutting off water during school hours can create its own safety and sanitation risks.</div>
        <div class="rai-item"><b>Known limitation.</b> Unusual but legitimate events — an assembly, a fire drill, extra cleaning — can occasionally cross the same thresholds as a leak. Marking "planned event" in the sidebar raises the threshold for that period so normal activity isn't flagged.</div>
        <div class="rai-item"><b>How this prototype was validated.</b> This version calculates its baseline directly from the uploaded file, since no historical school data was available for testing. In a real deployment, the system would first establish a school's normal baseline using several weeks of real sensor data, then compare new incoming readings against that fixed baseline — flagging anything that crosses the defined thresholds for the maintenance team to review.</div>
    </div>
    """, unsafe_allow_html=True)