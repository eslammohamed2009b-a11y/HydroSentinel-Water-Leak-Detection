# HydroSentinel-AI Technical Report (Scenario Matrix Edition)

Date: 2026-06-19  
Project: HydroSentinel-AI  
Release Tag: Scenario Matrix Upgrade  
Audience: Judges and Technical Reviewers  
System Positioning: Decision Support for Human Operators (No Autonomous Actuation)

---

## Executive Summary

HydroSentinel-AI is a machine-learning-based decision-support platform for school water infrastructure. It detects anomalous telemetry patterns, estimates leak severity and impact, and explains why alerts were generated.

In this release, the project was upgraded with a formal 4-scenario test matrix to improve demonstration coverage and evaluation rigor:

1. `normal.csv` -> Baseline school day (no leak)
2. `normal_leak.csv` -> Normal school day + leak injection
3. `event.csv` -> Event day (no leak)
4. `event_leak.csv` -> Event day + leak

This matrix explicitly separates event-driven legitimate consumption from leak behavior, which is the core reliability requirement for schools.

---

## 1) Architecture Overview

### 1.1 Presentation Layer (`app.py`)

- Streamlit-based interactive dashboard
- Operational and executive views
- Event Mode toggle
- CSV upload + simulation-data documentation
- Download buttons for the four official scenario files

### 1.2 Intelligence Layer (`ml_engine.py`)

- Input schema validation and row-level cleaning
- Model training/reuse lifecycle
- Diagnostic inference (classification + regression)
- Explainability and impact calculations
- API-ready result packaging

### 1.3 Persistence Layer

- Scenario CSV files
- Model artifact (`hydrosentinel_isolation_forest.joblib`)
- Feedback and run logs (`feedback.csv`, `logs.csv`)

---

## 2) Scenario Matrix (Official)

### 2.1 Why This Matrix Matters

A single "normal vs leak" split is insufficient for school environments, because event days produce legitimate demand spikes that can resemble leaks if context is ignored. The scenario matrix provides structured evidence of model discrimination across both occupancy and fault dimensions.

### 2.2 Scenario Definitions

| Scenario | File | Expected Behavior | Purpose |
|---|---|---|---|
| A | `normal.csv` | No leak flag | Baseline reference for routine day |
| B | `normal_leak.csv` | Leak signature should emerge | Validate leak sensitivity under normal occupancy |
| C | `event.csv` | Elevated usage but no leak | Validate false-positive control under event load |
| D | `event_leak.csv` | Leak under event context | Validate robustness under combined complexity |

### 2.3 Current Data Characteristics

All four files use the canonical schema:
- `Timestamp`
- `Flow_Rate_LPM`
- `Avg_Pressure_PSI`
- `Occupancy_Status`

Design logic:
- `normal.csv`: stable flow/pressure baseline with class/after-hours transitions
- `normal_leak.csv`: same baseline plus leak window injection (higher flow + lower pressure)
- `event.csv`: event-driven demand elevation without leak degradation
- `event_leak.csv`: elevated event demand with injected leak signature

---

## 3) Data Generation Strategy

Synthetic telemetry generation was designed to be deterministic and reviewable for judging.

### 3.1 Baseline Synthesis

Normal-day baseline simulates:
- Class-hour and after-hours occupancy segments
- Slight natural variation in flow and pressure
- No abrupt pressure-collapse signature

### 3.2 Leak Injection Strategy

Leak injection applies physically plausible directional change:
- Flow increases above local baseline
- Pressure drops below local baseline
- Injected over a controlled time window to represent sustained fault behavior

### 3.3 Event Day Synthesis

Event-day non-leak pattern intentionally includes:
- Higher legitimate demand
- Maintained pressure within non-fault ranges
- `Occupancy_Status='Event'` in event windows

This allows direct testing that increased consumption alone is not treated as a leak.

---

## 4) Tech Stack and Libraries

### 4.1 Core Dependencies

- `streamlit`: UI runtime
- `pandas`: CSV processing and data manipulation
- `numpy`: numerical operations and synthetic generation support
- `scikit-learn`: modeling pipelines and estimators
- `plotly`: telemetry visualization
- `joblib`: model persistence

### 4.2 Model Components Used

- `RandomForestClassifier`: leak-type classification and confidence
- `LinearRegression`: predicted leak loss (L/min)
- `ColumnTransformer` + `OneHotEncoder`: mixed numeric/categorical preprocessing

---

## 5) ML vs Hard-coded Rules

### 5.1 Why ML Is Needed

Hard-coded rules (e.g., fixed flow threshold) fail in schools because occupancy context changes behavior:
- Event periods can legitimately exceed normal flow
- Absolute thresholds cannot reliably separate demand surge vs leak

### 5.2 Advantage of Current Pipeline

The model can capture nonlinear interactions among:
- flow,
- pressure,
- occupancy context,
- time-derived features.

This improves discrimination quality and supports confidence-weighted alerts instead of rigid binary rules.

---

## 6) Physics-Based and Financial Insight

Let $L$ be leak rate in liters/min.

$$
\text{Liters/hour} = L \times 60
$$

$$
\text{m}^3/\text{hour} = \frac{L \times 60}{1000}
$$

Given `WATER_COST_PER_M3 = 0.50`:

$$
\text{Cost/hour} = \frac{L \times 60}{1000} \times 0.50
$$

$$
\text{Cost/day} = \text{Cost/hour} \times 24
$$

Equation consistency status:
- Unified in engine and Streamlit UI
- KPI and executive cards now share the same source-of-truth equation path

---

## 7) Environmental Impact Logic

HydroSentinel estimates water-related carbon impact using two additive components:

1. Treatment emissions factor
2. Energy emissions from pumping/treatment

Canonical structure:

$$
\text{CO2e}_{total} = \text{CO2e}_{treatment} + \text{CO2e}_{energy}
$$

with:

$$
\text{CO2e}_{energy} = (m^3 \times 0.45) \times 0.42
$$

The reporting now exposes both component breakdown and total carbon value, improving transparency for sustainability review.

---

## 8) Event Mode Logic

Event Mode reduces false positives by integrating context into both training/evaluation paths:

- Event-context scenarios are included when mode is enabled
- Confidence gating prevents low-confidence event spikes from being over-flagged

Practical effect:
- Better separation between legitimate event demand and leak signatures
- Higher operator trust during school activities

---

## 9) Verification and Test Coverage

### 9.1 Updated Test Coverage

Test suite now includes scenario-matrix validation:
- Reads and cleans each of the four scenario CSV files
- Verifies engine can evaluate each scenario without contract breakage
- Confirms required response keys and insight blocks are present

### 9.2 Reliability Guardrails

- Strict schema validation before inference
- Range checks for flow and pressure
- Occupancy-status whitelist
- JSON-ready output contract
- Human-in-the-loop warning in UI

---

## 10) Gap Analysis

### 10.1 Closed in This Release

- Scenario matrix completeness for demo/testing
- UI file naming clarity and simulation-data labeling
- Equation consistency for cost and environmental reporting

### 10.2 Remaining Improvement Opportunities

1. Rename model artifact to reflect hybrid diagnostic pipeline naming.
2. Add dedicated threshold-regression tests for expected leak/no-leak outcomes per scenario.
3. Introduce CI pipeline for automated test + lint + compile gates on push.

---

## 11) Governance and Safety Position

HydroSentinel is a decision-support assistant only:
- No autonomous valve control
- No automatic physical intervention
- Maintenance action remains human-approved

This boundary is intentional and aligned with responsible AI deployment in school infrastructure.

---

## 12) Final Technical Verdict

HydroSentinel-AI is technically coherent, auditable, and now better structured for judge evaluation through an explicit scenario matrix that captures both occupancy context and leak conditions.

Release status:
- Scenario matrix: implemented
- UI integration: updated
- Engine compatibility: verified through scenario tests
- Streamlit presentation: updated
- Ready for final demonstration and judging
