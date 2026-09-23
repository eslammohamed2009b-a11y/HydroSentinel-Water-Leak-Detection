# HydroSentinel

HydroSentinel is an AI-assisted water anomaly and leak-detection decision-support prototype for buildings and managed facilities. It combines simulated telemetry, contextual operating rules, and machine-learning models to make leak-like patterns easier to investigate.

**Live Demo:** [https://hydro-sentinel-water-leak-detection.vercel.app/demo](https://hydro-sentinel-water-leak-detection.vercel.app/demo)

## What It Does

- Analyzes flow, pressure, and operating context from telemetry records.
- Separates elevated but legitimate activity from leak-like behavior, including high-activity event scenarios.
- Estimates water loss and approximate financial and environmental impact.
- Returns reasoning, telemetry visualization data, and a scenario-specific interpretation rather than only a binary label.

## Project Story

HydroSentinel began during a 7-day AI hackathon. The team spent roughly five hours researching and narrowing possible problems before committing to water loss in school facilities.

The difficult insight was not simply detecting high flow: legitimate high activity can also look abnormal. High flow by itself is not enough; operating context changes the interpretation.

That observation became the project’s core decision-support idea: account for occupancy and high-activity conditions before treating elevated demand as leak-like behavior.

The first hackathon prototype used synthetic telemetry, Isolation Forest, and Streamlit to explore that idea quickly.

After the competition, the project was rebuilt rather than abandoned:

- Next.js and React frontend
- FastAPI backend
- SQLAlchemy and Alembic persistence
- Current diagnostic path using `RandomForestClassifier` for classification and `LinearRegression` for estimated loss rate

The original hackathon model and the current diagnostic path are not the same system.

## Competition Recognition

**Official Finalist — High School Track.**

The certificate confirms HydroSentinel advanced to the **Final Round**. The feedback report's "did not advance" refers only to the later **Final Judge panel**, not to finalist status.

**Final Round = finalist stage · Final Judge panel = later judging stage**

**Core Judge Score: 60.2 / 70**

- Problem Understanding: 5.0 / 5
- AI Reasoning: 4.0 / 5
- Solution Design: 4.0 / 5
- Impact & Decision: 4.0 / 5
- Responsible AI: 4.0 / 5

## Try the Public Demo

The public demo requires no login and runs four seeded, simulated scenarios end to end.

| Scenario | Expected interpretation |
| --- | --- |
| Normal Operation | No leak |
| Hidden Leak | Leak during normal usage |
| High Activity | No leak; elevated activity is legitimate in context |
| High Activity + Leak | Leak during elevated activity |

These are simulated scenarios, not live facility data or physical validation results.

## System Architecture

```text
Browser / Next.js
        ↓
FastAPI REST API
        ↓
Analysis + contextual rules + ML models
        ↓
SQLAlchemy / Alembic / PostgreSQL
```

The Next.js frontend is deployed on Vercel. The FastAPI backend is deployed on Render. PostgreSQL is the production-targeted persistence layer for authenticated analysis history and feedback.

## Analysis Pipeline

1. Load seeded telemetry for the selected scenario.
2. Extract flow, pressure, time, occupancy, and operating-context features.
3. Classify leak/anomaly behavior and estimate a loss rate.
4. Apply contextual rules, including different handling for high-activity event conditions.
5. Estimate water loss and approximate financial and environmental impact.
6. Return an explanation, anomaly details, and visualization data to the client.

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript |
| Backend | FastAPI, Python |
| ML / data | pandas, NumPy, scikit-learn, joblib |
| Database | SQLAlchemy, Alembic, PostgreSQL-targeted architecture |
| Deployment | Vercel frontend, Render backend |
| Testing | Python `unittest`, GitHub Actions, frontend production build |

## Reliability and Safety Work

- The public demo is isolated from authenticated user history and does not persist anonymous runs.
- A bounded, input-keyed demo result cache avoids unnecessary repeated work.
- Authenticated analysis executions receive unique analysis IDs and remain owner-scoped.
- Standard and Event analysis modes use concurrency-safe, mode-specific model handling.
- Liveness and readiness endpoints verify service availability and seeded scenario readiness.
- The anonymous demo uses proxy-aware, process-local rate limiting with explicit proxy-header trust configuration.
- CORS is restricted to configured local and HydroSentinel deployment origins.
- Production schema changes are handled through Alembic migrations rather than runtime schema creation.
- API errors return generic client messages while server-side tracebacks are logged with configured-secret redaction.

## Limitations

- Validation uses synthetic/simulated telemetry and has not been validated on physical building or facility infrastructure.
- The model score is not a calibrated leak probability, confidence interval, or confirmation that a physical leak exists.
- Estimated loss rate is a model output, not a physical measurement.
- Human review is required before any real-world operational action.
- Impact calculations are estimates based on stated assumptions: `$0.50/m³` water cost, `0.45 kWh/m³` treatment energy, `0.19 kgCO2e/m³` treatment emissions, and `0.42 kgCO2e/kWh` grid emissions.

## Project Evolution

The deployed application is the maintained continuation of the hackathon idea; the original Streamlit prototype is historical and is not the current public application.

## Run Locally

Create `.env` from `.env.example`, then start PostgreSQL and the backend from the repository root:

```bash
docker compose up -d postgres
python -m pip install -r backend/requirements.txt
alembic upgrade head
uvicorn backend.main:app --reload
```

In a separate terminal, start the frontend:

```bash
cd frontend
npm ci
npm run dev
```

The API is available at `http://localhost:8000/api/v1`. The frontend defaults to that API URL unless `NEXT_PUBLIC_API_BASE_URL` is set.

## Verification

```bash
python -m unittest test_system.py

cd frontend
npm ci
npm run build
```

## Repository Structure

```text
backend/        FastAPI application, analysis services, models, and persistence
frontend/       Next.js public demo and authenticated application views
alembic/        Database migration environment and revisions
test_system.py  Backend integration and regression tests
render.yaml     Render service and PostgreSQL infrastructure configuration
```
