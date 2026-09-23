"""Public, non-persistent endpoints for the seeded portfolio demo."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session

from backend.api.schemas.analysis import AnalysisRequest
from backend.api.schemas.analysis import AnalysisResponse
from backend.core.config import settings
from backend.core.safe_logging import log_exception
from backend.database.session import get_db_session
from backend.services.analysis_service import run_demo_analysis
from backend.services.analysis_service import serialize_analysis_result
from backend.services.demo_rate_limiter import demo_rate_limiter
from backend.services.demo_rate_limiter import select_demo_client_host


router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger(__name__)


@router.post("/analyses", response_model=AnalysisResponse)
def create_demo_analysis(
    payload: AnalysisRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> AnalysisResponse:
    client_host = select_demo_client_host(
        request.client.host if request.client else None,
        request.headers.get("X-Forwarded-For"),
        settings.trust_proxy_headers,
    )
    if not demo_rate_limiter.allow(
        client_host,
        settings.demo_rate_limit_requests,
        settings.demo_rate_limit_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demo request limit reached. Please try again shortly.",
        )
    try:
        result = run_demo_analysis(
            session=session,
            scenario_selected=payload.scenario_selected,
            event_mode=payload.event_mode,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Demo scenario data was not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log_exception(logger, "Anonymous demo analysis execution failed", exc)
        raise HTTPException(status_code=500, detail="Demo analysis could not be completed.") from exc

    return AnalysisResponse.model_validate(serialize_analysis_result(result))
