from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from sqlalchemy.orm import Session as DBSession
from ..models.session import (
    Session,
    PublicSession,
    SessionCreate,
    SessionJoin,
    SessionCodeUpdate,
    SessionLanguageUpdate,
    SessionCursorUpdate,
)
from ..models.execution import ChatMessage, ChatMessageCreate
from ..models.common import SupportedLanguage
from ..database.config import get_db
from ..database.service import DatabaseService
from ..utils.auth_utils import require_auth, require_session_participant
from ..utils.rate_limit import limiter

router = APIRouter(prefix="/sessions", tags=["Sessions"])

def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


@router.get("", response_model=List[Session])
def get_sessions(
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Get the current user's non-ended sessions (requires authentication)."""
    # Only return sessions where user is a participant
    all_sessions = service.get_all_sessions()
    user_sessions = []
    for session in all_sessions:
        participant_ids = [p.id for p in session.participants]
        if current_user_id in participant_ids and session.status.value != "ended":
            user_sessions.append(session)
    return user_sessions


@router.get("/public", response_model=List[PublicSession])
def get_public_sessions(service: DatabaseService = Depends(get_service)):
    """List bounded non-ended sessions for unauthenticated spectating."""
    return service.get_public_sessions()


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


@router.get("/{id}", response_model=PublicSession)
def get_session(id: str, service: DatabaseService = Depends(get_service)):
    """Get the restricted public session projection for direct-link viewing."""
    session = service.get_public_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{id}/private", response_model=Session)
def get_private_session(
    id: str,
    current_user_id: str = Depends(require_session_participant),
    service: DatabaseService = Depends(get_service),
):
    """Get full session data for an authenticated participant."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{id}/join", response_model=Session)
def join_session(
    id: str,
    request: Request,
    body: SessionJoin,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Join a session with its high-entropy secret (requires authentication)."""
    limiter.check(request, "join-by-secret", limit=10)
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status.value == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    if session.pin != body.pin:
        raise HTTPException(status_code=403, detail="Invalid session join secret")
    
    user = service.get_user(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    updated_session = service.join_session(id, user)
    if not updated_session:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    return updated_session


@router.post("/{id}/join-secret/rotate")
def rotate_join_secret(
    id: str,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service),
):
    """Rotate a host's bearer join secret, revoking the previous secret."""
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.hostId != current_user_id:
        raise HTTPException(status_code=403, detail="Only the host can rotate the join secret")
    if session.status.value == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    secret = service.rotate_join_secret(id)
    if not secret:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    return {"pin": secret}


@router.post("/join-by-pin", response_model=Session)
def join_by_pin(
    request: Request,
    body: SessionJoin,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Join a session by high-entropy secret (requires authentication)."""
    limiter.check(request, "join-by-secret", limit=10)
    session = service.get_session_by_pin(body.pin, include_ended=True)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status.value == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    
    user = service.get_user(current_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    updated_session = service.join_session(session.id, user)
    if not updated_session:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    return updated_session


@router.put("/{id}/code")
def update_code(
    id: str, 
    body: SessionCodeUpdate,
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
    if session.status.value == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    
    if not service.update_session_code(id, body.code):
        latest = service.get_session(id)
        if latest and latest.status.value == "ended":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Code updated"}


@router.put("/{id}/language")
def update_language(
    id: str, 
    body: SessionLanguageUpdate,
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
    if session.status.value == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    
    if not service.update_session_language(id, body.language.value):
        latest = service.get_session(id)
        if latest and latest.status.value == "ended":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
        raise HTTPException(status_code=404, detail="Session not found or invalid language")
    return {"message": "Language updated"}


@router.put("/{id}/cursor")
def update_cursor(
    id: str, 
    body: SessionCursorUpdate,
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
    
    if session.status.value == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    if not service.update_cursor_position(
        id, current_user_id, body.position.line, body.position.column
    ):
        latest = service.get_session(id)
        if latest and latest.status.value == "ended":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
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
    if current_user_id == session.hostId:
        raise HTTPException(status_code=409, detail="The host cannot leave the session")
    if not service.leave_session(id, current_user_id):
        raise HTTPException(status_code=404, detail="Participant not found")
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
        latest = service.get_session(id)
        if latest and latest.status.value == "ended":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
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
    if not msg:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
    return msg
