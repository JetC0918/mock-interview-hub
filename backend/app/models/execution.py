from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional, Literal
from .common import SupportedLanguage
from .problem import Problem, TestResult

class ChatMessage(BaseModel):
    id: str
    participantId: str
    username: str
    authorType: Literal["user", "assistant"]
    message: str
    timestamp: datetime

class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class PublicChatMessage(BaseModel):
    username: str
    authorType: Literal["user", "assistant"]
    message: str
    timestamp: datetime

class ExecutionRequest(BaseModel):
    code: str
    language: SupportedLanguage

class TestRequest(ExecutionRequest):
    problem: Problem

class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    exitCode: int
    executionTime: float
    testResults: Optional[List[TestResult]] = None
