import os
from fastapi import APIRouter, HTTPException, Depends, status, Response, Cookie, Request
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from ..models.user import User, UserCreate, UserLogin
from ..database.config import get_db
from ..database.service import DatabaseService, DuplicateEmailError
from ..utils.auth_utils import require_auth
from ..utils.rate_limit import limiter
import bcrypt

router = APIRouter(prefix="/auth", tags=["Auth"])

# Cookie settings
COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode("utf-8")


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


def set_secure_cookie(response: Response, token: str):
    """Set an opaque, server-backed session cookie."""
    is_production = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=is_production
    )


@router.post("/login", response_model=User)
def login(
    user_in: UserLogin, 
    response: Response, 
    request: Request,
    service: DatabaseService = Depends(get_service)
):
    """Login with email and password."""
    limiter.check(request, "auth-login", limit=20)
    result = service.get_user_by_email_with_hash(user_in.email)
    if not result:
        service.verify_password(user_in.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    user, password_hash = result
    if not password_hash:
        service.verify_password(user_in.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not service.verify_password(user_in.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    set_secure_cookie(response, service.create_auth_session(user.id))
    return user


@router.post("/signup", response_model=User, status_code=201)
def signup(
    user_in: UserCreate, 
    response: Response, 
    request: Request,
    service: DatabaseService = Depends(get_service)
):
    """Create a new account."""
    limiter.check(request, "auth-signup", limit=10)
    if not user_in.email or not user_in.password:
        raise HTTPException(
            status_code=422,
            detail="Email and password are required"
        )
    try:
        user, token = service.signup_with_session(user_in.username, str(user_in.email), user_in.password)
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Unable to create account")
    set_secure_cookie(response, token)
    return user


@router.post("/logout")
def logout(
    response: Response,
    token: Optional[str] = Cookie(None, alias=COOKIE_NAME),
    service: DatabaseService = Depends(get_service),
):
    """Revoke and clear the current session cookie."""
    if token:
        service.revoke_auth_session(token)
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
def get_current_user(
    user_id: str = Depends(require_auth),
    service: DatabaseService = Depends(get_service)
):
    """Get the current authenticated user."""
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
