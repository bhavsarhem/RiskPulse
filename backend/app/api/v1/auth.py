from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token
from backend.app.schemas.auth import Token, UserCreate, UserResponse, UserLogin
from backend.app.services.auth_service import auth_service
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new user."""
    return auth_service.create_user(db, user_in)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    """Log in with Email and Password."""
    user = auth_service.authenticate_user(db, login_data)
    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login/oauth", response_model=Token)
def login_oauth(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    """OAuth2 compatible token login, for Swagger UI."""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    user = auth_service.authenticate_user(db, login_data)
    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """Get details of current logged-in user."""
    return current_user
