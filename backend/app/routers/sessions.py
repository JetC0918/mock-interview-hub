from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from ..models.session import Session, SessionCreate, SessionJoin, Participant
from ..models.execution import ChatMessage, ChatMessageCreate
from ..models.common import SupportedLanguage, CursorPosition
from ..services.mock_db import db

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("/", response_model=List[Session])
def get_sessions():
    return list(db.sessions.values())

@router.post("/", response_model=Session, status_code=201)
def create_session(session_in: SessionCreate):
    # Mock getting current user (usually first host)
    user = list(db.users.values())[0] if db.users else db.create_user("Host", "host@example.com")
    
    session = db.create_session(
        title=session_in.title,
        host_id=user.id,
        language=session_in.language or SupportedLanguage.PYTHON
    )
    # Host joins automatically
    db.join_session(session.id, user)
    return session

@router.get("/{id}", response_model=Session)
def get_session(id: str):
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{id}/join", response_model=Session)
def join_session(id: str, body: SessionJoin):
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.pin != body.pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")
    
    # Mock user
    user = list(db.users.values())[-1] if db.users else db.create_user("Participant", None)
    
    updated_session = db.join_session(id, user)
    return updated_session

@router.post("/join-by-pin", response_model=Session)
def join_by_pin(body: SessionJoin):
    # Find session by pin
    found_session = None
    for s in db.sessions.values():
        if s.pin == body.pin:
            found_session = s
            break
    
    if not found_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mock user
    user = list(db.users.values())[-1] if db.users else db.create_user("Participant", None)
    
    updated_session = db.join_session(found_session.id, user)
    return updated_session

@router.put("/{id}/code")
def update_code(id: str, body: dict): # body: {code: str}
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.code = body.get("code", "")
    return {"message": "Code updated"}

@router.put("/{id}/language")
def update_language(id: str, body: dict): # body: {language: str}
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.language = body.get("language")
    return {"message": "Language updated"}

@router.put("/{id}/cursor")
def update_cursor(id: str, body: dict): # body: {userId: str, position: CursorPosition}
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Find participant
    userId = body.get("userId")
    for p in session.participants:
        if p.id == userId:
            p.cursorPosition = body.get("position")
            break
    return {"message": "Cursor updated"}

@router.post("/{id}/leave")
def leave_session(id: str):
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # In mock, we don't know WHO is leaving unless we have auth.
    # We'll just say ok for now. 
    return {"message": "Left session"}

@router.post("/{id}/end")
def end_session(id: str):
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = "ended"
    return {"message": "Session ended"}

# Chat Endpoints
@router.get("/{id}/messages", response_model=List[ChatMessage])
def get_messages(id: str):
    return db.get_messages(id)

@router.post("/{id}/messages", response_model=ChatMessage, status_code=201)
def send_message(id: str, body: ChatMessageCreate):
    session = db.get_session(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mock user
    user = list(db.users.values())[0] if db.users else db.create_user("User", None)
    
    msg = db.add_message(id, user.id, user.username, body.message)
    return msg
