from fastapi import HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.users import User
from src.utils.auth_dependencies import get_current_user

def require_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ACTIVE TRIAL
    if current_user.subscription_status == "trialing":
        if current_user.trial_end and current_user.trial_end > datetime.utcnow():
            return current_user  # allow access
        else:
            # trial expired
            raise HTTPException(
                status_code=402,
                detail="Your free trial has ended. Please upgrade to continue using AI features."
            )

    # ACTIVE SUBSCRIPTION
    if current_user.subscription_status == "active":
        if current_user.current_period_end and current_user.current_period_end > datetime.utcnow():
            return current_user
        else:
            raise HTTPException(
                status_code=402,
                detail="Your subscription has expired. Please renew your plan."
            )

    # EVERYTHING ELSE
    raise HTTPException(
        status_code=402,
        detail="Upgrade required to continue."
    )