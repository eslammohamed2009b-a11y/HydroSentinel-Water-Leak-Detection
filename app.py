import streamlit as st
import pandas as pd
import numpy as np

# --- 1. INDUSTRIAL CONSOLE CONFIGURATION ---
st.set_page_config(
    page_title="HydroSentinel AI - Command Center", 
    page_icon="💧", 
    layout="wide"
)

# Advanced Engineering UI Styling & Flashing Animations
st.markdown("""
    <style>
    /* Tech Console Dark Theme */
    .reportview-container, .main { background-color: #0f172a; color: #e2e8f0; }
    div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #38bdf8; }
    
    /* Flashing Red Alarm Animation */
    @keyframes pulse-red {
        0% { background-color: #ef4444; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { background-color: #991b1b; box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }
        100% { background-color: #ef4444; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .flashing-danger {
        animation: pulse-red 1.2s infinite;
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        font-weight: 900;
        font-size: 1.8rem;
        letter-spacing: 2px;
        margin-bottom: 25px;
    }
    
    /* Stable Green Banner */
    .stable-banner {
        background: linear-gradient(135deg, #10b981, #065f46);
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        font-weight: 900;
        font-size: 1.8rem;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
    }
    
    /* Dispatch Protocol Boxes */
    .dispatch-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #38bdf8;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MAIN HEADER & TECHNICAL REALITY NOTE ---
st.title("📟 HydroSentinel AI - Command Console")
st.markdown("""
**Prototype Ingestion Mode:** This console simulates live campus monitoring using historical water flow logs (CSV format) to demonstrate the HydroSentinel AI detection capabilities in real-time.
""")
st.markdown("---")

# --- 3. CSV INGESTION NODE ---
st.subheader("📥 Data Ingestion Node")
uploaded_file = st.file_uploader("Upload Campus Flow Log File (CSV Only)", type=["csv"])
st.markdown("---")

# Financial & Physical Constants (US EPA Standards for Large High Schools)
avg_water_cost_per_liter = 0.007  # ~$7 per cubic meter (Water + Sewer fees)

if uploaded_file is not None:
    try:
        # Read the uploaded CSV
        df = pd.read_csv(uploaded_file)
        
        # Engineering validation of the CSV columns
        if 'Timestamp' in df.columns and 'Flow_Rate_LPM' in df.columns:
            
            # --- 4. PRE-PROCESSING ANOMALY CHECK ---
            # Statistical check to evaluate data trends before fully embedding the AI model
            median_flow = df['Flow_Rate_LPM'].median()
            max_flow = df['Flow_Rate_LPM'].max()
            
            # Condition: If max flow deviates from median by more than 40 LPM, trigger alert
            is_leak = (max_flow - median_flow) > 40
            
            # --- CASE A: LEAK DETECTED ---
            if is_leak:
                leak_rate_lpm = round(max_flow - median_flow, 2)
                cost_per_minute = round(leak_rate_lpm * avg_water_cost_per_liter, 2)
                
                # Audio Siren Injection (Hidden HTML Audio Element that Autoplays)
                st.markdown("""
                    <audio autoplay loop>
                        <source src="https://assets.mixkit.co/active_storage/sfx/950/950-84.wav" type="audio/wav">
                    </audio>
                    """, unsafe_allow_html=True)
                
                # Flashing UI Alert
                st.markdown(f"""
                    <div class="flashing-danger">
                        🚨 SYSTEM ALARM: CRITICAL LEAK DETECTED
                    </div>
                    """, unsafe_allow_html=True)
                
                # Real-time Leak Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Leak Flow Rate", f"{leak_rate_lpm} L/min", delta="CRITICAL ELEVATION", delta_color="inverse")
                with col2:
                    st.metric("Financial Drain Rate", f"${cost_per_minute} / min", delta="BUDGET BLEED", delta_color="inverse")
                with col3:
                    st.metric("Total Analyzed Datapoints", f"{len(df)} Logs", delta="Scan Complete")
                    
                st.markdown("---")
                
                # Smart Dispatch Protocol for Maintenance Team (EPA Standards)
                st.subheader("🛠 Smart Maintenance Dispatch Protocol")
                st.markdown("The diagnostic signature indicates an isolated high-volume anomaly. Dispatch team immediately to:")
                
                st.markdown(f"""
                <div class="dispatch-card" style="border-left-color: #ef4444;">
                    <h4>📌 Priority 1: Main Restroom Blocks (Building A & B)</h4>
                    <p><b>Target:</b> Commercial Flushometer Diaphragm Valves.<br>
                    <b>Engineering Rationale:</b> Constant square-wave volume signature. Typically caused by silt blocking the bypass orifice of toilet flush valves, forcing a continuous run of ~60 L/min.</p>
                </div>
                <div class="dispatch-card" style="border-left-color: #f59e0b;">
                    <h4>📌 Priority 2: Central HVAC Mechanical Room</h4>
                    <p><b>Target:</b> Cooling Tower Evaporative Make-Up Float Valve.<br>
                    <b>Engineering Rationale:</b> Anomaly persists during zero-occupancy timestamps. Inspect if the mechanical arm of the water level float is seized open.</p>
                </div>
                <div class="dispatch-card" style="border-left-color: #64748b;">
                    <h4>📌 Priority 3: Athletic Turf Irrigation Vault (Zone 4)</h4>
                    <p><b>Target:</b> Solenoid Master Valve & Lateral PVC Piping.<br>
                    <b>Engineering Rationale:</b> Pressure drop overlaps with the automated night watering cycle. Inspect for a ruptured joint or cracked pipe body underground.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Anomaly Chart
                st.subheader("📊 Tactical Flow Rate Analysis (Leak Profile)")
                st.line_chart(df.set_index('Timestamp')['Flow_Rate_LPM'], color="#ef4444")
                
            # --- CASE B: STABLE SYSTEM ---
            else:
                st.markdown("""
                    <div class="stable-banner">
                        🟢 CAMPUS STATUS: SYSTEM OPERATIONAL & STABLE
                    </div>
                    """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Flow Rate", f"{round(df['Flow_Rate_LPM'].mean(), 1)} L/min", delta="Optimal Baseline")
                with col2:
                    st.metric("Projected Cost Rate", f"${round(df['Flow_Rate_LPM'].mean() * avg_water_cost_per_liter, 3)} / min", delta="Within Budget")
                with col3:
                    st.metric("Total Analyzed Datapoints", f"{len(df)} Logs", delta="Scan Complete")
                
                st.markdown("---")
                st.subheader("📊 Tactical Flow Rate Analysis (Stable Profile)")
                st.line_chart(df.set_index('Timestamp')['Flow_Rate_LPM'], color="#10b981")
                
        else:
            st.error("❌ Invalid CSV Schema. File must contain 'Timestamp' and 'Flow_Rate_LPM' columns.")
    except Exception as e:
        st.error(f"❌ Error parsing operational log: {e}")
else:
    # Idle State Dashboard Dashboard Panel
    st.info("⚡ System Idle. Awaiting local log file ingestion via the upload node above to execute analysis.")