"""Analysis endpoints for HydroSentinel backend."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.api.schemas.analysis import AnalysisHistoryItem
from backend.api.schemas.analysis import AnalysisRequest
from backend.api.schemas.analysis import AnalysisResponse
from backend.api.schemas.analysis import FeedbackRequest
from backend.api.schemas.analysis import FeedbackResponse
from backend.database.session import get_db_session
from backend.services.analysis_service import create_feedback
from backend.services.analysis_service import get_analysis_by_public_id
from backend.services.analysis_service import get_analysis_history
from backend.services.analysis_service import run_analysis
from backend.services.analysis_service import serialize_analysis_result


router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisResponse)
def create_analysis(payload: AnalysisRequest, session: Session = Depends(get_db_session)) -> AnalysisResponse:
    try:
        result = run_analysis(
            session=session,
            scenario_selected=payload.scenario_selected,
            event_mode=payload.event_mode,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    return AnalysisResponse.model_validate(serialize_analysis_result(result))


@router.get("", response_model=list[AnalysisHistoryItem])
def list_analyses(session: Session = Depends(get_db_session)) -> list[AnalysisHistoryItem]:
    return [
        AnalysisHistoryItem(
            analysis_id=item.analysis_id,
            scenario_selected=item.scenario_selected,
            event_mode=item.event_mode,
            has_leak=item.has_leak,
            confidence=item.confidence,
            leak_lpm=item.leak_lpm,
            total_liters=item.total_liters,
            created_at=item.created_at.isoformat(),
        )
        for item in get_analysis_history(session)
    ]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, session: Session = Depends(get_db_session)) -> AnalysisResponse:
    analysis = get_analysis_by_public_id(session, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis.payload_json)


@router.post("/{analysis_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(analysis_id: str, payload: FeedbackRequest, session: Session = Depends(get_db_session)) -> FeedbackResponse:
    try:
        feedback = create_feedback(session, analysis_id, payload.verdict)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FeedbackResponse(
        analysis_id=feedback.analysis_id,
        feedback=feedback.feedback,
        confidence=feedback.confidence,
        predicted_leak=feedback.predicted_leak,
    )