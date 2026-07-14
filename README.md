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

Deploy as two services:

- Backend API on Render (using `render.yaml` blueprint)
- Frontend on Vercel (root directory `frontend`)

### 1. Deploy backend (Render)

1. Push the repository to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select the repository and keep `render.yaml` at repo root.
4. Fill required secret values when prompted:
	- `BOOTSTRAP_ADMIN_EMAIL`
	- `BOOTSTRAP_ADMIN_PASSWORD`
5. Click deploy.

What Render provisions automatically from `render.yaml`:

- Managed PostgreSQL database (`hydrosentinel-db`)
- API web service (`hydrosentinel-api`)
- Auto-generated `JWT_SECRET_KEY`
- Runtime `DATABASE_URL` wiring to the managed database
- Migration run before API startup (`alembic upgrade head`)

After deployment, copy the backend base URL, for example:

- `https://hydrosentinel-api.onrender.com/api/v1`

### 2. Deploy frontend (Vercel)

1. In Vercel, import the same repository.
2. Set **Root Directory** to `frontend`.
3. Add environment variable:
	- `NEXT_PUBLIC_API_BASE_URL=https://<your-render-service>.onrender.com/api/v1`
4. Deploy.

### 3. Configure backend CORS with final frontend domain

In Render service environment variables, update:

- `ALLOWED_ORIGINS=https://<your-vercel-domain>`

Then redeploy backend.

### 4. Production smoke checks

- Backend health: `GET /api/v1/health`
- Swagger: `https://<render-domain>/docs`
- Frontend login/register loads without CORS errors
- Create one analysis from UI and verify it appears in history

## Security Notes

- Replace all default secrets before deployment
- Restrict `ALLOWED_ORIGINS` to deployed frontend domains only
- Rotate bootstrap admin credentials immediately after first login
- Keep the backend behind HTTPS in production
- Use managed PostgreSQL with network restrictions where possible

## Current Deployment Status

The repository is cloud-deployment ready with blueprint and frontend config files in place.
Actual cloud rollout still requires your Render and Vercel account access to complete the final clicks and domain wiring.

## License

See `LICENSE`.
