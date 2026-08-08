"""Database service layer providing same interface as MockDB for seamless migration."""
import json
import uuid
import hashlib
import secrets
from datetime import datetime, UTC, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError
import bcrypt

from .models import (
    UserModel, AuthSessionModel, SessionModel, ParticipantModel, ProblemModel,
    ExampleModel, ChatMessageModel,
    RoleEnum, SupportedLanguageEnum, SessionStatusEnum, DifficultyEnum
)
from ..models.user import User
from ..models.session import Session, PublicParticipant, PublicSession, Participant, SessionStatus
from ..models.problem import Problem, Example, Difficulty
from ..models.execution import ChatMessage
from ..models.common import SupportedLanguage, Role, CursorPosition


JOIN_SECRET_TTL = timedelta(hours=24)
MAX_SESSION_CODE_LENGTH = 100_000
MAX_CHAT_MESSAGES = 100
KNOWN_DEMO_EMAILS = {
    "host@example.com",
    "dev@example.com",
    "algo@example.com",
    "frontend@example.com",
}


class DatabaseService:
    """Database service providing CRUD operations with same interface as MockDB."""

    def __init__(self, db: DBSession):
        self.db = db

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
        self.db.commit()
        self.db.refresh(db_user)
        return self._user_model_to_pydantic(db_user)

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
            created_at=now,
            join_secret_created_at=now,
        )
        self.db.add(db_session)
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

    @staticmethod
    def _join_secret_expired(db_session: SessionModel) -> bool:
        created_at = db_session.join_secret_created_at or db_session.created_at
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

    def rotate_join_secret(self, session_id: str) -> Optional[str]:
        """Rotate the bearer join secret and restart its finite TTL."""
        now = datetime.now(UTC)
        new_secret = secrets.token_urlsafe(24)
        updated = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.status != SessionStatusEnum.ENDED,
        ).update({
            SessionModel.pin: new_secret,
            SessionModel.join_secret_created_at: now,
        }, synchronize_session=False)
        self.db.commit()
        return new_secret if updated == 1 else None

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

    def update_session_code(self, session_id: str, code: str) -> bool:
        """Update session code while the session is open."""
        if len(code) > MAX_SESSION_CODE_LENGTH:
            return False
        updated = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.status != SessionStatusEnum.ENDED,
        ).update({SessionModel.code: code}, synchronize_session=False)
        self.db.commit()
        return updated == 1

    def update_session_language(self, session_id: str, language: str) -> bool:
        """Update session language while the session is open."""
        try:
            db_language = SupportedLanguageEnum(language)
        except (TypeError, ValueError):
            return False
        updated = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.status != SessionStatusEnum.ENDED,
        ).update({SessionModel.language: db_language}, synchronize_session=False)
        self.db.commit()
        return updated == 1

    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status."""
        try:
            db_status = SessionStatusEnum(status)
        except (TypeError, ValueError):
            return False
        updated = self.db.query(SessionModel).filter(SessionModel.id == session_id).update(
            {SessionModel.status: db_status}, synchronize_session=False
        )
        self.db.commit()
        return updated == 1

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

    def get_messages(self, session_id: str, limit: int = MAX_CHAT_MESSAGES) -> List[ChatMessage]:
        """Get the newest bounded page of messages for a session."""
        limit = max(1, min(limit, MAX_CHAT_MESSAGES))
        db_msgs = self.db.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.timestamp.desc()).limit(limit).all()
        db_msgs.reverse()
        return [self._message_model_to_pydantic(m) for m in db_msgs]

    def leave_session(self, session_id: str, user_id: str) -> bool:
        """Remove a participant, while keeping the host association authoritative."""
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session or user_id == session.host_id:
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
            createdAt=db_user.created_at
        )

    def _session_model_to_pydantic(self, db_session: SessionModel) -> Session:
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
                joinedAt=p.joined_at
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
            code=db_session.code or "",
            status=SessionStatus(db_session.status.value),
            createdAt=db_session.created_at,
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
        db_sessions = self.db.query(SessionModel).filter(
            SessionModel.status != SessionStatusEnum.ENDED,
        ).order_by(SessionModel.created_at.desc()).limit(limit).all()
        return [self._public_session_model_to_pydantic(session) for session in db_sessions]

    def _public_session_model_to_pydantic(self, db_session: SessionModel) -> PublicSession:
        """Convert an ORM session to the intentionally restricted public projection."""
        session = self._session_model_to_pydantic(db_session)
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
            participantId=db_msg.user_id,
            username=db_msg.username,
            message=db_msg.message,
            timestamp=db_msg.timestamp
        )


def seed_database(db: DBSession):
    """Seed the database with initial data (development only)."""
    import secrets
    import os
    
    service = DatabaseService(db)
    
    # Check if already seeded
    if service.get_user_count() > 0:
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
    session = service.create_session(
        title="Python Interview Practice",
        host_id=host.id,
        language=SupportedLanguage.PYTHON
    )
    
    # Assign the Two Sum problem to this session
    service.assign_problem_to_session(session.id, "two-sum")
    
    # Update session with initial code and status
    service.update_session_code(
        session.id, 
        "def two_sum(nums, target):\n    # Write your code here\n    pass\n"
    )
    service.update_session_status(session.id, "active")
    
    # Add participants
    service.join_session(session.id, host)
    service.join_session(session.id, participant)
    
    print("Database seeded successfully!")
