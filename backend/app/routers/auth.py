from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session as DBSession
from ..models.user import User, UserCreate, UserLogin
from ..database.config import get_db
from ..database.service import DatabaseService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_service(db: DBSession = Depends(get_db)) -> DatabaseService:
    return DatabaseService(db)


@router.post("/login", response_model=User)
def login(user_in: UserLogin, service: DatabaseService = Depends(get_service)):
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
    return user


@router.post("/signup", response_model=User, status_code=201)
def signup(user_in: UserCreate, service: DatabaseService = Depends(get_service)):
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
    return user


@router.post("/guest", response_model=User, status_code=201)
def guest_login(user_in: UserCreate, service: DatabaseService = Depends(get_service)):
    # Guest logic: create temp user without email/password
    user = service.create_user(user_in.username, None)
    return user


@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
def get_current_user(service: DatabaseService = Depends(get_service)):
    # In real app, get from token dependency
    # For now, return first user for mock simplicity
    user = service.get_first_user()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
