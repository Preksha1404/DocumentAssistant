import jwt
import os
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.users import User
from app.schemas.users import UserCreate, UserLogin
from app.utils.auth_functions import get_pwd_hash, verify_pwd, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class AuthService:

    @staticmethod
    def register_user(db: Session, user: UserCreate):
        # Check if email already exists
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Hash password and create new customer
        hashed_password = get_pwd_hash(user.password)
        new_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            phone=user.phone,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user
    
    @staticmethod
    def login_user(credentials: UserLogin, db: Session):
       
        user = db.query(User).filter(User.email == credentials.email).first()

        if not user or not verify_pwd(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE)
        access_token = create_access_token(
            data={
                "id": user.id,
                "email": user.email,
            },
            expires_delta=access_token_expires
        )

        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE)
        refresh_token = create_refresh_token(
            data={
                "id": user.id,
                "email": user.email
            },
            expires_delta=refresh_token_expires
        )

        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)

        return user, access_token, refresh_token

    @staticmethod
    def refresh_token(refresh_token: str, db: Session):
        """
        Validate refresh token and generate new access token.
        Returns: new access token
        """
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("email")

            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.email == email).first()

        if not user or user.refresh_token != refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_access_token(
            data={
                "id": user.id,
                "email": user.email
            },
            expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE)
        )

        return new_access_token