"""FastAPI entrypoint for HydroSentinel backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session

from backend.api.routers.analysis import router as analysis_router
from backend.api.routers.auth import router as auth_router
from backend.api.routers.health import router as health_router
from backend.api.routers.scenarios import router as scenarios_router
from backend.core.config import settings
from backend.database.session import SessionLocal
from backend.services.bootstrap_service import initialize_database
from backend.services.bootstrap_service import seed_default_data


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    session: Session = SessionLocal()
    try:
        seed_default_data(session)
    finally:
        session.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Production API for HydroSentinel leak detection, analytics, authentication, and administration.",
    debug=settings.app_debug,
    version=settings.app_version,
    swagger_ui_parameters={"persistAuthorization": True, "displayRequestDuration": True},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.onrender.com", "*.vercel.app"])

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(scenarios_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": settings.app_name}