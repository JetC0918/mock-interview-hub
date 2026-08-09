from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Query
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
    GuestSessionJoin,
    GuestSessionJoinResponse,
    SessionRevisionResponse,
)
from ..models.execution import ChatMessage, ChatMessageCreate, PublicChatMessage
from ..models.common import SupportedLanguage
from ..database.config import get_db
from ..database.service import DatabaseService, AdmissionError, RevisionResult, IdempotencyConflictError
from .auth import set_secure_cookie
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
    return service.get_user_sessions(current_user_id)


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
    
    problem = service.get_random_problem()
    return service.create_hosted_session(
        title=session_in.title,
        host_id=user.id,
        language=session_in.language or SupportedLanguage.PYTHON,
        problem_id=problem.id if problem else None,
    )


@router.get("/{id}", response_model=PublicSession)
def get_session(id: str, service: DatabaseService = Depends(get_service)):
    """Get the restricted public session projection for direct-link viewing."""
    session = service.get_public_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{id}/public-messages", response_model=List[PublicChatMessage])
def get_public_messages(
    id: str,
    limit: int = Query(default=50, ge=1, le=50),
    service: DatabaseService = Depends(get_service),
):
    if not service.get_public_session(id):
        raise HTTPException(status_code=404, detail="Session not found")
    return service.get_public_messages(id, limit)


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
    try:
        return service.admit_user(id, body.pin, current_user_id)
    except AdmissionError as error:
        _raise_admission(error)


@router.post("/{id}/guest-join", response_model=GuestSessionJoinResponse)
def guest_join_session(
    id: str,
    body: GuestSessionJoin,
    request: Request,
    response: Response,
    service: DatabaseService = Depends(get_service),
):
    """Validate admission before creating any durable guest/auth state."""
    limiter.check(request, "join-by-secret", limit=10)
    try:
        user, session, token = service.create_guest_admission(
            id, body.pin, body.username, body.attemptId, body.attemptSecret,
        )
    except AdmissionError as error:
        _raise_admission(error)
    except IdempotencyConflictError:
        raise HTTPException(status_code=409, detail="Guest admission attempt does not match the original request")
    set_secure_cookie(response, token)
    return GuestSessionJoinResponse(user=user, session=session)


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


@router.post("/{id}/start")
def start_session(
    id: str,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service),
):
    """Start a waiting session exactly once as its host."""
    result = service.start_session(id, current_user_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    if result == "forbidden":
        raise HTTPException(status_code=403, detail="Only the host can start the session")
    if result == "ended":
        raise HTTPException(status_code=410, detail="Session has ended")
    return {"status": "active"}


@router.post("/join-by-pin", response_model=Session)
def join_by_pin(
    request: Request,
    body: SessionJoin,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Join a session by high-entropy secret (requires authentication)."""
    limiter.check(request, "join-by-secret", limit=10)
    try:
        return service.admit_user_by_secret(body.pin, current_user_id)
    except AdmissionError as error:
        _raise_admission(error)


def _raise_admission(error: AdmissionError):
    if error.kind == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    if error.kind == "ended":
        raise HTTPException(status_code=410, detail="Session has ended")
    if error.kind == "quota":
        raise HTTPException(status_code=429, detail="Session participant limit reached")
    raise HTTPException(status_code=403, detail="Invalid session join secret")


def _revision_response(result: RevisionResult) -> SessionRevisionResponse:
    if result.kind == "updated":
        return SessionRevisionResponse(codeRevision=result.revision or 0)
    if result.kind == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    if result.kind == "ended":
        raise HTTPException(status_code=410, detail="Session has ended")
    if result.kind == "forbidden":
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    raise HTTPException(
        status_code=409,
        detail={"message": "Shared editor revision is stale", "currentRevision": result.revision},
    )


@router.put("/{id}/code", response_model=SessionRevisionResponse)
def update_code(
    id: str, 
    body: SessionCodeUpdate,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Update session code (requires session participation)."""
    return _revision_response(service.update_session_code(
        id, current_user_id, body.code, body.baseRevision,
    ))


@router.put("/{id}/language", response_model=SessionRevisionResponse)
def update_language(
    id: str, 
    body: SessionLanguageUpdate,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Update session language (requires session participation)."""
    return _revision_response(service.update_session_language(
        id, current_user_id, body.language.value, body.baseRevision,
    ))


@router.put("/{id}/cursor")
def update_cursor(
    id: str, 
    body: SessionCursorUpdate,
    request: Request,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Update cursor position (requires session participation)."""
    limiter.check(request, "cursor", limit=120)
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
    if session.status.value == "ended":
        raise HTTPException(status_code=410, detail="Session has ended")
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
    result = service.end_session(id, current_user_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    if result == "forbidden":
        raise HTTPException(status_code=403, detail="Only the host can end the session")
    if result == "ended":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Session has ended")
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
    request: Request,
    current_user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Send a chat message (requires session participation)."""
    limiter.check(request, "chat", limit=60)
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
