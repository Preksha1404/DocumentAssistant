from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from app.models.users import User
from app.utils.auth_functions import verify_token
from app.core.database import get_db
from typing import Optional

# Auth Dependencies
def get_current_user(
    access_token: Optional[str] = Cookie(None, include_in_schema=False),
    db: Session = Depends(get_db)
):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(access_token)

    user = db.query(User).filter(User.email == token_data.email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user