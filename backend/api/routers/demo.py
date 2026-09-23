"""Public, non-persistent endpoints for the seeded portfolio demo."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.api.schemas.analysis import AnalysisRequest
from backend.api.schemas.analysis import AnalysisResponse
from backend.database.session import get_db_session
from backend.services.analysis_service import run_demo_analysis
from backend.services.analysis_service import serialize_analysis_result


router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger(__name__)


@router.post("/analyses", response_model=AnalysisResponse)
def create_demo_analysis(
    payload: AnalysisRequest,
    session: Session = Depends(get_db_session),
) -> AnalysisResponse:
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
        logger.exception("Anonymous demo analysis execution failed")
        raise HTTPException(status_code=500, detail="Demo analysis could not be completed.") from exc

    return AnalysisResponse.model_validate(serialize_analysis_result(result))
