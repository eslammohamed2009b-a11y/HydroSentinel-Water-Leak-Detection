"""Scenario endpoints for HydroSentinel backend."""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.api.schemas.analysis import ScenarioSummary
from backend.database.session import get_db_session
from backend.services.analysis_service import list_scenarios


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioSummary])
def get_scenarios(session: Session = Depends(get_db_session)) -> list[ScenarioSummary]:
    return [ScenarioSummary.model_validate(item) for item in list_scenarios(session)]