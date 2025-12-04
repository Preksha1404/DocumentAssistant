from fastapi import HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users import User
from app.utils.auth_dependencies import get_current_user

def require_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Trial active
    if current_user.subscription_status == "trialing":
        if current_user.trial_end and current_user.trial_end > datetime.utcnow():
            return current_user
    
    # Active subscription
    if current_user.subscription_status == "active":
        return current_user

    # Trial expired or subscription canceled
    raise HTTPException(
        status_code=402,
        detail="Your trial has ended. Please subscribe to continue using the AI assistant."
    )