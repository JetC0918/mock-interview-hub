"""
AI Assistant Router

Provides endpoints for AI-powered coding guidance.
"""
import os
from fastapi import APIRouter, HTTPException, Request, Depends, Cookie
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, UTC
import uuid

from ..services.ai_service import get_ai_service

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Cookie name for auth check
COOKIE_NAME = "user_id"


class AIAssistRequest(BaseModel):
    """Request model for AI assistance."""
    sessionId: str
    message: str
    problemContext: Optional[dict] = None


class AIAssistResponse(BaseModel):
    """Response model for AI assistance."""
    id: str
    participantId: str
    username: str
    message: str
    timestamp: datetime


@router.post("/assist", response_model=AIAssistResponse)
async def get_ai_assistance(
    request: AIAssistRequest,
    user_id: Optional[str] = Cookie(None, alias=COOKIE_NAME)
):
    """
    Get AI-powered guidance for a coding question.
    Requires authentication.
    """
    # Require authentication to use AI features
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to use AI features"
        )
    
    try:
        ai_service = get_ai_service()
    except ValueError as e:
        raise HTTPException(
            status_code=503, 
            detail="AI service is temporarily unavailable"
        )
    
    # Remove @AI tag from message if present
    clean_message = request.message.replace("@AI", "").replace("@ai", "").strip()
    
    if not clean_message:
        raise HTTPException(
            status_code=400,
            detail="Please provide a question after @AI"
        )
    
    # Get AI guidance
    response_text = ai_service.get_guidance(
        user_message=clean_message,
        problem_context=request.problemContext
    )
    
    return AIAssistResponse(
        id=str(uuid.uuid4()),
        participantId="ai-assistant",
        username="AI Assistant",
        message=response_text,
        timestamp=datetime.now(UTC)
    )
