from fastapi import APIRouter, HTTPException, Depends, status, Cookie
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from ..models.session import Session, SessionCreate, SessionJoin, Participant
from ..models.execution import ChatMessage, ChatMessageCreate
from ..models.common import SupportedLanguage, CursorPosition
from ..database.config import get_db
from ..database.service import DatabaseService
from ..utils.auth_utils import get_current_user_id, require_auth, require_session_participant, require_session_host

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Cookie name (must match auth.py)
COOKIE_NAME = "user_id"


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


@router.get("", response_model=List[Session])
def get_sessions(
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Get all active sessions (requires authentication)."""
    # Only return sessions where user is a participant
    all_sessions = service.get_all_sessions()
    user_sessions = []
    for session in all_sessions:
        participant_ids = [p.id for p in session.participants]
        if current_user_id in participant_ids:
            user_sessions.append(session)
    return user_sessions


@router.post("", response_model=Session, status_code=201)
def create_session(
    session_in: SessionCreate,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Create a new session (requires authentication)."""
    user = service.get_user(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    session = service.create_session(
        title=session_in.title,
        host_id=user.id,
        language=session_in.language or SupportedLanguage.PYTHON
    )
    
    # Auto-assign a problem to the session
    problem = service.get_random_problem()
    if problem:
        service.assign_problem_to_session(session.id, problem.id)
    
    # Host joins automatically
    service.join_session(session.id, user)
    return service.get_session(session.id)


@router.get("/{id}", response_model=Session)
def get_session(id: str, service: DatabaseService = Depends(get_service)):
    """Get session by ID (public - needed for joining)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{id}/join", response_model=Session)
def join_session(
    id: str,
    body: SessionJoin,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Join a session with PIN (requires authentication)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.pin != body.pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")
    
    user = service.get_user(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    updated_session = service.join_session(id, user)
    return updated_session


@router.post("/join-by-pin", response_model=Session)
def join_by_pin(
    body: SessionJoin,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Join a session by PIN only (requires authentication)."""
    session = service.get_session_by_pin(body.pin)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    user = service.get_user(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    updated_session = service.join_session(session.id, user)
    return updated_session


@router.put("/{id}/code")
def update_code(
    id: str, 
    body: dict, 
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Update session code (requires session participation)."""
    # Verify user is a participant
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    participant_ids = [p.id for p in session.participants]
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    
    if not service.update_session_code(id, body.get("code", "")):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Code updated"}


@router.put("/{id}/language")
def update_language(
    id: str, 
    body: dict,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Update session language (requires session participation)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    participant_ids = [p.id for p in session.participants]
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    
    if not service.update_session_language(id, body.get("language")):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Language updated"}


@router.put("/{id}/cursor")
def update_cursor(
    id: str, 
    body: dict,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Update cursor position (requires session participation)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    participant_ids = [p.id for p in session.participants]
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    
    user_id = body.get("userId")
    position = body.get("position", {})
    if not service.update_cursor_position(id, user_id, position.get("line"), position.get("column")):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Cursor updated"}


@router.post("/{id}/leave")
def leave_session(
    id: str,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Leave a session (requires authentication)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # TODO: Actually remove user from participants
    return {"message": "Left session"}


@router.post("/{id}/end")
def end_session(
    id: str,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """End a session (requires host role)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Only host can end the session
    if current_user_id != session.hostId:
        raise HTTPException(status_code=403, detail="Only the host can end the session")
    
    if not service.update_session_status(id, "ended"):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session ended"}


# Chat Endpoints
@router.get("/{id}/messages", response_model=List[ChatMessage])
def get_messages(
    id: str,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Get chat messages (requires session participation)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    participant_ids = [p.id for p in session.participants]
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    
    return service.get_messages(id)


@router.post("/{id}/messages", response_model=ChatMessage, status_code=201)
def send_message(
    id: str,
    body: ChatMessageCreate,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Send a chat message (requires session participation)."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    participant_ids = [p.id for p in session.participants]
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    
    user = service.get_user(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    msg = service.add_message(id, user.id, user.username, body.message)
    return msg
