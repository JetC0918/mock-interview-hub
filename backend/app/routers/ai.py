"""
AI Assistant Router

Provides endpoints for AI-powered coding guidance.
"""
import os
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, constr
from typing import List, Optional
from datetime import datetime, UTC
import uuid

from ..services.ai_service import get_ai_service
from ..database.config import get_db
from ..database.service import DatabaseService
from ..utils.auth_utils import require_auth
from ..utils.rate_limit import limiter

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def get_service(db=Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)

class ProblemExample(BaseModel):
    input: str = Field(default="", max_length=2_000)
    output: str = Field(default="", max_length=2_000)


class ProblemContext(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=8_000)
    difficulty: Optional[str] = Field(default=None, max_length=32)
    examples: List[ProblemExample] = Field(default_factory=list, max_length=10)
    constraints: List[constr(max_length=500)] = Field(default_factory=list, max_length=30)


class AIAssistRequest(BaseModel):
    """Request model for AI assistance."""
    sessionId: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    problemContext: Optional[ProblemContext] = None


class AIAssistResponse(BaseModel):
    """Response model for AI assistance."""
    id: str
    participantId: str
    username: str
    message: str
    timestamp: datetime


@router.post("/assist", response_model=AIAssistResponse)
async def get_ai_assistance(
    request: Request,
    payload: AIAssistRequest,
    user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service),
):
    """
    Get AI-powered guidance for a coding question.
    Requires authentication.
    """
    limiter.check(request, "ai-assist", limit=20)
    session = service.get_session(payload.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status.value == "ended":
        raise HTTPException(status_code=410, detail="Session has ended")
    if user_id not in {participant.id for participant in session.participants}:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")

    try:
        ai_service = get_ai_service()
    except ValueError as e:
        raise HTTPException(
            status_code=503, 
            detail="AI service is temporarily unavailable"
        )
    
    # Remove @AI tag from message if present
    clean_message = payload.message.replace("@AI", "").replace("@ai", "").strip()
    
    if not clean_message:
        raise HTTPException(
            status_code=400,
            detail="Please provide a question after @AI"
        )
    
    # Get AI guidance
    response_text = ai_service.get_guidance(
        user_message=clean_message,
        problem_context=(
            payload.problemContext.model_dump(exclude_none=True)
            if payload.problemContext
            else None
        )
    )
    
    return AIAssistResponse(
        id=str(uuid.uuid4()),
        participantId="ai-assistant",
        username="AI Assistant",
        message=response_text,
        timestamp=datetime.now(UTC)
    )
