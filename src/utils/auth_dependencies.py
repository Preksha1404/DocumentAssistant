from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.orm import Session
from src.models.users import User
from src.utils.auth_functions import verify_token
from src.core.database import get_db
from typing import Optional

def get_current_user(
    access_token: Optional[str] = Cookie(None, include_in_schema=False),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    token = None

    # Check Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # Cookie token
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    token_data = verify_token(token)
    
    user = db.query(User).filter(User.email == token_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user