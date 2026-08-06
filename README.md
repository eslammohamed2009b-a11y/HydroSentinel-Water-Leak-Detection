# HydroSentinel-AI

HydroSentinel-AI is an AI-assisted water anomaly and leak-detection decision-support prototype for buildings and managed facilities, including offices, hotels, hospitals, residential buildings, schools, and commercial properties. It is not a municipal water-network product or a certified leak-detection device.

## Current Finalized Version

- Next.js frontend and FastAPI backend
- JWT authentication, refresh tokens, and owner-scoped analysis history/feedback
- PostgreSQL-targeted SQLAlchemy persistence with Alembic migrations
- Seeded simulated telemetry scenarios with flow, pressure, and building operating context
- Synthetic-data diagnostic pipeline and contextual Event / High Activity Mode
- Estimated water, financial, and environmental impact with stated assumptions

Architecture: `Next.js 16 + React` frontend → `FastAPI` API → `SQLAlchemy/Alembic` → `PostgreSQL`; the backend evaluates seeded scenarios with the existing Python/scikit-learn pipeline and persists private results and feedback.

## Limitations and Responsible Use

- Validation data is synthetic/simulated; it has not been validated on physical building or facility infrastructure.
- Model scores are synthetic classifier scores, not calibrated leak probabilities, confidence intervals, or accuracy claims.
- `Estimated Loss Rate` is a model estimate, not a physical measurement.
- Estimated volume integrates flagged L/min values over parsed sample intervals (capped at one hour). Financial estimates assume `$0.50/m³`, and environmental estimates assume `0.45 kWh/m³`, `0.19 kgCO2e/m³` treatment emissions, and `0.42 kgCO2e/kWh` grid emissions.
- Human review remains required before operational action.

## Original USAII Hackathon Context

HydroSentinel began as a rapid Streamlit prototype for the USAII Global AI Hackathon 2026, where the required target setting was school facilities. It advanced to the Final Round / finalist level in the High School track. The original competition scenarios and historical datasets therefore retain school-oriented names and context. Streamlit is historical only; the current product is the Next.js/FastAPI application above.

## Run Locally

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.main:app --reload
```

In a separate terminal:

```bash
cd frontend
npm install
npm run build
```

The API is at `http://localhost:8000/api/v1`; the frontend expects `NEXT_PUBLIC_API_BASE_URL` (default: that local API URL).

Required deployment settings: `DATABASE_URL`, `JWT_SECRET_KEY`, `ALLOWED_ORIGINS`, `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`, and `NEXT_PUBLIC_API_BASE_URL`.

## Verification

```bash
python -m unittest test_system.py
cd frontend && npm run build
```

## Deployment State

`render.yaml` defines a PostgreSQL-backed Render API deployment and runs Alembic before startup. `vercel.json` defines the frontend build. Actual deployment, domain wiring, and CORS finalization require the repository owner's Render and Vercel credentials; no live deployment is claimed by this repository.
