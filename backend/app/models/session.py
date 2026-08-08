from pydantic import BaseModel, Field
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


class PublicParticipant(BaseModel):
    """Participant fields safe to expose through a bearer session link."""
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
    participants: List[Participant] = Field(default_factory=list)
    code: str = ""
    status: SessionStatus
    createdAt: datetime
    problem: Optional[Problem] = None


class PublicSession(BaseModel):
    """Restricted session projection for unauthenticated direct-link viewing."""
    id: str
    title: str
    description: Optional[str] = None
    language: SupportedLanguage
    participants: List[PublicParticipant] = Field(default_factory=list)
    code: str = ""
    status: SessionStatus
    createdAt: datetime
    problem: Optional[Problem] = None

class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    language: Optional[SupportedLanguage] = SupportedLanguage.PYTHON

class SessionJoin(BaseModel):
    pin: str = Field(min_length=8, max_length=128)


class SessionCodeUpdate(BaseModel):
    code: str = Field(max_length=100_000)


class SessionLanguageUpdate(BaseModel):
    language: SupportedLanguage


class SessionCursorUpdate(BaseModel):
    position: CursorPosition
