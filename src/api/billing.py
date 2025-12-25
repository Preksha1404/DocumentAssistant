import stripe
import os
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from src.core.database import get_db
from src.models.users import User
from src.utils.auth_dependencies import get_current_user

# CONFIG
logger = logging.getLogger("billing")
logger.setLevel(logging.INFO)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID = os.getenv("STRIPE_PRICE_ID")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/billing", tags=["Billing"])

# HELPERS
def safe_dt_from_ts(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts))
    except Exception:
        logger.exception("Failed to parse timestamp: %s", ts)
        return None

# API: GET CURRENT SUBSCRIPTION
@router.get("/me/subscription")
def get_subscription_status(current_user: User = Depends(get_current_user)):
    return {
        "subscription_status": current_user.subscription_status,
        "trial_end": current_user.trial_end,
        "current_period_end": current_user.current_period_end,
    }

# API: CREATE CHECKOUT SESSION
@router.post("/create-checkout-session")
def create_checkout_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure Stripe customer exists
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(email=current_user.email)
        current_user.stripe_customer_id = customer.id
        db.commit()

    # Redirect URLs
    if os.getenv("ENV") == "production":
        success_url = f"{os.getenv('FRONTEND_URL')}?page=payment_success"
        cancel_url  = f"{os.getenv('FRONTEND_URL')}?page=payment_cancel"
    else:
        success_url = "http://localhost:8501/?page=payment_success"
        cancel_url  = "http://localhost:8501/?page=payment_cancel"

    # Create checkout with USER METADATA
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=current_user.stripe_customer_id,
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        subscription_data={
            "trial_period_days": 1,
            "metadata": {
                "user_id": str(current_user.id)
            }
        },
        metadata={
            "user_id": str(current_user.id)
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )

    logger.info("Checkout session created for user_id=%s", current_user.id)
    return {"checkout_url": session.url}

# STRIPE WEBHOOK
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except Exception:
        logger.exception("Stripe webhook verification failed")
        return JSONResponse(status_code=400, content={"error": "invalid webhook"})

    etype = event["type"]
    obj = event["data"]["object"]

    try:
        # SUBSCRIPTION CREATED
        if etype == "customer.subscription.created":

            logger.info("SUBSCRIPTION.CREATED WEBHOOK RECEIVED")

            # Extract metadata
            metadata = obj.get("metadata", {})
            user_id = metadata.get("user_id")

            logger.info("Extracted metadata: %s", metadata)
            logger.info("Extracted user_id from metadata: %s", user_id)

            if not user_id:
                logger.error("user_id missing in subscription metadata")
                return JSONResponse(status_code=200, content={"status": "ignored"})

            # Fetch user from DB
            user = db.query(User).filter(User.id == int(user_id)).first()

            if not user:
                logger.error("No user found in DB for user_id=%s", user_id)
                return JSONResponse(status_code=200, content={"status": "ignored"})

            # Prepare values to store
            new_status = obj.get("status")
            new_trial_end = safe_dt_from_ts(obj.get("trial_end"))
            new_sub_id = obj.get("id")
            new_customer_id = obj.get("customer")

            logger.info(
                "Values to persist → status=%s trial_end=%s sub_id=%s customer_id=%s",
                new_status,
                new_trial_end,
                new_sub_id,
                new_customer_id
            )

            # Apply updates
            user.subscription_status = new_status
            user.trial_end = new_trial_end
            user.stripe_subscription_id = new_sub_id
            user.stripe_customer_id = new_customer_id

            # Commit
            try:
                db.commit()
                logger.info("DB commit successful")
            except Exception:
                logger.exception("DB commit failed")
                db.rollback()
                return JSONResponse(status_code=200, content={"status": "db_error"})

            # Refresh + re-check
            db.refresh(user)


        # INVOICE PAID (TRIAL → ACTIVE OR RENEWAL)
        elif etype == "invoice.payment_succeeded":
            subscription_id = obj.get("subscription")
            if not subscription_id:
                return JSONResponse(status_code=200, content={"status": "ignored"})

            user = db.query(User).filter(
                User.stripe_subscription_id == subscription_id
            ).first()

            if not user:
                logger.warning("No user for subscription=%s", subscription_id)
                return JSONResponse(status_code=200, content={"status": "ignored"})

            user.subscription_status = "active"

            # Try invoice line period end
            period_end = None
            lines = obj.get("lines", {}).get("data", [])
            if lines:
                period_end = lines[0].get("period", {}).get("end")

            if period_end:
                user.current_period_end = safe_dt_from_ts(period_end)

            user.trial_end = None
            db.commit()

            logger.info(
                "Subscription activated | user=%s sub=%s",
                user.email,
                subscription_id,
            )

        # SUBSCRIPTION CANCELED
        elif etype == "customer.subscription.deleted":
            subscription_id = obj.get("id")

            user = db.query(User).filter(
                User.stripe_subscription_id == subscription_id
            ).first()

            if not user:
                return JSONResponse(status_code=200, content={"status": "ignored"})

            user.subscription_status = "canceled"
            user.trial_end = None
            user.current_period_end = None
            db.commit()

            logger.info("Subscription canceled | user=%s", user.email)

        else:
            logger.info("Unhandled event type: %s", etype)

    except Exception:
        logger.exception("Error processing webhook event %s", etype)

    return JSONResponse(status_code=200, content={"status": "success"})