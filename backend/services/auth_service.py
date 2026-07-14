"""Authentication service layer."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.security import get_password_hash
from backend.auth.security import verify_password
from backend.models.user import RefreshToken
from backend.models.user import User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def create_user(session: Session, email: str, full_name: str, password: str, role: str = "operator") -> User:
    existing = get_user_by_email(session, email)
    if existing is not None:
        raise ValueError("A user with this email already exists.")

    user = User(
        email=email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        role=role,
        is_active=True,
        is_superuser=(role == "admin"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def store_refresh_token(session: Session, user: User, token: str, expires_at) -> RefreshToken:
    refresh_token = RefreshToken(user_id=user.id, token=token, expires_at=expires_at, is_revoked=False)
    session.add(refresh_token)
    session.commit()
    session.refresh(refresh_token)
    return refresh_token


def get_refresh_token(session: Session, token: str) -> RefreshToken | None:
    return session.scalar(select(RefreshToken).where(RefreshToken.token == token))


def revoke_refresh_token(session: Session, token: str) -> None:
    refresh_token = get_refresh_token(session, token)
    if refresh_token is None:
        return
    refresh_token.is_revoked = True
    session.commit()