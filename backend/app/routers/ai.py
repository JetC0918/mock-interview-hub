"""
AI Assistant Router

Provides endpoints for AI-powered coding guidance.
"""
import os
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, constr, model_validator
from typing import List, Optional
from datetime import datetime, UTC
import uuid
import json
import hashlib
import asyncio
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import sessionmaker

from ..services.ai_service import get_ai_service, AIProviderError
from ..database.config import get_db, SessionLocal
from ..database.service import DatabaseService, AdmissionError, IdempotencyConflictError
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
    requestId: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")

    @model_validator(mode="after")
    def validate_prompt(self):
        clean = self.message.strip()
        if clean[:3].lower() == "@ai" and (len(clean) == 3 or clean[3].isspace()):
            clean = clean[3:].strip()
        if not clean:
            raise ValueError("AI message must contain a question")
        return self


class AIAssistResponse(BaseModel):
    """Response model for AI assistance."""
    id: str
    participantId: str
    username: str
    authorType: str
    message: str = Field(max_length=8_000)
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
    limiter.check(request, "ai-assist", limit=20, identity=user_id)

    # Remove @AI tag from message if present
    clean_message = payload.message.strip()
    if clean_message[:3].lower() == "@ai" and (len(clean_message) == 3 or clean_message[3].isspace()):
        clean_message = clean_message[3:].strip()

    context_payload = payload.problemContext.model_dump(exclude_none=True) if payload.problemContext else None
    fingerprint = hashlib.sha256(json.dumps(
        {"message": clean_message, "problemContext": context_payload},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    prompted_at = datetime.now(UTC)
    db_factory = sessionmaker(bind=service.db.get_bind(), autocommit=False, autoflush=False)
    service.db.rollback()

    def reserve_request():
        db = db_factory()
        try:
            return DatabaseService(db).reserve_ai_request(
                payload.sessionId, user_id, payload.requestId, fingerprint,
                payload.message, prompted_at,
            )
        finally:
            db.close()

    try:
        reservation = await run_in_threadpool(reserve_request)
    except AdmissionError as error:
        code = 404 if error.kind == "not_found" else 410
        raise HTTPException(status_code=code, detail="Session not found" if code == 404 else "Session has ended")
    except PermissionError:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    except IdempotencyConflictError:
        raise HTTPException(status_code=409, detail="AI request ID does not match the original input")
    if reservation.state == "complete":
        return AIAssistResponse(**reservation.message.model_dump())
    if reservation.state == "pending":
        raise HTTPException(status_code=409, detail="AI request is already in progress", headers={"Retry-After": "5"})
    if reservation.state == "ambiguous":
        raise HTTPException(status_code=409, detail="AI provider outcome is indeterminate; start a new request to retry")

    def mark_request(ambiguous: bool):
        db = db_factory()
        try:
            DatabaseService(db).mark_ai_request(
                payload.sessionId, user_id, payload.requestId, ambiguous,
            )
        finally:
            db.close()

    try:
        ai_service = get_ai_service()
    except ValueError:
        await run_in_threadpool(mark_request, False)
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable")

    # Get AI guidance
    try:
        response_text = await ai_service.get_guidance(
            user_message=clean_message,
            problem_context=(
                payload.problemContext.model_dump(exclude_none=True)
                if payload.problemContext
                else None
            )
        )
    except AIProviderError as error:
        await run_in_threadpool(mark_request, error.ambiguous)
        detail = "AI provider outcome is indeterminate" if error.ambiguous else "AI provider request failed; please retry"
        raise HTTPException(status_code=502, detail=detail)
    except asyncio.CancelledError:
        await run_in_threadpool(mark_request, True)
        raise
    except Exception:
        await run_in_threadpool(mark_request, True)
        raise HTTPException(status_code=502, detail="AI provider outcome is indeterminate")

    def finish_request():
        db = db_factory()
        try:
            return DatabaseService(db).finish_ai_request(
                payload.sessionId, user_id, payload.requestId, response_text,
            )
        finally:
            db.close()

    try:
        saved = await run_in_threadpool(finish_request)
    except asyncio.CancelledError:
        # A cancellation during the commit boundary leaves the external
        # provider outcome unknowable.  Preserve the fail-closed lease state
        # before propagating cancellation to the server.
        await run_in_threadpool(mark_request, True)
        raise
    except AdmissionError as error:
        raise HTTPException(status_code=410 if error.kind == "ended" else 404, detail="Session has ended" if error.kind == "ended" else "Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="You are not a participant of this session")
    except IdempotencyConflictError:
        await run_in_threadpool(mark_request, True)
        raise HTTPException(status_code=409, detail="AI response could not be committed; outcome is indeterminate")
    except Exception:
        # If the provider succeeded but transcript persistence failed, never
        # silently release the request for an automatic second paid call.
        await run_in_threadpool(mark_request, True)
        raise HTTPException(status_code=502, detail="AI response could not be committed; outcome is indeterminate")
    return AIAssistResponse(**saved.model_dump())
