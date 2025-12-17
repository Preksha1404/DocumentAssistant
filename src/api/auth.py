import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Response, Cookie, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserCreate, UserLogin, UserResponse
from src.utils.auth_dependencies import get_current_user
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return AuthService.register_user(db, user)

@router.post("/login")
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user, access, refresh = AuthService.login_user(credentials, db)

    user_data = UserResponse.model_validate(user).model_dump(mode="json")

    res = JSONResponse(content={
        "user": user_data,
        "message": "Login successful",
        "access_token": access,
        "refresh_token": refresh
    })

    res.set_cookie("access_token", access, httponly=True, secure=True,
                   samesite="None", max_age=24*60*60, path="/")
    res.set_cookie("refresh_token", refresh, httponly=True, secure=True,
                   samesite="None", max_age=7*24*60*60, path="/")

    return res

@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, include_in_schema=False),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access = AuthService.refresh_token(refresh_token, db)
    response.set_cookie("access_token", new_access, httponly=True)
    return {"access_token": new_access}

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user