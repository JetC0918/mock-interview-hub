"""SQLAlchemy ORM models mapping to existing Pydantic schemas."""
from datetime import datetime, UTC
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text,
    Enum as SQLEnum, ForeignKey, Table, UniqueConstraint, CheckConstraint, event, DDL, text
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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    hosted_sessions = relationship("SessionModel", back_populates="host")
    participations = relationship("ParticipantModel", back_populates="user")
    messages = relationship("ChatMessageModel", back_populates="user")
    auth_sessions = relationship("AuthSessionModel", back_populates="user", cascade="all, delete-orphan")


class AuthSessionModel(Base):
    """Opaque, revocable server-side authentication session."""
    __tablename__ = "auth_sessions"

    id = Column(String, primary_key=True, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("UserModel", back_populates="auth_sessions")


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
    __table_args__ = (UniqueConstraint("pin", name="uq_sessions_pin"),)

    id = Column(String, primary_key=True, index=True)
    pin = Column(String, nullable=False, index=True)
    host_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    language = Column(SQLEnum(SupportedLanguageEnum), nullable=False)
    code = Column(Text, default="")
    code_revision = Column(Integer, default=0, server_default=text("0"), nullable=False)
    status = Column(SQLEnum(SessionStatusEnum), nullable=False)
    problem_id = Column(String, ForeignKey("problems.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    # Separate from session creation so rotating a join secret renews its TTL.
    # Nullable keeps databases created before this column readable during the
    # one-time startup migration.
    join_secret_created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"), nullable=False,
    )

    # Relationships
    host = relationship("UserModel", back_populates="hosted_sessions")
    problem = relationship("ProblemModel", back_populates="sessions")
    participants = relationship("ParticipantModel", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")


# Participant (Session-User association with extra data)
class ParticipantModel(Base):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_participants_session_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    color = Column(String, nullable=True)
    cursor_line = Column(Integer, nullable=True)
    cursor_column = Column(Integer, nullable=True)
    is_typing = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    session = relationship("SessionModel", back_populates="participants")
    user = relationship("UserModel", back_populates="participations")


# Chat Message Model
class ChatMessageModel(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("author_type IN ('user', 'assistant')", name="ck_chat_messages_author_type"),
        CheckConstraint(
            "(author_type = 'assistant' AND user_id = 'system:ai-assistant') OR "
            "(author_type = 'user' AND user_id <> 'system:ai-assistant')",
            name="ck_chat_messages_author_identity",
        ),
    )

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    # The AI uses a fixed system user so records remain readable by the prior
    # release during an instant Render rollback.
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    username = Column(String, nullable=False)
    author_type = Column(String, nullable=False, default="user", server_default="user")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    session = relationship("SessionModel", back_populates="messages")
    user = relationship("UserModel", back_populates="messages")


class GuestAdmissionAttemptModel(Base):
    __tablename__ = "guest_admission_attempts"

    attempt_id_hash = Column(String, primary_key=True)
    credential_hash = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AIRequestModel(Base):
    __tablename__ = "ai_requests"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", "request_id_hash", name="uq_ai_request_identity"),
        CheckConstraint("status IN ('pending', 'complete', 'failed', 'ambiguous')", name="ck_ai_requests_status"),
    )

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    request_id_hash = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    prompted_at = Column(DateTime(timezone=True), nullable=False)
    lease_expires_at = Column(DateTime(timezone=True), nullable=False)
    response_message_id = Column(String, ForeignKey("chat_messages.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


# SQLite test/development databases need the same legacy-write compatibility
# as PostgreSQL production. A write that changes code/language without
# explicitly advancing the revision is treated as a prior-release write.
event.listen(
    SessionModel.__table__,
    "after_create",
    DDL("""
    CREATE TRIGGER IF NOT EXISTS bump_session_code_revision
    AFTER UPDATE OF code, language ON sessions
    FOR EACH ROW
    WHEN NEW.code_revision = OLD.code_revision
         AND (NEW.code IS NOT OLD.code OR NEW.language IS NOT OLD.language)
    BEGIN
      UPDATE sessions SET code_revision = OLD.code_revision + 1 WHERE id = OLD.id;
    END
    """).execute_if(dialect="sqlite"),
)
