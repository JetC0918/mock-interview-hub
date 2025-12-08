from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from .common import Role

class User(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    role: Optional[Role] = None
    createdAt: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
