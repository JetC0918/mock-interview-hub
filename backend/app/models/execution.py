from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from .common import SupportedLanguage
from .problem import Problem, TestResult

class ChatMessage(BaseModel):
    id: str
    participantId: str
    username: str
    message: str
    timestamp: datetime

class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)

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
