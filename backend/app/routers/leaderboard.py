from fastapi import APIRouter
from typing import List
from ..models.common import Role
from ..models.user import User

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/", response_model=List[dict])
def get_leaderboard():
    # Mock data
    return [
        {
            "rank": 1,
            "userId": "u1",
            "username": "CodeMaster",
            "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=CodeMaster",
            "sessionsCompleted": 42,
            "avgScore": 98.5,
            "totalTime": "120h"
        },
        {
            "rank": 2,
            "userId": "u2",
            "username": "BugHunter",
            "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=BugHunter",
            "sessionsCompleted": 30,
            "avgScore": 95.0,
            "totalTime": "80h"
        }
    ]
