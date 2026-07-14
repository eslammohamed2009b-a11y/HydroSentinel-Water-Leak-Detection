"""Authentication endpoints."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from datetime import datetime
from datetime import timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user
from backend.api.schemas.auth import LoginRequest
from backend.api.schemas.auth import RefreshRequest
from backend.api.schemas.auth import RegisterRequest
from backend.api.schemas.auth import TokenResponse
from backend.api.schemas.auth import UserResponse
from backend.auth.security import create_access_token
from backend.auth.security import create_refresh_token
from backend.database.session import get_db_session
from backend.models.user import User
from backend.services.auth_service import authenticate_user
from backend.services.auth_service import create_user
from backend.services.auth_service import get_refresh_token
from backend.services.auth_service import revoke_refresh_token
from backend.services.auth_service import store_refresh_token


router = APIRouter(prefix="/auth", tags=["auth"])


def _build_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_db_session)) -> UserResponse:
    try:
        user = create_user(session, payload.email, payload.full_name, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database unavailable: {exc}") from exc

    return _build_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    try:
        user = authenticate_user(session, payload.email, payload.password)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Database unavailable: {exc}") from exc

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    refresh_token, expires_at = create_refresh_token()
    store_refresh_token(session, user, refresh_token, expires_at)
    return TokenResponse(access_token=create_access_token(user.email), refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    token_record = get_refresh_token(session, payload.refresh_token)
    if token_record is None or token_record.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    return TokenResponse(access_token=create_access_token(token_record.user.email), refresh_token=payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, session: Session = Depends(get_db_session)) -> None:
    revoke_refresh_token(session, payload.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _build_user_response(current_user)