from typing import Dict, List, Optional
from datetime import datetime
import uuid
from ..models.user import User, Role
from ..models.session import Session, SessionStatus, Participant, CursorPosition
from ..models.common import SupportedLanguage
from ..models.execution import ChatMessage
from ..models.problem import Problem, Difficulty, Example

class MockDB:
    def __init__(self):
        self.users: Dict[str, User] = self._seed_users()
        self.sessions: Dict[str, Session] = self._seed_sessions()
        self.messages: Dict[str, List[ChatMessage]] = {} 
        self.problems: Dict[str, Problem] = self._seed_problems()
        
    def _seed_users(self) -> Dict[str, User]:
        users = {}
        # Host
        u1 = User(
            id="u1", username="CodeMaster", email="host@example.com", 
            role=Role.HOST, avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=CodeMaster", 
            createdAt=datetime.now()
        )
        # Participant
        u2 = User(
            id="u2", username="Pythonista", email="dev@example.com", 
            role=Role.PARTICIPANT, avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=Pythonista", 
            createdAt=datetime.now()
        )
        users[u1.id] = u1
        users[u2.id] = u2
        
        # Additional Registered Users (login with password="password")
        u3 = User(
            id="u3", username="AlgoGuru", email="algo@example.com",
            role=Role.PARTICIPANT, avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=AlgoGuru",
            createdAt=datetime.now()
        )
        u4 = User(
            id="u4", username="FrontEndFan", email="frontend@example.com",
            role=Role.SPECTATOR, avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=FrontEndFan",
            createdAt=datetime.now()
        )
        users[u3.id] = u3
        users[u4.id] = u4
        return users

    def _seed_sessions(self) -> Dict[str, Session]:
        # Pre-create an active session
        s1 = Session(
            id="session-1",
            pin="1234",
            hostId="u1",
            title="Python Interview Practice",
            description="Solving Two Sum and other easy problems.",
            language=SupportedLanguage.PYTHON,
            status=SessionStatus.ACTIVE,
            createdAt=datetime.now(),
            participants=[],
            code="def two_sum(nums, target):\n    # Write your code here\n    pass\n",
            problem=None # Will be linked dynamically or manually if needed
        )
        # Add participants to session
        # We need to do this carefully if we were using the real join method affecting session.
        # Here we just manually construct.
        p1 = Participant(
            id="u1", username="CodeMaster", role=Role.HOST, joinedAt=datetime.now(),
            avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=CodeMaster",
            color="#FF5733"
        )
        p2 = Participant(
            id="u2", username="Pythonista", role=Role.PARTICIPANT, joinedAt=datetime.now(),
            avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=Pythonista",
            color="#33FF57"
        )
        s1.participants = [p1, p2]
        
        return {s1.id: s1}

    def _seed_problems(self) -> Dict[str, Problem]:
        p1 = Problem(
            id="two-sum",
            title="Two Sum",
            description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
            examples=[
                Example(input="nums = [2,7,11,15], target = 9", output="[0,1]"),
                Example(input="nums = [3,2,4], target = 6", output="[1,2]")
            ],
            constraints=["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
            difficulty=Difficulty.EASY
        )
        p2 = Problem(
            id="reverse-string",
            title="Reverse String",
            description="Write a function that reverses a string. The input string is given as an array of characters s.",
            examples=[
                Example(input='s = ["h","e","l","l","o"]', output='["o","l","l","e","h"]'),
                Example(input='s = ["H","a","n","n","a","h"]', output='["h","a","n","n","a","H"]')
            ],
            constraints=["1 <= s.length <= 10^5"],
            difficulty=Difficulty.EASY
        )
        return {p1.id: p1, p2.id: p2}

    # User Methods
    def create_user(self, username: str, email: Optional[str], role: Role = Role.PARTICIPANT) -> User:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            createdAt=datetime.now()
        )
        self.users[user_id] = user
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    # Session Methods
    def create_session(self, title: str, host_id: str, language: SupportedLanguage) -> Session:
        session_id = str(uuid.uuid4())
        pin = f"{uuid.uuid4().int % 10000:04d}" # Simple 4 digit pin
        session = Session(
            id=session_id,
            pin=pin,
            hostId=host_id,
            title=title,
            language=language,
            status=SessionStatus.WAITING,
            createdAt=datetime.now(),
            participants=[]
        )
        self.sessions[session_id] = session
        self.messages[session_id] = []
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)
        
    def join_session(self, session_id: str, user: User) -> Optional[Session]:
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Check if already in
        for p in session.participants:
            if p.id == user.id:
                return session

        participant = Participant(
            id=user.id,
            username=user.username,
            avatar=user.avatar,
            role=Role.PARTICIPANT if user.id != session.hostId else Role.HOST,
            joinedAt=datetime.now()
        )
        session.participants.append(participant)
        return session

    def add_message(self, session_id: str, user_id: str, username: str, text: str) -> ChatMessage:
        msg = ChatMessage(
            id=str(uuid.uuid4()),
            participantId=user_id,
            username=username,
            message=text,
            timestamp=datetime.now()
        )
        if session_id in self.messages:
            self.messages[session_id].append(msg)
        return msg

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return self.messages.get(session_id, [])

db = MockDB()
