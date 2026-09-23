"""Readiness endpoint distinct from the lightweight liveness route."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from backend.core.safe_logging import log_exception
from backend.database.session import get_db_session
from backend.services.readiness_service import database_is_ready


router = APIRouter(tags=["readiness"])
logger = logging.getLogger(__name__)


@router.get("/ready")
def readiness_check(session: Session = Depends(get_db_session)) -> dict[str, str]:
    try:
        ready = database_is_ready(session)
    except Exception as exc:
        log_exception(logger, "Readiness check failed", exc)
        ready = False

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The service is temporarily unavailable.",
        )
    return {"status": "ready"}
