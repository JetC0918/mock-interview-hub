from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime, UTC
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
    codeRevision: int = Field(ge=0)
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
    codeRevision: int = Field(ge=0)
    status: SessionStatus
    createdAt: datetime
    problem: Optional[Problem] = None

class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    language: Optional[SupportedLanguage] = SupportedLanguage.PYTHON

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value

class SessionJoin(BaseModel):
    pin: str = Field(min_length=8, max_length=128)

    @field_validator("pin")
    @classmethod
    def validate_secret_format(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("join secret must use the server-issued URL-safe format")
        return value


class GuestSessionJoin(SessionJoin):
    username: str = Field(min_length=1, max_length=80)
    attemptId: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    attemptSecret: str = Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("username must not be blank")
        return value


class SessionCodeUpdate(BaseModel):
    code: str = Field(max_length=100_000)
    baseRevision: int = Field(ge=0)


class SessionRevisionResponse(BaseModel):
    codeRevision: int = Field(ge=0)


class SessionLanguageUpdate(BaseModel):
    language: SupportedLanguage
    baseRevision: int = Field(ge=0)


class SessionCursorUpdate(BaseModel):
    position: CursorPosition


class GuestSessionJoinResponse(BaseModel):
    user: "User"
    session: Session


from .user import User
GuestSessionJoinResponse.model_rebuild()
