from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Example(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None

class Problem(BaseModel):
    id: str
    title: str
    description: str
    examples: List[Example]
    constraints: List[str]
    difficulty: Difficulty

class TestResult(BaseModel):
    passed: bool
    input: str
    expected: str
    actual: str
