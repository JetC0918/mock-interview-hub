from fastapi import APIRouter, HTTPException, Depends, status, Cookie
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from ..models.session import Session, SessionCreate, SessionJoin, Participant
from ..models.execution import ChatMessage, ChatMessageCreate
from ..models.common import SupportedLanguage, CursorPosition
from ..database.config import get_db
from ..database.service import DatabaseService

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Cookie name (must match auth.py)
COOKIE_NAME = "user_id"


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


def get_current_user_id(user_id: Optional[str] = Cookie(None, alias=COOKIE_NAME)) -> Optional[str]:
    """Get current user ID from session cookie."""
    return user_id


@router.get("/", response_model=List[Session])
def get_sessions(service: DatabaseService = Depends(get_service)):
    return service.get_all_sessions()


@router.post("/", response_model=Session, status_code=201)
def create_session(
    session_in: SessionCreate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
    service: DatabaseService = Depends(get_service)
):
    # Get current user from session cookie
    user = None
    if current_user_id:
        user = service.get_user(current_user_id)
    if not user:
        # Fallback for unauthenticated users
        user = service.get_first_user()
        if not user:
            user = service.create_user("Host", "host@example.com")
    
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
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{id}/join", response_model=Session)
def join_session(
    id: str,
    body: SessionJoin,
    current_user_id: Optional[str] = Depends(get_current_user_id),
    service: DatabaseService = Depends(get_service)
):
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.pin != body.pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")
    
    # Get current user from session cookie
    user = None
    if current_user_id:
        user = service.get_user(current_user_id)
    if not user:
        # Fallback for unauthenticated users
        user = service.get_last_user()
        if not user:
            user = service.create_user("Participant", None)
    
    updated_session = service.join_session(id, user)
    return updated_session


@router.post("/join-by-pin", response_model=Session)
def join_by_pin(
    body: SessionJoin,
    current_user_id: Optional[str] = Depends(get_current_user_id),
    service: DatabaseService = Depends(get_service)
):
    # Find session by pin
    session = service.get_session_by_pin(body.pin)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get current user from session cookie
    user = None
    if current_user_id:
        user = service.get_user(current_user_id)
    if not user:
        # Fallback for unauthenticated users
        user = service.get_last_user()
        if not user:
            user = service.create_user("Participant", None)
    
    updated_session = service.join_session(session.id, user)
    return updated_session


@router.put("/{id}/code")
def update_code(id: str, body: dict, service: DatabaseService = Depends(get_service)):
    if not service.update_session_code(id, body.get("code", "")):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Code updated"}


@router.put("/{id}/language")
def update_language(id: str, body: dict, service: DatabaseService = Depends(get_service)):
    if not service.update_session_language(id, body.get("language")):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Language updated"}


@router.put("/{id}/cursor")
def update_cursor(id: str, body: dict, service: DatabaseService = Depends(get_service)):
    user_id = body.get("userId")
    position = body.get("position", {})
    if not service.update_cursor_position(id, user_id, position.get("line"), position.get("column")):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Cursor updated"}


@router.post("/{id}/leave")
def leave_session(id: str, service: DatabaseService = Depends(get_service)):
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # In mock, we don't know WHO is leaving unless we have auth
    return {"message": "Left session"}


@router.post("/{id}/end")
def end_session(id: str, service: DatabaseService = Depends(get_service)):
    if not service.update_session_status(id, "ended"):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session ended"}


# Chat Endpoints
@router.get("/{id}/messages", response_model=List[ChatMessage])
def get_messages(id: str, service: DatabaseService = Depends(get_service)):
    return service.get_messages(id)


@router.post("/{id}/messages", response_model=ChatMessage, status_code=201)
def send_message(
    id: str,
    body: ChatMessageCreate,
    current_user_id: Optional[str] = Depends(get_current_user_id),
    service: DatabaseService = Depends(get_service)
):
    session = service.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get current user from session cookie
    user = None
    if current_user_id:
        user = service.get_user(current_user_id)
    if not user:
        # Fallback for unauthenticated users
        user = service.get_first_user()
        if not user:
            user = service.create_user("User", None)
    
    msg = service.add_message(id, user.id, user.username, body.message)
    return msg
