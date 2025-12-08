"""Database service layer providing same interface as MockDB for seamless migration."""
import json
import uuid
from datetime import datetime, UTC
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
import bcrypt

from .models import (
    UserModel, SessionModel, ParticipantModel, ProblemModel, 
    ExampleModel, ChatMessageModel,
    RoleEnum, SupportedLanguageEnum, SessionStatusEnum, DifficultyEnum
)
from ..models.user import User
from ..models.session import Session, Participant, SessionStatus
from ..models.problem import Problem, Example, Difficulty
from ..models.execution import ChatMessage
from ..models.common import SupportedLanguage, Role, CursorPosition


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

    # ==================== Session Methods ====================

    def create_session(
        self, 
        title: str, 
        host_id: str, 
        language: SupportedLanguage
    ) -> Session:
        """Create a new coding session."""
        session_id = str(uuid.uuid4())
        pin = f"{uuid.uuid4().int % 10000:04d}"
        
        db_session = SessionModel(
            id=session_id,
            pin=pin,
            host_id=host_id,
            title=title,
            language=SupportedLanguageEnum(language.value),
            status=SessionStatusEnum.WAITING,
            code="",
            created_at=datetime.now(UTC)
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

    def get_session_by_pin(self, pin: str) -> Optional[Session]:
        """Find session by PIN."""
        db_session = self.db.query(SessionModel).filter(SessionModel.pin == pin).first()
        return self._session_model_to_pydantic(db_session) if db_session else None

    def join_session(self, session_id: str, user: User) -> Optional[Session]:
        """Add user to session as participant."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
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
            self.db.commit()
            self.db.refresh(db_session)

        return self._session_model_to_pydantic(db_session)

    def update_session_code(self, session_id: str, code: str) -> bool:
        """Update session code."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
            return False
        db_session.code = code
        self.db.commit()
        return True

    def update_session_language(self, session_id: str, language: str) -> bool:
        """Update session language."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
            return False
        db_session.language = SupportedLanguageEnum(language)
        self.db.commit()
        return True

    def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status."""
        db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not db_session:
            return False
        db_session.status = SessionStatusEnum(status)
        self.db.commit()
        return True

    def update_cursor_position(self, session_id: str, user_id: str, line: int, column: int) -> bool:
        """Update participant cursor position."""
        participant = self.db.query(ParticipantModel).filter(
            ParticipantModel.session_id == session_id,
            ParticipantModel.user_id == user_id
        ).first()
        if not participant:
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
    ) -> ChatMessage:
        """Add a chat message to session."""
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

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session."""
        db_msgs = self.db.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.timestamp).all()
        return [self._message_model_to_pydantic(m) for m in db_msgs]

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
    """Seed the database with initial data."""
    service = DatabaseService(db)
    
    # Check if already seeded
    if service.get_user_count() > 0:
        return
    
    # Create users
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
