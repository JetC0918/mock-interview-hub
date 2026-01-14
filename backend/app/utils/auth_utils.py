"""
Authentication utilities for route authorization.
"""
from fastapi import HTTPException, Depends, Cookie, status
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from ..database.config import get_db
from ..database.service import DatabaseService

# Cookie name (must match auth.py)
COOKIE_NAME = "user_id"


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


def get_current_user_id(user_id: Optional[str] = Cookie(None, alias=COOKIE_NAME)) -> Optional[str]:
    """Get current user ID from session cookie."""
    return user_id


def require_auth(user_id: Optional[str] = Depends(get_current_user_id)) -> str:
    """Require authentication - raises 401 if not authenticated."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user_id


def require_session_participant(
    session_id: str,
    user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
) -> str:
    """
    Require user to be a participant of the session.
    Returns user_id if authorized.
    """
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    participant_ids = [p.id for p in session.participants]
    if user_id not in participant_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this session"
        )
    
    return user_id


def require_session_host(
    session_id: str,
    user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
) -> str:
    """
    Require user to be the host of the session.
    Returns user_id if authorized.
    """
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if user_id != session.hostId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can perform this action"
        )
    
    return user_id
