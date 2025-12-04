import stripe
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.users import User
from app.utils.auth_dependencies import get_current_user

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
price_id = os.getenv("STRIPE_PRICE_ID")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.post("/create-checkout-session")
def create_checkout_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create Stripe customer if not exists
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email
        )
        current_user.stripe_customer_id = customer.id
        db.commit()

    # Create Stripe Checkout Session
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=current_user.stripe_customer_id,
        line_items=[
            {"price": price_id, "quantity": 1}
        ],
        subscription_data={
            "trial_period_days": 1
        },
        success_url="http://localhost:8000/payment-success",
        cancel_url="http://localhost:8000/payment-cancel",
    )

    return {"checkout_url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    # Handle different event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session["customer"]

        # Find user
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = "trialing"
            db.commit()

    elif event["type"] == "customer.subscription.created":
        sub = event["data"]["object"]
        user = db.query(User).filter(User.stripe_customer_id == sub["customer"]).first()
        if user:
            user.stripe_subscription_id = sub["id"]
            user.subscription_status = sub["status"]
            user.trial_end = datetime.fromtimestamp(sub["trial_end"])
            user.current_period_end = datetime.fromtimestamp(sub["current_period_end"])
            db.commit()

    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        sub = invoice["subscription"]

        user = db.query(User).filter(User.stripe_subscription_id == sub).first()
        if user:
            user.subscription_status = "active"
            db.commit()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        user = db.query(User).filter(User.stripe_subscription_id == sub["id"]).first()
        if user:
            user.subscription_status = "canceled"
            db.commit()

    return {"status": "success"}