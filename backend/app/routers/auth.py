from fastapi import APIRouter, HTTPException, Depends, status
from ..models.user import User, UserCreate, UserLogin
from ..services.mock_db import db
from ..services.auth_utils import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=User)
def login(user_in: UserLogin):
    user = db.get_user_by_email(user_in.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user_in.password != "password": # Mock password check
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    return user

@router.post("/signup", response_model=User, status_code=201)
def signup(user_in: UserCreate):
    if user_in.email and db.get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    user = db.create_user(user_in.username, user_in.email)
    return user

@router.post("/guest", response_model=User, status_code=201)
def guest_login(user_in: UserCreate): # Reusing UserCreate but only username required effectively
    # Guest logic: create temp user
    user = db.create_user(user_in.username, None)
    return user

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
def get_current_user(user_id: str = "mock_user_id"): 
    # In real app, get from token dependency
    # For now, we need a way to simulate logged in user. 
    # We'll valid user_id passed or default to first user in db or error
    if not db.users:
         raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Just return the first user for mock simplicity if no ID passed in header (which we haven't implemented)
    return list(db.users.values())[0]
