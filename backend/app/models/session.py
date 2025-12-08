from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum
from .common import SupportedLanguage, Role, CursorPosition
from .problem import Problem

class SessionStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"

class Participant(BaseModel):
    id: str
    username: str
    avatar: Optional[str] = None
    role: Role
    cursorPosition: Optional[CursorPosition] = None
    isTyping: bool = False
    color: Optional[str] = None
    joinedAt: datetime

class Session(BaseModel):
    id: str
    pin: str
    hostId: str
    title: str
    description: Optional[str] = None
    language: SupportedLanguage
    participants: List[Participant] = []
    code: str = ""
    status: SessionStatus
    createdAt: datetime
    problem: Optional[Problem] = None

class SessionCreate(BaseModel):
    title: str
    language: Optional[SupportedLanguage] = SupportedLanguage.PYTHON

class SessionJoin(BaseModel):
    pin: str
