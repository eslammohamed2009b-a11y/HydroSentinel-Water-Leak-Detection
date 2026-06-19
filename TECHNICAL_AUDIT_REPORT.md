# HydroSentinel-AI Engineering Audit (Deep Dive)

Date: 2026-06-19  
Project: HydroSentinel-AI  
Audit Type: Engineering Deep Dive for Judges  
System Role: Decision Support (Human-in-the-loop)

## 1) Scope And Verification Summary

This audit was performed against the running codebase and actual datasets in the repository.  
Verification executed after UI and report updates:

- Unit tests: `python test_system.py -v` -> PASS (3/3)
- Syntax/compile checks: `python -m py_compile app.py ml_engine.py generate_data.py generate_data_new.py contextual_rules.py test_system.py` -> PASS

Integration status:
- Data UI Integration -> PASS (download buttons added for all 4 simulation CSV files)
- ML pipeline + UI adapter + JSON contract -> PASS
- Event-mode path + normal path -> PASS

---

## 2) Data UI Integration (Simulation Data Downloads)

Implemented in Streamlit UI:
- Added `st.download_button` for:
  - `normal.csv`
  - `event.csv`
  - `event_leak.csv`
  - `example_normal_day_2026-10-05.csv`
- Buttons explicitly labeled as: `Simulation Data`
- Tooltip text clarifies these files are synthetic IoT-like telemetry used for demo and validation.

Engineering intent:
- Judges can directly inspect the exact data used by the models.
- Supports transparency and reproducibility.
- Reinforces that data source is simulated (not live hardware sensors).

---

## 3) Data Generation Deep Dive (CSV + Simulation)

### 3.1 Canonical Telemetry Schema

All primary CSV inputs are structured around 4 fields:

- `Timestamp` (datetime string)
- `Flow_Rate_LPM` (float, liters per minute)
- `Avg_Pressure_PSI` (float, PSI)
- `Occupancy_Status` (categorical string)

Validation constraints in code enforce:
- Required columns present
- `Flow_Rate_LPM` numeric and within `[0, 500]`
- `Avg_Pressure_PSI` numeric and within `(0, 150]`
- `Occupancy_Status` in `{Class_Hours, After_Hours, Vacation, Event}`

### 3.2 Actual Dataset Profiles (Observed In Repository)

#### `normal.csv`
- Rows: 24
- Time span: 2026-06-01 00:00:00 -> 2026-06-01 23:00:00
- Flow: min 14.0, max 15.7, avg 14.70
- Pressure: min 49.6, max 50.8, avg 50.32
- Status distribution: `After_Hours:13`, `Class_Hours:11`

#### `event.csv`
- Rows: 24
- Time span: 2026-06-01 00:00:00 -> 2026-06-01 23:00:00
- Flow: min 14.1, max 20.0, avg 16.01
- Pressure: min 49.2, max 50.7, avg 50.06
- Status distribution: `After_Hours:13`, `Class_Hours:11`

#### `event_leak.csv`
- Rows: 24
- Time span: 2026-06-01 00:00:00 -> 2026-06-01 23:00:00
- Flow: min 17.2, max 23.5, avg 20.55
- Pressure: min 45.1, max 49.8, avg 47.54
- Status distribution: `After_Hours:13`, `Class_Hours:11`

#### `example_normal_day_2026-10-05.csv`
- Raw rows: 26
- Contains two comment lines beginning with `#` (non-data lines)
- Effective telemetry rows after validation: 24
- Time span of valid telemetry: 2026-10-05 00:00:00 -> 2026-10-05 23:00:00
- Pattern includes a deliberate mid-day non-leak event bump and post-event return to baseline

### 3.3 Synthetic Generation Strategy In Code

Two generation scripts exist:

#### `generate_data.py`
- Annual calendar over 2026
- Encodes school seasonality (summer/winter breaks)
- Baseline logic by context:
  - School weekdays: higher flow, stable pressure
  - Weekends/breaks: lower flow, lower activity
- Supports injected leak scenarios (`leak_normal`, `leak_event`) by:
  - Increasing flow sharply
  - Dropping pressure to emulate hydraulic stress

#### `generate_data_new.py`
- Academic-year frame (2026-08-01 to 2027-07-31)
- Explicit break windows (winter/spring/summer transitions)
- Gaussian-distributed baseline with clipping
- Optional leak-day injections with stronger event leak profile

### 3.4 Why This Simulation Is Technically Defensible

Because real sensors are absent in this stage, synthetic data emulates physically plausible telemetry under controlled scenarios:
- Normal school behavior (class vs after-hours)
- Event-driven legitimate demand increase
- Leak signatures represented by flow-pressure mismatch

This lets the team:
- Train and benchmark models now
- Reproduce judge-facing results deterministically
- Transition later to live IoT streams with minimal interface change (same schema)

---

## 4) Tech Stack And Libraries

Core runtime dependencies (`requirements.txt`):

- `streamlit`: Web UI framework for operator and executive dashboards
- `pandas`: CSV ingestion, cleaning, transformation, tabular analytics
- `numpy`: numeric operations, random sampling, clipping, quantiles
- `scikit-learn`: ML models and pipelines (IsolationForest, RandomForest, preprocessing)
- `plotly`: interactive charts (time-series flow + anomaly markers)
- `joblib`: model artifact serialization/deserialization

Also used from Python stdlib:
- `pathlib`: robust path handling
- `json`: API-ready payload serialization
- `hashlib`: deterministic analysis/model fingerprints
- `io`: in-memory upload file handling

---

## 5) AI Design: ML vs Hard-coded Rules

HydroSentinel uses a model-driven approach instead of rigid `if/else` thresholds.

### 5.1 Why `if/else` Is Insufficient

Hard-coded rules fail in school contexts because:
- Baselines shift by occupancy mode and season
- Events produce legitimate high usage spikes
- Same flow value can be normal in one context and abnormal in another

Example failure mode:
- Rule: `if flow > 18 then leak`
- During school event, 18-20 LPM can be normal -> false alarms

### 5.2 Model Approach In HydroSentinel

- `Isolation Forest` concept is retained in architecture for anomaly reasoning lineage.
- Current production scoring path is diagnostic and supervised:
  - `RandomForestClassifier` predicts leak type (`no_leak`, `fixture_leak`, `valve_failure`, `mainline_break`)
  - `LinearRegression` estimates leak-loss LPM

Advantages over rules:
- Learns nonlinear interactions between flow + pressure + occupancy + time features
- Handles distribution drift better than fixed thresholds
- Produces confidence scores and class probabilities
- Provides interpretable feature importance for reasoning narratives

---

## 6) Physics-Based Insight (Water Loss + Cost)

The system transforms leak-rate predictions into practical operational metrics.

Let $L$ be leak rate in liters/min.

### 6.1 Water Loss Conversion

$$
\text{Liters per hour} = L \times 60
$$

$$
\text{m}^3\text{/hour} = \frac{L \times 60}{1000}
$$

### 6.2 Cost Conversion

Using configured tariff:
- `WATER_COST_PER_M3 = 0.50`

$$
\text{Cost/hour} = \frac{L \times 60}{1000} \times 0.50
$$

Monthly projection in engine:

$$
\text{Cost/month} = \text{Cost/hour} \times 24 \times 30
$$

This physics-to-economics chain is critical for decision support because it converts signal anomalies into maintenance priority language.

---

## 7) Environmental Impact Logic (Water Carbon Footprint)

HydroSentinel models water-related carbon impact from two components:

1) Treatment factor (kgCO2e per m3)  
2) Energy factor from pumping/treatment (`kWh per m3`) multiplied by grid emission intensity (`kgCO2e per kWh`)

Constants in engine:
- `WATER_TREATMENT_ENERGY_KWH_PER_M3 = 0.45`
- `GRID_EMISSION_KGCO2_PER_KWH = 0.42`
- Treatment term used in one path: `0.19 kgCO2e/m3`

Representative formula:

$$
\text{CO2e} = m^3 \times 0.19 + m^3 \times 0.45 \times 0.42
$$

This quantifies climate impact of non-revenue water loss and makes sustainability impact explicit in maintenance decisions.

---

## 8) Event Mode Logic (Scientific False-Positive Control)

Event Mode is not cosmetic; it modifies inference behavior:

1) Training context selection:
- If Event Mode is ON, training labels loading includes event telemetry context alongside normal context.
- If OFF, baseline stays closer to regular-day patterns.

2) Inference-time guardrail:
- When Event Mode is OFF, event-status rows require higher confidence (`Leak_Probability >= 80`) to remain flagged.
- This suppresses low-confidence event spikes that are likely legitimate usage.

Scientific effect:
- Reduces Type-I errors (false positives) during atypical occupancy patterns.
- Maintains sensitivity for real leaks through confidence gating rather than absolute suppression.

---

## 9) Gap Analysis And Reliability Findings

### 9.1 Findings (Criticality-Oriented)

1) Cost-calculation inconsistency between UI KPI and engine formulas  
- Engine path uses `WATER_COST_PER_M3 = 0.50`  
- Some UI calculations use `WATER_COST_PER_LITER = 0.007`  
Impact:
- Different cost projections can appear for the same leak rate.
Recommendation:
- Unify all cost displays to one tariff model and source of truth.

2) Environmental-carbon inconsistency across calculation paths  
- `calculate_carbon_footprint` includes treatment + energy terms  
- `InsightEngine.build_environmental_insight` currently reports energy-derived carbon only  
Impact:
- Two legitimate but different carbon estimates may confuse judges/users.
Recommendation:
- Harmonize into one canonical environmental formula (or clearly expose both with labels).

3) Non-data comment lines inside `example_normal_day_2026-10-05.csv`  
- Lines prefixed with `#` are parsed as invalid rows in generic CSV readers.  
Impact:
- Not fatal (validator removes invalid rows), but avoidable data hygiene risk.
Recommendation:
- Move annotations to README/report or maintain a clean pure-data CSV for production.

4) Model artifact naming legacy (`hydrosentinel_isolation_forest.joblib`)  
- Name suggests pure isolation forest, while active diagnostic bundle contains classifier/regressor stack.
Impact:
- Documentation ambiguity.
Recommendation:
- Rename artifact to diagnostic-neutral name and update references.

### 9.2 Reliability Posture

Strengths:
- Validation layer blocks malformed telemetry and out-of-range values.
- Model training fingerprinting supports reuse/invalidation sanity.
- API-ready JSON contract is tested.
- Event-aware logic reduces false positives in school operations.

Boundaries:
- This is Decision Support, not autonomous control.
- Human review remains mandatory before field action.

Formal statement for judges:
- HydroSentinel-AI is engineered as a human-supervised analytical co-pilot. It provides evidence-backed alerts, quantified impact, and explainable reasoning, while final operational decisions remain under responsible human authority.

---

## 10) Final Engineering Verdict

Verdict: `Technically coherent and submission-ready with minor standardization gaps.`

Current readiness:
- Core pipeline: PASS
- UI integration (simulation-data download controls): PASS
- System verification: PASS
- Explainability + decision-support framing: PASS

Recommended next hardening sprint:
1. Unify cost formula source-of-truth across UI and engine.
2. Unify carbon-footprint computation path and label assumptions clearly.
3. Clean annotated CSV comments from production data files.
4. Rename model artifact to reflect current diagnostic architecture.
