"""Database service layer providing same interface as MockDB for seamless migration."""
import json
import uuid
import hashlib
import secrets
import hmac
import base64
import os
from datetime import datetime, UTC, timedelta
from dataclasses import dataclass
from typing import List, Optional, Literal
from sqlalchemy.orm import Session as DBSession, load_only, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update
import bcrypt

from .models import (
    UserModel, AuthSessionModel, SessionModel, ParticipantModel, ProblemModel,
    ExampleModel, ChatMessageModel, GuestAdmissionAttemptModel, AIRequestModel,
    RoleEnum, SupportedLanguageEnum, SessionStatusEnum, DifficultyEnum
)
from ..models.user import User
from ..models.session import Session, PublicParticipant, PublicSession, Participant, SessionStatus
from ..models.problem import Problem, Example, Difficulty
from ..models.execution import ChatMessage, PublicChatMessage
from ..models.common import SupportedLanguage, Role, CursorPosition


JOIN_SECRET_TTL = timedelta(hours=24)
MAX_SESSION_CODE_LENGTH = 100_000
MAX_CHAT_MESSAGES = 100
MAX_SESSION_PARTICIPANTS = 20
KNOWN_DEMO_EMAILS = {
    "host@example.com",
    "dev@example.com",
    "algo@example.com",
    "frontend@example.com",
}
AI_SYSTEM_USER_ID = "system:ai-assistant"


class AdmissionError(Exception):
    """Stable service error for the admission/lifecycle HTTP matrix."""

    def __init__(self, kind: Literal["not_found", "ended", "invalid_secret", "quota"]):
        super().__init__(kind)
        self.kind = kind


class DuplicateEmailError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


@dataclass(frozen=True)
class RevisionResult:
    kind: Literal["updated", "not_found", "ended", "forbidden", "conflict"]
    revision: int | None = None


@dataclass(frozen=True)
class AIReservation:
    state: Literal["reserved", "complete", "pending", "ambiguous"]
    message: ChatMessage | None = None


class DatabaseService:
    """Database service providing CRUD operations with same interface as MockDB."""

    def __init__(self, db: DBSession):
        self.db = db

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    # ==================== Password Utilities ====================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    # ==================== Authentication Session Methods ====================

    @staticmethod
    def hash_session_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_auth_session(self, user_id: str, lifetime: timedelta | None = None) -> str:
        """Create an opaque token and persist only its hash."""
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        db_session = AuthSessionModel(
            id=str(uuid.uuid4()),
            token_hash=self.hash_session_token(token),
            user_id=user_id,
            created_at=now,
            expires_at=now + (lifetime or timedelta(days=7)),
        )
        self.db.add(db_session)
        self.db.commit()
        return token

    def _new_auth_session(self, user_id: str, lifetime: timedelta | None = None) -> tuple[str, AuthSessionModel]:
        """Build an auth-session row without committing an outer transaction."""
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        return token, AuthSessionModel(
            id=str(uuid.uuid4()),
            token_hash=self.hash_session_token(token),
            user_id=user_id,
            created_at=now,
            expires_at=now + (lifetime or timedelta(days=7)),
        )

    @staticmethod
    def _idempotency_key() -> bytes:
        value = os.environ.get("IDEMPOTENCY_SECRET")
        if not value:
            if os.environ.get("APP_ENV", "development").lower() == "production":
                raise RuntimeError("IDEMPOTENCY_SECRET is required in production")
            value = "development-only-idempotency-secret"
        return value.encode("utf-8")

    @classmethod
    def _guest_attempt_material(
        cls, attempt_id: str, attempt_secret: str, session_id: str, username: str, join_secret: str,
    ) -> tuple[str, str, str, str]:
        attempt_hash = hashlib.sha256(attempt_id.encode("ascii")).hexdigest()
        material = f"{attempt_id}:{attempt_secret}".encode("ascii")
        credential_hash = hmac.new(
            cls._idempotency_key(), b"guest-attempt-v1\0" + material, hashlib.sha256,
        ).hexdigest()
        token_bytes = hmac.new(
            cls._idempotency_key(), b"guest-auth-token-v1\0" + material, hashlib.sha256,
        ).digest()
        token = base64.urlsafe_b64encode(token_bytes).rstrip(b"=").decode("ascii")
        fingerprint = hmac.new(
            cls._idempotency_key(),
            b"guest-semantics-v1\0" + f"{session_id}\0{username}\0{join_secret}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return attempt_hash, credential_hash, fingerprint, token

    def get_user_id_by_session_token(self, token: str) -> Optional[str]:
        """Resolve a token only when current, unrevoked, and tied to a user."""
        db_session = self.db.query(AuthSessionModel).filter(
            AuthSessionModel.token_hash == self.hash_session_token(token),
            AuthSessionModel.revoked_at.is_(None),
        ).first()
        if not db_session:
            return None
        expires_at = db_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            return None
        user = self.db.query(UserModel).filter(UserModel.id == db_session.user_id).first()
        return user.id if user else None

    def revoke_auth_session(self, token: str) -> bool:
        db_session = self.db.query(AuthSessionModel).filter(
            AuthSessionModel.token_hash == self.hash_session_token(token),
            AuthSessionModel.revoked_at.is_(None),
        ).first()
        if not db_session:
            return False
        db_session.revoked_at = datetime.now(UTC)
        self.db.commit()
        return True

    # ==================== User Methods ====================

    def create_user(
        self, 
        username: str, 
        email: Optional[str], 
        password: Optional[str] = None,
        role: Role = Role.PARTICIPANT
    ) -> User:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password) if password else None
        
        db_user = UserModel(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=RoleEnum(role.value) if role else None,
            avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
            created_at=datetime.now(UTC)
        )
        self.db.add(db_user)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            if email and self.db.query(UserModel.id).filter(UserModel.email == email).first():
                raise DuplicateEmailError from error
            raise
        self.db.refresh(db_user)
        return self._user_model_to_pydantic(db_user)

    def signup_with_session(self, username: str, email: str, password: str) -> tuple[User, str]:
        """Create an account and opaque login session in one transaction."""
        db_user = UserModel(
            id=str(uuid.uuid4()),
            username=username,
            email=email.lower(),
            password_hash=self.hash_password(password),
            role=RoleEnum.PARTICIPANT,
            avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
            created_at=datetime.now(UTC),
        )
        token, auth_session = self._new_auth_session(db_user.id)
        self.db.add_all([db_user, auth_session])
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            if self.db.query(UserModel.id).filter(UserModel.email == email.lower()).first():
                raise DuplicateEmailError from error
            raise
        self.db.refresh(db_user)
        return self._user_model_to_pydantic(db_user), token

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._user_model_to_pydantic(db_user) if db_user else None

    def get_user_by_email_with_hash(self, email: str) -> Optional[tuple[User, str]]:
        """Get user by email with password hash for authentication."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not db_user:
            return None
        return self._user_model_to_pydantic(db_user), db_user.password_hash

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._user_model_to_pydantic(db_user) if db_user else None

    def get_first_user(self) -> Optional[User]:
        """Get the first user (for mock purposes)."""
        db_user = self.db.query(UserModel).first()
        return self._user_model_to_pydantic(db_user) if db_user else None

    def get_last_user(self) -> Optional[User]:
        """Get the most recently created user."""
        db_user = self.db.query(UserModel).order_by(UserModel.created_at.desc()).first()
        return self._user_model_to_pydantic(db_user) if db_user else None

    def get_user_count(self) -> int:
        """Get total number of users."""
        return self.db.query(UserModel).count()

    def has_known_demo_accounts(self) -> bool:
        """Return whether a deployment still contains deterministic demo accounts."""
        return self.db.query(UserModel).filter(UserModel.email.in_(KNOWN_DEMO_EMAILS)).first() is not None

    # ==================== Session Methods ====================

    def create_session(
        self, 
        title: str, 
        host_id: str, 
        language: SupportedLanguage
    ) -> Session:
        """Create a new coding session."""
        session_id = str(uuid.uuid4())
        # This is a bearer admission secret, not a human-sized PIN.
        pin = secrets.token_urlsafe(24)
        
        now = datetime.now(UTC)
        db_session = SessionModel(
            id=session_id,
            pin=pin,
            host_id=host_id,
            title=title,
            language=SupportedLanguageEnum(language.value),
            status=SessionStatusEnum.WAITING,
            code="",
            code_revision=0,
            created_at=now,
            join_secret_created_at=now,
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return self._session_model_to_pydantic(db_session)

    def create_hosted_session(
        self, title: str, host_id: str, language: SupportedLanguage, problem_id: str | None = None,
    ) -> Session:
        """Create the session and authoritative host membership atomically."""
        now = datetime.now(UTC)
        db_session = SessionModel(
            id=str(uuid.uuid4()), pin=secrets.token_urlsafe(24), host_id=host_id,
            title=title, language=SupportedLanguageEnum(language.value),
            status=SessionStatusEnum.WAITING, code="", code_revision=0,
            problem_id=problem_id, created_at=now, join_secret_created_at=now,
        )
        self.db.add(db_session)
        self.db.add(ParticipantModel(
            session_id=db_session.id, user_id=host_id, role=RoleEnum.HOST, joined_at=now,
        ))
        self.db.commit()
        self.db.refresh(db_session)
        return self._session_model_to_pydantic(db_session)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        return self._session_model_to_pydantic(db_session) if db_session else None

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions."""
        db_sessions = self.db.query(SessionModel).all()
        return [self._session_model_to_pydantic(s) for s in db_sessions]

    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Session]:
        """List a user's sessions without materializing the potentially large code body."""
        rows = (
            self.db.query(SessionModel)
            .options(
                load_only(
                    SessionModel.id, SessionModel.pin, SessionModel.host_id,
                    SessionModel.title, SessionModel.description, SessionModel.language,
                    SessionModel.status, SessionModel.created_at, SessionModel.problem_id,
                    SessionModel.code_revision,
                ),
                selectinload(SessionModel.participants).selectinload(ParticipantModel.user),
                selectinload(SessionModel.problem).selectinload(ProblemModel.examples),
            )
            .join(ParticipantModel, ParticipantModel.session_id == SessionModel.id)
            .filter(
                ParticipantModel.user_id == user_id,
                SessionModel.status != SessionStatusEnum.ENDED,
            )
            .order_by(SessionModel.created_at.desc())
            .limit(max(1, min(limit, 50)))
            .all()
        )
        return [self._session_model_to_pydantic(row, include_code=False) for row in rows]

    @staticmethod
    def _join_secret_expired(db_session: SessionModel) -> bool:
        # A legacy row with no authoritative rotation timestamp has unknown
        # secret age.  Fail closed instead of silently renewing a bearer
        # credential from the general session creation timestamp.
        created_at = db_session.join_secret_created_at
        if created_at is None:
            return True
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        return created_at + JOIN_SECRET_TTL <= datetime.now(UTC)

    def get_session_by_pin(self, pin: str, include_ended: bool = False) -> Optional[Session]:
        """Find a session by secret while enforcing its finite admission lifetime."""
        db_session = self.db.query(SessionModel).filter(SessionModel.pin == pin).first()
        if not db_session or self._join_secret_expired(db_session):
            return None
        if not include_ended and db_session.status == SessionStatusEnum.ENDED:
            return None
        return self._session_model_to_pydantic(db_session)

    @staticmethod
    def _assert_admission(db_session: SessionModel | None, secret: str) -> SessionModel:
        if db_session is None:
            raise AdmissionError("not_found")
        if db_session.status == SessionStatusEnum.ENDED:
            raise AdmissionError("ended")
        if DatabaseService._join_secret_expired(db_session) or not hmac.compare_digest(db_session.pin, secret):
            raise AdmissionError("invalid_secret")
        return db_session

    def admit_user(self, session_id: str, secret: str, user_id: str) -> Session:
        """Serialize admission against end/rotate and add membership idempotently."""
        db_session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .with_for_update()
            .first()
        )
        self._assert_admission(db_session, secret)
        existing = self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).first()
        if not existing:
            count = self.db.query(ParticipantModel.id).filter(
                ParticipantModel.session_id == session_id,
            ).count()
            if count >= MAX_SESSION_PARTICIPANTS:
                self.db.rollback()
                raise AdmissionError("quota")
            self.db.add(ParticipantModel(
                session_id=session_id,
                user_id=user_id,
                role=RoleEnum.HOST if db_session.host_id == user_id else RoleEnum.PARTICIPANT,
                joined_at=datetime.now(UTC),
            ))
            try:
                self.db.flush()
            except IntegrityError:
                self.db.rollback()
                current = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
                self._assert_admission(current, secret)
                membership = self.db.query(ParticipantModel.id).filter(
                    ParticipantModel.session_id == session_id,
                    ParticipantModel.user_id == user_id,
                ).first()
                if not membership:
                    raise
                return self._session_model_to_pydantic(current)
        self.db.commit()
        # Reload membership added by this transaction before serializing the
        # response; relationship collections may have been touched by a
        # prior admission check in the same SQLAlchemy session.
        self.db.expire(db_session, ["participants"])
        self.db.refresh(db_session)
        return self._session_model_to_pydantic(db_session)

    def admit_user_by_secret(self, secret: str, user_id: str) -> Session:
        db_session = (
            self.db.query(SessionModel)
            .filter(SessionModel.pin == secret)
            .with_for_update()
            .first()
        )
        if db_session is None:
            # Without a session ID, an absent/rotated secret is an invalid
            # credential rather than evidence that a specific session exists.
            raise AdmissionError("invalid_secret")
        return self.admit_user(db_session.id, secret, user_id)

    def create_guest_admission(
        self, session_id: str, secret: str, username: str, attempt_id: str, attempt_secret: str,
    ) -> tuple[User, Session, str]:
        """Validate first, then create guest, membership, and auth session atomically."""
        attempt_hash, credential_hash, fingerprint, token = self._guest_attempt_material(
            attempt_id, attempt_secret, session_id, username, secret,
        )
        db_session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .with_for_update()
            .first()
        )
        existing_attempt = self.db.query(GuestAdmissionAttemptModel).filter(
            GuestAdmissionAttemptModel.attempt_id_hash == attempt_hash,
        ).with_for_update().first()
        if existing_attempt:
            # Idempotent retries may replay a committed response, but terminal
            # lifecycle state always wins. Never re-admit after session end.
            if db_session is None:
                self.db.rollback()
                raise AdmissionError("not_found")
            if db_session.status == SessionStatusEnum.ENDED:
                self.db.rollback()
                raise AdmissionError("ended")
            if (
                not hmac.compare_digest(existing_attempt.credential_hash, credential_hash)
                or not hmac.compare_digest(existing_attempt.fingerprint, fingerprint)
                or existing_attempt.session_id != session_id
            ):
                self.db.rollback()
                raise IdempotencyConflictError
            if self._utc(existing_attempt.expires_at) <= datetime.now(UTC):
                self.db.rollback()
                raise AdmissionError("invalid_secret")
            user = self.db.query(UserModel).filter(UserModel.id == existing_attempt.user_id).first()
            membership = self.db.query(ParticipantModel.id).filter(
                ParticipantModel.session_id == session_id,
                ParticipantModel.user_id == existing_attempt.user_id,
            ).first()
            auth_session = self.db.query(AuthSessionModel).filter(
                AuthSessionModel.token_hash == self.hash_session_token(token),
                AuthSessionModel.revoked_at.is_(None),
            ).first()
            if not user or not db_session or not membership or not auth_session:
                self.db.rollback()
                raise IdempotencyConflictError
            user_dto = self._user_model_to_pydantic(user)
            session_dto = self._session_model_to_pydantic(db_session).model_copy(update={"pin": secret})
            self.db.rollback()
            return user_dto, session_dto, token
        self._assert_admission(db_session, secret)
        if self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id,
        ).count() >= MAX_SESSION_PARTICIPANTS:
            self.db.rollback()
            raise AdmissionError("quota")
        now = datetime.now(UTC)
        db_user = UserModel(
            id=str(uuid.uuid4()), username=username, email=None, password_hash=None,
            role=RoleEnum.PARTICIPANT,
            avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}", created_at=now,
        )
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=7)
        auth_session = AuthSessionModel(
            id=str(uuid.uuid4()), token_hash=self.hash_session_token(token),
            user_id=db_user.id, created_at=now, expires_at=expires_at,
        )
        participant = ParticipantModel(
            session_id=session_id, user_id=db_user.id, role=RoleEnum.PARTICIPANT, joined_at=now,
        )
        attempt = GuestAdmissionAttemptModel(
            attempt_id_hash=attempt_hash, credential_hash=credential_hash,
            fingerprint=fingerprint,
            session_id=session_id, user_id=db_user.id, expires_at=expires_at, created_at=now,
        )
        self.db.add_all([db_user, auth_session, participant, attempt])
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            concurrent = self.db.query(GuestAdmissionAttemptModel).filter(
                GuestAdmissionAttemptModel.attempt_id_hash == attempt_hash,
            ).first()
            if concurrent:
                return self.create_guest_admission(
                    session_id, secret, username, attempt_id, attempt_secret,
                )
            raise
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(db_user)
        self.db.refresh(db_session)
        return self._user_model_to_pydantic(db_user), self._session_model_to_pydantic(db_session), token

    def rotate_join_secret(self, session_id: str) -> Optional[str]:
        """Rotate the bearer join secret and restart its finite TTL."""
        now = datetime.now(UTC)
        new_secret = secrets.token_urlsafe(24)
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).with_for_update().first()
        if not db_session or db_session.status == SessionStatusEnum.ENDED:
            self.db.rollback()
            return None
        db_session.pin = new_secret
        db_session.join_secret_created_at = now
        self.db.commit()
        return new_secret

    def join_session(self, session_id: str, user: User) -> Optional[Session]:
        """Add user to a non-ended session as participant."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
            return None
        if db_session.status == SessionStatusEnum.ENDED:
            return None

        # Check if already participating
        existing = self.db.query(ParticipantModel).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user.id
        ).first()
        
        if not existing:
            role = RoleEnum.HOST if user.id == db_session.host_id else RoleEnum.PARTICIPANT
            participant = ParticipantModel(
                session_id=session_id,
                user_id=user.id,
                role=role,
                joined_at=datetime.now(UTC)
            )
            self.db.add(participant)
            try:
                self.db.commit()
            except IntegrityError:
                # A concurrent join may have inserted the same association.
                self.db.rollback()
            self.db.refresh(db_session)

        return self._session_model_to_pydantic(db_session)

    def _classify_revision_failure(self, session_id: str, user_id: str) -> RevisionResult:
        row = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not row:
            return RevisionResult("not_found")
        if row.status == SessionStatusEnum.ENDED:
            return RevisionResult("ended", row.code_revision)
        member = self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).first()
        if not member:
            return RevisionResult("forbidden", row.code_revision)
        return RevisionResult("conflict", row.code_revision)

    def update_session_code(self, session_id: str, user_id: str, code: str, base_revision: int) -> RevisionResult:
        """Compare-and-swap shared code; stale writers never overwrite newer state."""
        if len(code) > MAX_SESSION_CODE_LENGTH:
            return RevisionResult("conflict")
        member_exists = select(ParticipantModel.id).where(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).exists()
        result = self.db.execute(
            update(SessionModel)
            .where(
                SessionModel.id == session_id,
                SessionModel.status != SessionStatusEnum.ENDED,
                SessionModel.code_revision == base_revision,
                member_exists,
            )
            .values(code=code, code_revision=SessionModel.code_revision + 1)
            .returning(SessionModel.code_revision)
        ).scalar_one_or_none()
        if result is not None:
            self.db.commit()
            return RevisionResult("updated", result)
        self.db.rollback()
        return self._classify_revision_failure(session_id, user_id)

    def update_session_language(self, session_id: str, user_id: str, language: str, base_revision: int) -> RevisionResult:
        """Update session language while the session is open."""
        try:
            db_language = SupportedLanguageEnum(language)
        except (TypeError, ValueError):
            return RevisionResult("conflict")
        member_exists = select(ParticipantModel.id).where(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).exists()
        result = self.db.execute(
            update(SessionModel)
            .where(
                SessionModel.id == session_id,
                SessionModel.status != SessionStatusEnum.ENDED,
                SessionModel.code_revision == base_revision,
                member_exists,
            )
            .values(language=db_language, code_revision=SessionModel.code_revision + 1)
            .returning(SessionModel.code_revision)
        ).scalar_one_or_none()
        if result is not None:
            self.db.commit()
            return RevisionResult("updated", result)
        self.db.rollback()
        return self._classify_revision_failure(session_id, user_id)

    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status."""
        try:
            db_status = SessionStatusEnum(status)
        except (TypeError, ValueError):
            return False
        updated = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.status != SessionStatusEnum.ENDED,
        ).update(
            {SessionModel.status: db_status}, synchronize_session=False
        )
        self.db.commit()
        return updated == 1

    def start_session(self, session_id: str, user_id: str) -> str:
        """Atomically transition a host-owned waiting session to active.

        The session row is the lifecycle serialization point shared by start,
        end, join, and secret rotation.  Repeating start on an already-active
        session is idempotent; ended sessions remain terminal.
        """
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
        ).with_for_update().first()
        if not session:
            self.db.rollback()
            return "not_found"
        if session.host_id != user_id:
            self.db.rollback()
            return "forbidden"
        if session.status == SessionStatusEnum.ENDED:
            self.db.rollback()
            return "ended"
        if session.status == SessionStatusEnum.ACTIVE:
            self.db.rollback()
            return "active"
        session.status = SessionStatusEnum.ACTIVE
        self.db.commit()
        return "started"

    def end_session(self, session_id: str, user_id: str) -> str:
        """Atomically end a host-owned session, preserving terminal status."""
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
        ).with_for_update().first()
        if not session:
            self.db.rollback()
            return "not_found"
        if session.host_id != user_id:
            self.db.rollback()
            return "forbidden"
        if session.status == SessionStatusEnum.ENDED:
            self.db.rollback()
            return "ended"
        session.status = SessionStatusEnum.ENDED
        self.db.commit()
        return "ended_now"

    def update_cursor_position(self, session_id: str, user_id: str, line: int, column: int) -> bool:
        """Update the authenticated participant cursor while the session is open."""
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).with_for_update().first()
        if not session or session.status == SessionStatusEnum.ENDED:
            return False
        participant = self.db.query(ParticipantModel).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id
        ).first()
        if not participant:
            return False
        if line is None or column is None:
            return False
        participant.cursor_line = line
        participant.cursor_column = column
        self.db.commit()
        return True

    # ==================== Chat Message Methods ====================

    def add_message(
        self, 
        session_id: str, 
        user_id: str, 
        username: str, 
        text: str
    ) -> Optional[ChatMessage]:
        """Add a chat message to session."""
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).with_for_update().first()
        if not session or session.status == SessionStatusEnum.ENDED:
            return None
        member = self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).first()
        if not member:
            self.db.rollback()
            return None
        msg_id = str(uuid.uuid4())
        db_msg = ChatMessageModel(
            id=msg_id,
            session_id=session_id,
            user_id=user_id,
            username=username,
            message=text,
            timestamp=datetime.now(UTC)
        )
        self.db.add(db_msg)
        self.db.commit()
        self.db.refresh(db_msg)
        return self._message_model_to_pydantic(db_msg)

    def add_ai_exchange(
        self, session_id: str, user_id: str, username: str, prompt: str, reply: str,
    ) -> Optional[ChatMessage]:
        """Persist a completed user/assistant exchange as one lifecycle-checked unit."""
        session = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).with_for_update().first()
        if not session or session.status == SessionStatusEnum.ENDED:
            self.db.rollback()
            return None
        member = self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).first()
        if not member:
            self.db.rollback()
            return None
        now = datetime.now(UTC)
        if not self.db.query(UserModel.id).filter(UserModel.id == AI_SYSTEM_USER_ID).first():
            self.db.add(UserModel(
                id=AI_SYSTEM_USER_ID, username="AI Assistant", email=None,
                password_hash=None, role=RoleEnum.SPECTATOR, created_at=now,
            ))
            self.db.flush()
        user_message = ChatMessageModel(
            id=str(uuid.uuid4()), session_id=session_id, user_id=user_id,
            username=username, message=prompt, timestamp=now,
            author_type="user",
        )
        assistant_message = ChatMessageModel(
            id=str(uuid.uuid4()), session_id=session_id, user_id=AI_SYSTEM_USER_ID,
            username="AI Assistant", message=reply, timestamp=now + timedelta(microseconds=1),
            author_type="assistant",
        )
        self.db.add_all([user_message, assistant_message])
        self.db.commit()
        self.db.refresh(assistant_message)
        return self._message_model_to_pydantic(assistant_message)

    def reserve_ai_request(
        self, session_id: str, user_id: str, request_id: str, fingerprint: str,
        prompt: str, prompted_at: datetime,
    ) -> AIReservation:
        """Reserve exactly one provider call for a logical client request."""
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).with_for_update().first()
        if not session:
            self.db.rollback()
            raise AdmissionError("not_found")
        if session.status == SessionStatusEnum.ENDED:
            self.db.rollback()
            raise AdmissionError("ended")
        member = self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id, ParticipantModel.user_id == user_id,
        ).first()
        if not member:
            self.db.rollback()
            raise PermissionError
        request_hash = hashlib.sha256(request_id.encode("ascii")).hexdigest()
        existing = self.db.query(AIRequestModel).filter(
            AIRequestModel.session_id == session_id,
            AIRequestModel.user_id == user_id,
            AIRequestModel.request_id_hash == request_hash,
        ).with_for_update().first()
        now = datetime.now(UTC)
        if existing:
            if not hmac.compare_digest(existing.fingerprint, fingerprint):
                self.db.rollback()
                raise IdempotencyConflictError
            if existing.status == "complete":
                message = self.db.query(ChatMessageModel).filter(
                    ChatMessageModel.id == existing.response_message_id,
                ).first()
                if not message:
                    existing.status = "ambiguous"
                    existing.updated_at = now
                    self.db.commit()
                    return AIReservation("ambiguous")
                result = AIReservation("complete", self._message_model_to_pydantic(message))
                self.db.rollback()
                return result
            if existing.status == "pending" and self._utc(existing.lease_expires_at) <= now:
                existing.status = "ambiguous"
                existing.updated_at = now
                self.db.commit()
                return AIReservation("ambiguous")
            if existing.status in {"pending", "ambiguous"}:
                self.db.rollback()
                return AIReservation(existing.status)
            existing.status = "pending"
            existing.lease_expires_at = now + timedelta(seconds=40)
            existing.updated_at = now
            self.db.commit()
            return AIReservation("reserved")
        self.db.add(AIRequestModel(
            id=str(uuid.uuid4()), session_id=session_id, user_id=user_id,
            request_id_hash=request_hash, fingerprint=fingerprint, prompt=prompt, status="pending",
            prompted_at=prompted_at, lease_expires_at=now + timedelta(seconds=40),
            created_at=now, updated_at=now,
        ))
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return self.reserve_ai_request(
                session_id, user_id, request_id, fingerprint, prompt, prompted_at,
            )
        return AIReservation("reserved")

    def finish_ai_request(
        self, session_id: str, user_id: str, request_id: str, reply: str,
    ) -> ChatMessage:
        request_hash = hashlib.sha256(request_id.encode("ascii")).hexdigest()
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).with_for_update().first()
        if not session or session.status == SessionStatusEnum.ENDED:
            self.db.rollback()
            raise AdmissionError("ended" if session else "not_found")
        record = self.db.query(AIRequestModel).filter(
            AIRequestModel.session_id == session_id, AIRequestModel.user_id == user_id,
            AIRequestModel.request_id_hash == request_hash,
        ).with_for_update().first()
        if not record or record.status != "pending":
            self.db.rollback()
            raise IdempotencyConflictError
        member = self.db.query(ParticipantModel.id).filter(
            ParticipantModel.session_id == session_id, ParticipantModel.user_id == user_id,
        ).first()
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not member or not user:
            self.db.rollback()
            raise PermissionError
        now = datetime.now(UTC)
        user_message = ChatMessageModel(
            id=str(uuid.uuid4()), session_id=session_id, user_id=user_id,
            username=user.username, message=record.prompt, timestamp=self._utc(record.prompted_at),
            author_type="user",
        )
        assistant_message = ChatMessageModel(
            id=str(uuid.uuid4()), session_id=session_id, user_id=AI_SYSTEM_USER_ID,
            username="AI Assistant", message=reply, timestamp=now, author_type="assistant",
        )
        self.db.add_all([user_message, assistant_message])
        record.status = "complete"
        record.response_message_id = assistant_message.id
        record.updated_at = now
        self.db.commit()
        self.db.refresh(assistant_message)
        return self._message_model_to_pydantic(assistant_message)

    def mark_ai_request(self, session_id: str, user_id: str, request_id: str, ambiguous: bool) -> None:
        request_hash = hashlib.sha256(request_id.encode("ascii")).hexdigest()
        self.db.query(AIRequestModel).filter(
            AIRequestModel.session_id == session_id, AIRequestModel.user_id == user_id,
            AIRequestModel.request_id_hash == request_hash,
            AIRequestModel.status == "pending",
        ).update({
            AIRequestModel.status: "ambiguous" if ambiguous else "failed",
            AIRequestModel.updated_at: datetime.now(UTC),
        }, synchronize_session=False)
        self.db.commit()

    def get_messages(self, session_id: str, limit: int = MAX_CHAT_MESSAGES) -> List[ChatMessage]:
        """Get the newest bounded page of messages for a session."""
        limit = max(1, min(limit, MAX_CHAT_MESSAGES))
        db_msgs = self.db.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.timestamp.desc()).limit(limit).all()
        db_msgs.reverse()
        return [self._message_model_to_pydantic(m) for m in db_msgs]

    def get_public_messages(self, session_id: str, limit: int = 50) -> List[PublicChatMessage]:
        return [
            PublicChatMessage(
                username=message.username, authorType=message.authorType,
                message=message.message, timestamp=message.timestamp,
            )
            for message in self.get_messages(session_id, min(limit, 50))
        ]

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """Remove a participant, while keeping the host association authoritative."""
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).with_for_update().first()
        if not session or session.status == SessionStatusEnum.ENDED or user_id == session.host_id:
            return False
        participant = self.db.query(ParticipantModel).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id,
        ).first()
        if not participant:
            return False
        self.db.delete(participant)
        self.db.commit()
        return True

    # ==================== Problem Methods ====================

    def create_problem(
        self,
        problem_id: str,
        title: str,
        description: str,
        examples: List[dict],
        constraints: List[str],
        difficulty: Difficulty
    ) -> Problem:
        """Create a new coding problem."""
        db_problem = ProblemModel(
            id=problem_id,
            title=title,
            description=description,
            constraints=json.dumps(constraints),
            difficulty=DifficultyEnum(difficulty.value)
        )
        self.db.add(db_problem)
        
        for ex in examples:
            example = ExampleModel(
                problem_id=problem_id,
                input=ex.get("input", ""),
                output=ex.get("output", ""),
                explanation=ex.get("explanation")
            )
            self.db.add(example)
        
        self.db.commit()
        self.db.refresh(db_problem)
        return self._problem_model_to_pydantic(db_problem)

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        """Get problem by ID."""
        db_problem = self.db.query(ProblemModel).filter(ProblemModel.id == problem_id).first()
        return self._problem_model_to_pydantic(db_problem) if db_problem else None

    def get_all_problems(self) -> List[Problem]:
        """Get all problems."""
        db_problems = self.db.query(ProblemModel).all()
        return [self._problem_model_to_pydantic(p) for p in db_problems]

    def assign_problem_to_session(self, session_id: str, problem_id: str) -> bool:
        """Assign a problem to a session."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
            return False
        db_session.problem_id = problem_id
        self.db.commit()
        return True

    def get_random_problem(self) -> Optional[Problem]:
        """Get a random problem from the database."""
        db_problem = self.db.query(ProblemModel).first()
        return self._problem_model_to_pydantic(db_problem) if db_problem else None

    # ==================== Conversion Helpers ====================

    def _user_model_to_pydantic(self, db_user: UserModel) -> User:
        """Convert SQLAlchemy UserModel to Pydantic User."""
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            avatar=db_user.avatar,
            role=Role(db_user.role.value) if db_user.role else None,
            createdAt=self._utc(db_user.created_at)
        )

    def _session_model_to_pydantic(self, db_session: SessionModel, include_code: bool = True) -> Session:
        """Convert SQLAlchemy SessionModel to Pydantic Session."""
        participants = []
        for p in db_session.participants:
            cursor_pos = None
            if p.cursor_line is not None and p.cursor_column is not None:
                cursor_pos = CursorPosition(line=p.cursor_line, column=p.cursor_column)
            
            participants.append(Participant(
                id=p.user_id,
                username=p.user.username,
                avatar=p.user.avatar,
                role=Role(p.role.value),
                cursorPosition=cursor_pos,
                isTyping=p.is_typing,
                color=p.color,
                joinedAt=self._utc(p.joined_at)
            ))

        problem = None
        if db_session.problem:
            problem = self._problem_model_to_pydantic(db_session.problem)

        return Session(
            id=db_session.id,
            pin=db_session.pin,
            hostId=db_session.host_id,
            title=db_session.title,
            description=db_session.description,
            language=SupportedLanguage(db_session.language.value),
            participants=participants,
            code=(db_session.code or "") if include_code else "",
            codeRevision=db_session.code_revision or 0,
            status=SessionStatus(db_session.status.value),
            createdAt=self._utc(db_session.created_at),
            problem=problem
        )

    def get_public_session(self, session_id: str) -> Optional[PublicSession]:
        """Return the intentionally restricted direct-link session projection."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
            return None
        return self._public_session_model_to_pydantic(db_session)

    def get_public_sessions(self, limit: int = 50) -> List[PublicSession]:
        """Return a bounded list of sessions safe for unauthenticated spectating."""
        limit = max(1, min(limit, 50))
        db_sessions = self.db.query(SessionModel).options(
            load_only(
                SessionModel.id, SessionModel.title, SessionModel.description,
                SessionModel.language, SessionModel.status, SessionModel.created_at,
                SessionModel.problem_id, SessionModel.code_revision,
            ),
            selectinload(SessionModel.participants).selectinload(ParticipantModel.user),
            selectinload(SessionModel.problem).selectinload(ProblemModel.examples),
        ).filter(
            # Waiting sessions are lobbies, not live spectator targets.  They
            # become discoverable only after the host's atomic start action.
            SessionModel.status == SessionStatusEnum.ACTIVE,
        ).order_by(SessionModel.created_at.desc()).limit(limit).all()
        return [self._public_session_model_to_pydantic(session, include_code=False) for session in db_sessions]

    def _public_session_model_to_pydantic(self, db_session: SessionModel, include_code: bool = True) -> PublicSession:
        """Convert an ORM session to the intentionally restricted public projection."""
        if not include_code:
            participants = [
                PublicParticipant(
                    username=participant.user.username,
                    avatar=participant.user.avatar,
                    role=Role(participant.role.value),
                    cursorPosition=(
                        CursorPosition(line=participant.cursor_line, column=participant.cursor_column)
                        if participant.cursor_line is not None and participant.cursor_column is not None else None
                    ),
                    isTyping=participant.is_typing,
                    color=participant.color,
                    joinedAt=self._utc(participant.joined_at),
                )
                for participant in db_session.participants
            ]
            return PublicSession(
                id=db_session.id, title=db_session.title, description=db_session.description,
                language=SupportedLanguage(db_session.language.value), participants=participants,
                code="", codeRevision=db_session.code_revision or 0,
                status=SessionStatus(db_session.status.value), createdAt=self._utc(db_session.created_at),
                problem=self._problem_model_to_pydantic(db_session.problem) if db_session.problem else None,
            )
        session = self._session_model_to_pydantic(db_session, include_code=include_code)
        return PublicSession(
            id=session.id,
            title=session.title,
            description=session.description,
            language=session.language,
            participants=[
                PublicParticipant(**participant.model_dump(exclude={"id"}))
                for participant in session.participants
            ],
            code=session.code,
            codeRevision=session.codeRevision,
            status=session.status,
            createdAt=session.createdAt,
            problem=session.problem,
        )

    def _problem_model_to_pydantic(self, db_problem: ProblemModel) -> Problem:
        """Convert SQLAlchemy ProblemModel to Pydantic Problem."""
        examples = [
            Example(
                input=ex.input,
                output=ex.output,
                explanation=ex.explanation
            ) for ex in db_problem.examples
        ]
        return Problem(
            id=db_problem.id,
            title=db_problem.title,
            description=db_problem.description,
            examples=examples,
            constraints=json.loads(db_problem.constraints),
            difficulty=Difficulty(db_problem.difficulty.value)
        )

    def _message_model_to_pydantic(self, db_msg: ChatMessageModel) -> ChatMessage:
        """Convert SQLAlchemy ChatMessageModel to Pydantic ChatMessage."""
        return ChatMessage(
            id=db_msg.id,
            participantId="ai-assistant" if db_msg.author_type == "assistant" else db_msg.user_id,
            username=db_msg.username,
            authorType=db_msg.author_type,
            message=db_msg.message,
            timestamp=self._utc(db_msg.timestamp)
        )


def seed_database(db: DBSession):
    """Seed the database with initial data (development only)."""
    import secrets
    import os
    
    service = DatabaseService(db)
    
    # Check if already seeded
    if service.has_known_demo_accounts():
        return
    
    # Create demo users with deterministic passwords for tests
    host = service.create_user(
        username="CodeMaster",
        email="host@example.com",
        password="password",
        role=Role.HOST
    )
    
    participant = service.create_user(
        username="Pythonista",
        email="dev@example.com",
        password="password",
        role=Role.PARTICIPANT
    )
    
    service.create_user(
        username="AlgoGuru",
        email="algo@example.com",
        password="password",
        role=Role.PARTICIPANT
    )
    
    service.create_user(
        username="FrontEndFan",
        email="frontend@example.com",
        password="password",
        role=Role.SPECTATOR
    )
    if not db.query(UserModel.id).filter(UserModel.id == AI_SYSTEM_USER_ID).first():
        db.add(UserModel(
            id=AI_SYSTEM_USER_ID, username="AI Assistant", email=None,
            password_hash=None, role=RoleEnum.SPECTATOR, created_at=datetime.now(UTC),
        ))
        db.commit()
    
    # Create problems
    service.create_problem(
        problem_id="two-sum",
        title="Two Sum",
        description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        examples=[
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"},
            {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"}
        ],
        constraints=["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
        difficulty=Difficulty.EASY
    )
    
    service.create_problem(
        problem_id="reverse-string",
        title="Reverse String",
        description="Write a function that reverses a string. The input string is given as an array of characters s.",
        examples=[
            {"input": 's = ["h","e","l","l","o"]', "output": '["o","l","l","e","h"]'},
            {"input": 's = ["H","a","n","n","a","h"]', "output": '["h","a","n","n","a","H"]'}
        ],
        constraints=["1 <= s.length <= 10^5"],
        difficulty=Difficulty.EASY
    )
    
    # Create a session
    session = service.create_hosted_session(
        title="Python Interview Practice",
        host_id=host.id,
        language=SupportedLanguage.PYTHON
    )
    
    # Assign the Two Sum problem to this session
    service.assign_problem_to_session(session.id, "two-sum")
    
    # Update session with initial code and status
    service.update_session_code(
        session.id, host.id,
        "def two_sum(nums, target):\n    # Write your code here\n    pass\n", 0,
    )
    service.update_session_status(session.id, "active")
    
    # Add participants
    service.join_session(session.id, participant)
    
    print("Database seeded successfully!")
