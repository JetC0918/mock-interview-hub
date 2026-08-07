import os
from fastapi import APIRouter, HTTPException, Depends, status, Response, Cookie, Request
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from ..models.user import User, UserCreate, UserLogin
from ..database.config import get_db
from ..database.service import DatabaseService

router = APIRouter(prefix="/auth", tags=["Auth"])

# Cookie settings
COOKIE_NAME = "user_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


def set_secure_cookie(response: Response, user_id: str):
    """Set a secure session cookie."""
    is_production = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(
        key=COOKIE_NAME,
        value=user_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=is_production
    )


@router.post("/login", response_model=User)
def login(
    user_in: UserLogin, 
    response: Response, 
    service: DatabaseService = Depends(get_service)
):
    """Login with email and password."""
    result = service.get_user_by_email_with_hash(user_in.email)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user, password_hash = result
    if not password_hash or not service.verify_password(user_in.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    set_secure_cookie(response, user.id)
    return user


@router.post("/signup", response_model=User, status_code=201)
def signup(
    user_in: UserCreate, 
    response: Response, 
    service: DatabaseService = Depends(get_service)
):
    """Create a new account."""
    if user_in.email and service.get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    user = service.create_user(
        username=user_in.username, 
        email=user_in.email,
        password=user_in.password
    )
    
    set_secure_cookie(response, user.id)
    return user


@router.post("/guest", response_model=User, status_code=201)
def guest_login(
    user_in: UserCreate, 
    response: Response, 
    service: DatabaseService = Depends(get_service)
):
    """Join as a guest."""
    user = service.create_user(user_in.username, None)
    set_secure_cookie(response, user.id)
    return user


@router.post("/logout")
def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
def get_current_user(
    user_id: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    service: DatabaseService = Depends(get_service)
):
    """Get the current authenticated user."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
