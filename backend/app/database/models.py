"""SQLAlchemy ORM models mapping to existing Pydantic schemas."""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, 
    Enum as SQLEnum, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from .config import Base
import enum


# Enums matching Pydantic models
class RoleEnum(str, enum.Enum):
    HOST = "host"
    PARTICIPANT = "participant"
    SPECTATOR = "spectator"


class SupportedLanguageEnum(str, enum.Enum):
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"


class SessionStatusEnum(str, enum.Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"


class DifficultyEnum(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# User Model
class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)  # For registered users
    avatar = Column(String, nullable=True)
    role = Column(SQLEnum(RoleEnum), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    hosted_sessions = relationship("SessionModel", back_populates="host")
    participations = relationship("ParticipantModel", back_populates="user")
    messages = relationship("ChatMessageModel", back_populates="user")


# Problem Model
class ProblemModel(Base):
    __tablename__ = "problems"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    constraints = Column(Text, nullable=False)  # JSON-encoded list
    difficulty = Column(SQLEnum(DifficultyEnum), nullable=False)

    # Relationships
    examples = relationship("ExampleModel", back_populates="problem", cascade="all, delete-orphan")
    sessions = relationship("SessionModel", back_populates="problem")


class ExampleModel(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(String, ForeignKey("problems.id"), nullable=False)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    # Relationships
    problem = relationship("ProblemModel", back_populates="examples")


# Session Model
class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    pin = Column(String, nullable=False, index=True)
    host_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    language = Column(SQLEnum(SupportedLanguageEnum), nullable=False)
    code = Column(Text, default="")
    status = Column(SQLEnum(SessionStatusEnum), nullable=False)
    problem_id = Column(String, ForeignKey("problems.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    host = relationship("UserModel", back_populates="hosted_sessions")
    problem = relationship("ProblemModel", back_populates="sessions")
    participants = relationship("ParticipantModel", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")


# Participant (Session-User association with extra data)
class ParticipantModel(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    color = Column(String, nullable=True)
    cursor_line = Column(Integer, nullable=True)
    cursor_column = Column(Integer, nullable=True)
    is_typing = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="participants")
    user = relationship("UserModel", back_populates="participations")


# Chat Message Model
class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    username = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="messages")
    user = relationship("UserModel", back_populates="messages")
