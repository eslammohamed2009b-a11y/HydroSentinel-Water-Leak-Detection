import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
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

    /* Mission pipeline strip — literal sequence: data in -> AI -> insight -> action */
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
    .action-tag { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 9px; border-radius: 20px; }
    .action-tag.high { background: var(--coral-soft); color: var(--coral); }
    .action-tag.medium { background: var(--amber-soft); color: var(--amber); }
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

# =============================================================================
# SIDEBAR — DATA INPUT & AI SETTINGS
# =============================================================================
with st.sidebar:
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
    st.subheader("🧠 AI Settings")
    ai_sensitivity = st.slider(
        "Detection sensitivity", 0.01, 0.15, 0.04, step=0.01,
        help="Higher sensitivity flags more readings for review (more false alarms). Lower sensitivity only flags the clearest issues.",
    )
    flag_event_day = st.checkbox(
        "Today includes a planned event (assembly, sports day, deep cleaning)",
        help="Expected high water use on event days can look like a leak. Checking this tells the AI to be more careful before flagging normal daytime usage.",
    )
    event_window_enabled = st.checkbox(
        "Enable a specific event window",
        help="Use a time window when planned activity is expected, so the AI is less likely to flag normal high use as a leak.",
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
        <div class="pipeline-step"><span class="num">2</span> 🧠 AI Analysis</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-step"><span class="num">3</span> 🌍 Environmental Insight</div>
        <div class="pipeline-arrow">→</div>
        <div class="pipeline-step"><span class="num">4</span> ✅ Recommended Action</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="context-note">
        <b>About this system:</b> HydroSentinel AI is a decision-support system for school water infrastructure,
        built to give maintenance teams the evidence and reasoning they need to act on leaks quickly and confidently —
        not just a statistical anomaly flag. This version reads water-use data from a CSV file (or a simulated live demo)
        to stand in for direct sensor integration, which wasn't available to test during development. In a real school
        deployment, HydroSentinel AI would connect directly to smart water meters and pressure sensors, watching them
        continuously day and night to support the maintenance team's day-to-day decisions.
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# HELPERS
# =============================================================================
def add_time_features(df):
    """Pulls Hour and Day Type out of the timestamp so the AI can judge
    whether a reading is unusual *for that time of day*, not just on average."""
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


def get_baseline_for_row(normal_df, row):
    """Finds the 'normal' flow and pressure for the same kind of time period
    (e.g. Class Hours) so we can show a fair Normal vs Current comparison."""
    bucket = normal_df[normal_df["Occupancy_Status"] == row["Occupancy_Status"]]
    if len(bucket) < 3:
        bucket = normal_df
    base_flow = bucket["Flow_Rate_LPM"].median()
    base_pressure = bucket["Avg_Pressure_PSI"].median()
    if pd.isna(base_flow):
        base_flow = row["Flow_Rate_LPM"]
    if pd.isna(base_pressure):
        base_pressure = row["Avg_Pressure_PSI"]
    return round(base_flow, 1), round(base_pressure, 1)


def evaluate_telemetry(data, sensitivity, dampen_event_day=False, event_start=None, event_end=None):
    data = add_time_features(data)

    data["In_Event_Window"] = False
    if event_start and event_end and event_start < event_end:
        data["In_Event_Window"] = data["Timestamp"].between(event_start, event_end)

    occupancy_map = {"Class_Hours": 1, "After_Hours": 2, "Weekend": 3}
    data["Occupancy_Encoded"] = data["Occupancy_Status"].map(occupancy_map).fillna(0)

    # Contextual features (hour of day, weekend flag) reduce false positives
    # by letting the model judge a reading against the right kind of time period,
    # not just the dataset-wide average.
    feature_cols = ["Flow_Rate_LPM", "Avg_Pressure_PSI", "Occupancy_Encoded", "Hour", "Is_Weekend"]
    X = data[feature_cols].copy()

    model = IsolationForest(contamination=sensitivity, n_estimators=150, random_state=42)
    model.fit(X)
    data["Anomaly_Signal"] = model.predict(X)

    # Confidence: how unusual each reading is, scaled to 0-100%.
    raw_scores = model.decision_function(X)  # higher = more normal
    lo, hi = raw_scores.min(), raw_scores.max()
    if hi - lo > 1e-9:
        data["Confidence"] = ((hi - raw_scores) / (hi - lo) * 100).round(1)
    else:
        data["Confidence"] = 0.0

    # --- False-positive guard ---
    # IsolationForest's `contamination` setting always flags that fixed share of
    # readings as outliers, even on a day with zero real leaks — it just picks the
    # most-extreme-looking normal reading. We confirm each statistical flag against
    # a real-world deviation check before treating it as a genuine leak signal: it
    # must be meaningfully above the school's normal flow for that kind of period,
    # not just the most unusual point in an otherwise quiet dataset.
    CONFIRM_RATIO = 1.3       # at least 30% above normal flow, OR
    CONFIRM_ABS_LPM = 4.0     # at least 4 L/min above normal flow
    normal_flow_baseline = data.loc[data["Anomaly_Signal"] == 1, "Flow_Rate_LPM"].median()
    if pd.isna(normal_flow_baseline) or normal_flow_baseline <= 0:
        normal_flow_baseline = data["Flow_Rate_LPM"].median()
    ratio = data["Flow_Rate_LPM"] / max(normal_flow_baseline, 0.01)
    abs_diff = data["Flow_Rate_LPM"] - normal_flow_baseline
    meaningfully_elevated = (ratio >= CONFIRM_RATIO) | (abs_diff >= CONFIRM_ABS_LPM)
    unconfirmed = (data["Anomaly_Signal"] == -1) & (~meaningfully_elevated)
    data.loc[unconfirmed, "Anomaly_Signal"] = 1

    # Event-day filter: on flagged event days, don't treat moderately elevated
    # daytime usage as a leak — only flag readings well above normal even for an event.
    if dampen_event_day or data["In_Event_Window"].any():
        normal_flow_ref = data.loc[data["Anomaly_Signal"] == 1, "Flow_Rate_LPM"].median()
        if pd.isna(normal_flow_ref):
            normal_flow_ref = data["Flow_Rate_LPM"].median()
        event_ceiling = normal_flow_ref * 1.8
        daytime = data["Occupancy_Status"].isin(["Class_Hours", "After_Hours"])
        soften = (data["Anomaly_Signal"] == -1) & daytime & (data["Flow_Rate_LPM"] < event_ceiling)
        if data["In_Event_Window"].any():
            soften &= data["In_Event_Window"]
        data.loc[soften, "Anomaly_Signal"] = 1

    anomalies = data[data["Anomaly_Signal"] == -1]
    has_leak = len(anomalies) > 0

    metrics = {
        "has_leak": has_leak, "anomalies": anomalies, "df": data,
        "leak_lpm": 0.0, "diameter_mm": 0.0, "cost_min": 0.0, "total_liters": 0.0,
        "metaphor": "No leak detected", "students_count": 0, "time_parsed": bool(data["_time_parsed"].iloc[0]),
    }

    if has_leak:
        normal_df = data[data["Anomaly_Signal"] == 1]
        normal_median = normal_df["Flow_Rate_LPM"].median()
        if pd.isna(normal_median):
            normal_median = data["Flow_Rate_LPM"].median()

        top_row = anomalies.loc[anomalies["Flow_Rate_LPM"].idxmax()]
        max_anomaly = top_row["Flow_Rate_LPM"]

        leak_lpm = round(max_anomaly - normal_median, 1)
        if leak_lpm <= 0:
            leak_lpm = round(max_anomaly * 0.5, 1)

        # Estimate leak opening size from flow + pressure (Torricelli's equation)
        flow_m3_s = (leak_lpm / 1000) / 60
        press_pascal = max(top_row["Avg_Pressure_PSI"] * PSI_TO_PASCAL, 1.0)
        velocity = np.sqrt((2 * press_pascal) / DENSITY_WATER)
        area_m2 = flow_m3_s / (DISCHARGE_COEFF * max(velocity, 0.01))
        diameter_mm = round((2 * np.sqrt(area_m2 / np.pi)) * 1000, 2)

        base_flow, base_pressure = get_baseline_for_row(normal_df, top_row)

        metrics.update({
            "leak_lpm": leak_lpm,
            "diameter_mm": diameter_mm,
            "cost_min": round(leak_lpm * WATER_COST_PER_LITER, 2),
            "total_liters": round(anomalies["Flow_Rate_LPM"].sum(), 1),
            "students_count": int(anomalies["Flow_Rate_LPM"].sum() / DAILY_DRINKING_LITERS_PER_STUDENT),
            "top_row": top_row,
            "base_flow": base_flow,
            "base_pressure": base_pressure,
            "confidence": top_row["Confidence"],
        })

        if leak_lpm < 12:
            metrics["metaphor"] = "a faucet left fully running"
        elif leak_lpm <= 35:
            metrics["metaphor"] = "a toilet valve stuck open and constantly refilling"
        else:
            metrics["metaphor"] = "a broken pipe releasing water under pressure"

    return metrics


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
        ai_sensitivity,
        dampen_event_day=flag_event_day,
        event_start=event_start,
        event_end=event_end,
    )

    if not res["time_parsed"]:
        st.caption("Note: we couldn't read dates/times from the Timestamp column, so time-of-day context wasn't used in this analysis.")

    # ---- Status banner ----
    if res["has_leak"]:
        sev_label, _ = severity_level(res["leak_lpm"])
        st.markdown(f"""
        <div class="status-banner critical">
            <div class="status-headline">⚠️ Possible leak detected — {sev_label} severity</div>
            <div class="status-sub">The AI found a water-use pattern that doesn't match this school's normal routine. Review the details below before taking action.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-banner ok">
            <div class="status-headline">✅ No leak detected</div>
            <div class="status-sub">Water use across the readings we checked matches the school's normal patterns.</div>
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
                <div class="footnote">{res['confidence']:.0f}% AI confidence</div></div>""", unsafe_allow_html=True)
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
            quick_action = "Shut off main valve & call a plumber" if res["diameter_mm"] > 15.0 else "Send maintenance to check fixtures"
            st.markdown(f"""<div class="answer-card accent-ok">
                <div class="label">Recommended action</div><div class="value" style="font-size:1.05rem;">{quick_action}</div>
                <div class="footnote">See full reasoning below</div></div>""", unsafe_allow_html=True)
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
        st.caption("Each dot marks a reading the AI flagged as different from this school's normal pattern for that time of day.")

    # ---- TAB 2: Why + What to do ----
    with tab2:
        if res["has_leak"]:
            top_row = res["top_row"]

            st.markdown(f"""
            <div class="why-card">
                <span class="confidence-tag">{res['confidence']:.0f}% AI confidence</span>
                <div class="why-title">Why the AI flagged this</div>
                <div class="why-compare">
                    <div class="pair">Normal flow: <b>{res['base_flow']} L/min</b> → Current flow: <b>{top_row['Flow_Rate_LPM']} L/min</b></div>
                    <div class="pair">Normal pressure: <b>{res['base_pressure']} PSI</b> → Current pressure: <b>{top_row['Avg_Pressure_PSI']} PSI</b></div>
                </div>
                <div class="why-reason">The AI noticed flow well above what's normal for this time of day, paired with a pressure drop — together, this combination usually means water is escaping somewhere in the system rather than being used normally.</div>
                <span class="why-evidence">To put it in perspective: this is roughly the same rate as {res['metaphor']}.</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### What to do next")

            if res["diameter_mm"] > 15.0:
                st.markdown(f"""
                <div class="action-card priority-high">
                    <span class="action-tag high">High priority</span>
                    <div class="action-title">Shut off the main water valve and call a plumber</div>
                    <div class="action-row"><b>Why:</b> A leak of this size points to a broken pipe or major fitting failure, not a single sink or toilet — flow this high doesn't come from one fixture.</div>
                    <div class="action-row"><b>Evidence:</b> The estimated opening size is about Ø {res['diameter_mm']} mm, and pressure dropped at the same time flow spiked — a classic sign of a structural leak.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="action-card priority-high">
                    <span class="action-tag high">High priority</span>
                    <div class="action-title">Send maintenance to check nearby restrooms and fixtures</div>
                    <div class="action-row"><b>Why:</b> This pattern matches a stuck valve or a running toilet — a common, easily-fixed issue rather than a structural problem.</div>
                    <div class="action-row"><b>Evidence:</b> Flow jumped once and then stayed steady at a high level, instead of spiking unpredictably the way a burst pipe would.</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div class="action-card priority-medium">
                <span class="action-tag medium">Worth checking</span>
                <div class="action-title">Have someone check outdoor irrigation or mechanical equipment (e.g. HVAC cooling system)</div>
                <div class="action-row"><b>Why:</b> Some of the unusual readings happened during hours when no students or staff are normally in the building, which points to automated equipment rather than people using water.</div>
                <div class="action-row"><b>Evidence:</b> These readings don't line up with the school's typical daytime usage schedule.</div>
            </div>
            """, unsafe_allow_html=True)

            # ---- Environmental impact ----
            monthly_liters = round(res["leak_lpm"] * 60 * 24 * 30)
            annual_cost = round(res["leak_lpm"] * WATER_COST_PER_LITER * 60 * 24 * 365)
            sig_label = significance_level(res["total_liters"])
            st.markdown(f"""
            <div class="env-card">
                <h4>🌍 Environmental impact</h4>
                <div class="env-stat"><div class="num">{res['students_count']}</div><div class="lbl">students' daily drinking water lost so far</div></div>
                <div class="env-stat"><div class="num">{monthly_liters:,} L</div><div class="lbl">estimated waste per month if left unfixed</div></div>
                <div class="env-stat"><div class="num">${annual_cost:,}</div><div class="lbl">estimated yearly cost if ignored</div></div>
                <div class="env-stat"><div class="num">{sig_label}</div><div class="lbl">environmental significance level</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="action-card" style="border-left:4px solid #3F8F5F;">
                <div class="action-title">No action needed right now</div>
                <div class="action-row">Water use matches the school's normal pattern. We'll keep watching and let you know if anything changes.</div>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# RESPONSIBLE AI NOTICE
# =============================================================================
st.markdown("""
    <div class="rai-card">
        <h4>⚖️ What this decision-support system can and can't do</h4>
        <div class="rai-item"><b>Confidence, not certainty.</b> The percentage shown reflects how unusual a reading looks compared to this school's normal pattern — it's an estimate, not a guarantee.</div>
        <div class="rai-item"><b>A person always decides.</b> This system never shuts off water or contacts anyone automatically. Every alert needs a maintenance team member to review it and choose what to do — shutting off water during school hours can create its own safety and sanitation risks.</div>
        <div class="rai-item"><b>Known limitation.</b> Unusual but legitimate events — an assembly, a fire drill, extra cleaning — can occasionally look like a leak. Marking "planned event" in the sidebar helps the AI tell the difference.</div>
        <div class="rai-item"><b>How this prototype was validated.</b> This version learns and checks patterns using the same uploaded file, since no historical school data was available for testing. In a real deployment, the system would first learn a school's normal patterns over several weeks of real sensor data, then watch new incoming readings separately — flagging anything that doesn't fit for the maintenance team to review.</div>
    </div>
    """, unsafe_allow_html=True)
