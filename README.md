# HydroSentinel

HydroSentinel is a production-oriented water leak detection platform for school infrastructure. It combines a FastAPI backend, a Next.js 15 frontend, PostgreSQL persistence, JWT authentication, and a Python machine-learning engine for anomaly detection and leak diagnostics.

## Architecture

```text
project/
├── frontend/                # Next.js 15 + React + TypeScript UI
├── backend/                 # FastAPI API, auth, services, AI, ORM models
├── alembic/                 # Database migrations
├── docker-compose.yml       # Local full-stack environment
├── render.yaml              # Render backend deployment blueprint
├── vercel.json              # Vercel frontend deployment blueprint
└── .env.example             # Required environment variables
```

## Core Features

- Operational and executive dashboards
- Event-aware leak detection
- Scenario matrix stored in PostgreSQL
- Analysis history and detail views
- Feedback capture per analysis
- JWT authentication with refresh tokens
- Swagger UI at `/docs`
- Alembic migrations for schema management
- Docker Compose for local development
- GitHub Actions CI for backend tests and frontend build

## Backend Stack

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL via `psycopg`
- Passlib
- Python-JOSE
- Pandas / NumPy / scikit-learn / joblib

## Frontend Stack

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS 4

## Environment Variables

Copy `.env.example` to `.env` and set production-safe values.

Critical values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ALLOWED_ORIGINS`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `NEXT_PUBLIC_API_BASE_URL`

## Local Development

### 1. Backend only

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.main:app --reload
```

Backend URLs:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

### 2. Full stack with Docker Compose

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## Database Migrations

Create and apply migrations with Alembic:

```bash
alembic revision -m "describe change"
alembic upgrade head
```

## Testing

Run backend integration tests:

```bash
python -m unittest test_system.py
```

The current test suite uses a temporary SQLite database for local validation. Production configuration targets PostgreSQL.

## Deployment

### Frontend on Vercel

- Root directory: `frontend`
- Build command: `npm run build`
- Required env: `NEXT_PUBLIC_API_BASE_URL`

### Backend on Render

- Build command: `pip install -r backend/requirements.txt`
- Start command: `alembic upgrade head ; uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/v1/health`

### PostgreSQL

Use Neon, Supabase, or Render Postgres and set the resulting connection string in `DATABASE_URL`.

## Security Notes

- Replace all default secrets before deployment
- Restrict `ALLOWED_ORIGINS` to deployed frontend domains only
- Rotate bootstrap admin credentials immediately after first login
- Keep the backend behind HTTPS in production
- Use managed PostgreSQL with network restrictions where possible

## Current Deployment Status

The repository is deployment-prepared but not cloud-deployed from this session because the environment does not include:

- Node.js for local frontend build verification
- Docker for local container verification
- Cloud credentials or API tokens for Vercel / Render / Supabase / Neon

## License

See `LICENSE`.
