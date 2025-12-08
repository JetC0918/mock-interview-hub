from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class SupportedLanguage(str, Enum):
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"

class Role(str, Enum):
    HOST = "host"
    PARTICIPANT = "participant"
    SPECTATOR = "spectator"

class CursorPosition(BaseModel):
    line: int
    column: int
