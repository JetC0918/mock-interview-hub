"""Authentication utilities for route authorization."""

from fastapi import HTTPException, Depends, status
from fastapi.security import APIKeyCookie
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from ..database.config import get_db
from ..database.service import DatabaseService

COOKIE_NAME = "session_token"
cookie_scheme = APIKeyCookie(name=COOKIE_NAME, auto_error=False)


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


def get_current_session_token(token: Optional[str] = Depends(cookie_scheme)) -> Optional[str]:
    """Read the opaque session token from the cookie."""
    return token


def require_auth(
    token: Optional[str] = Depends(get_current_session_token),
    service: DatabaseService = Depends(get_service),
) -> str:
    """Require a current, unrevoked authentication session."""
    user_id = service.get_user_id_by_session_token(token) if token else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user_id
def require_session_participant(
    id: str,
    user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service),
) -> str:
    """Require the verified principal to be a participant of the session."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if user_id not in {participant.id for participant in session.participants}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a participant of this session")
    return user_id
