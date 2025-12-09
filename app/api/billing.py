import stripe
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.models.users import User
from app.utils.auth_dependencies import get_current_user

logger = logging.getLogger("billing")
logger.setLevel(logging.INFO)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
price_id = os.getenv("STRIPE_PRICE_ID")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/billing", tags=["Billing"])

# helper: safe timestamp -> datetime
def safe_dt_from_ts(ts):
    try:
        if not ts:
            return None
        return datetime.fromtimestamp(int(ts))
    except Exception:
        logger.exception("failed to parse timestamp: %s", ts)
        return None
    
@router.get("/me/subscription")
def get_subscription_status(current_user: User = Depends(get_current_user)):
    return {
        "subscription_status": current_user.subscription_status,
        "trial_end": current_user.trial_end,
        "current_period_end": current_user.current_period_end
    }

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
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError as e:
        # Invalid payload
        logger.exception("Invalid payload")
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.error.SignatureVerificationError as e:
        logger.exception("Invalid signature")
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})
    except Exception as e:
        logger.exception("Unexpected error constructing event")
        return JSONResponse(status_code=400, content={"error": str(e)})

    etype = event.get("type")
    data_obj = event.get("data", {}).get("object", {})

    # Use try/except for each handler to avoid a single error causing 500
    try:
        # Checkout completed: ensure customer stored in DB
        if etype == "checkout.session.completed":
            session = data_obj
            customer_id = session.get("customer")
            email = session.get("customer_details", {}).get("email")

            if not customer_id and not email:
                logger.warning("checkout.session.completed missing customer & email")
            else:
                # find user by stripe_customer_id
                user = None
                if customer_id:
                    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

                # find by email (session may include customer_details.email)
                if user is None and email:
                    user = db.query(User).filter(User.email == email).first()

                if user:
                    if not user.stripe_customer_id and customer_id:
                        user.stripe_customer_id = customer_id
                        db.commit()
                        logger.info("Saved stripe_customer_id for user %s", user.email)
                    else:
                        logger.info("checkout.session.completed: user found (%s) stripe_customer_id=%s", user.email, user.stripe_customer_id)
                else:
                    logger.warning("checkout.session.completed: no matching user for customer=%s email=%s", customer_id, email)

        # Subscription created
        elif etype == "customer.subscription.created":
            sub = data_obj
            customer_id = sub.get("customer")
            sub_id = sub.get("id")

            if not customer_id:
                logger.warning("customer.subscription.created missing customer")
            else:
                user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
                if not user:
                    logger.warning("No user found with stripe_customer_id=%s", customer_id)
                else:
                    # idempotency: if same subscription already stored, skip timestamp overwrite
                    if user.stripe_subscription_id == sub_id:
                        logger.info("Subscription already stored for user %s, skipping update", user.email)
                    else:
                        user.stripe_subscription_id = sub_id
                        status = sub.get("status")
                        if status:
                            user.subscription_status = status

                        trial_end_ts = sub.get("trial_end")
                        current_period_end_ts = sub.get("current_period_end")

                        user.trial_end = safe_dt_from_ts(trial_end_ts)
                        user.current_period_end = safe_dt_from_ts(current_period_end_ts)

        # Invoice paid (first charge after trial or recurring invoice)
        elif etype == "invoice.payment_succeeded":
            invoice = data_obj
            subscription_id = invoice.get("subscription")

            # In rare cases the invoice may not contain subscription; try to retrieve invoice from stripe
            if not subscription_id:
                # try to fetch invoice from stripe to get subscription id
                invoice_id = invoice.get("id")
                if invoice_id:
                    try:
                        full_invoice = stripe.Invoice.retrieve(invoice_id)
                        subscription_id = full_invoice.get("subscription")
                    except Exception:
                        logger.exception("Failed to retrieve invoice %s from stripe", invoice_id)

            if not subscription_id:
                logger.warning("invoice.payment_succeeded missing subscription id on invoice %s", invoice.get("id"))
            else:
                user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
                if not user:
                    # Sometimes you stored subscription id under a different field format; try by customer->user
                    customer_id = invoice.get("customer")
                    if customer_id:
                        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

                if not user:
                    logger.warning("No user found for subscription %s (invoice %s)", subscription_id, invoice.get("id"))
                else:
                    # Update status to active and update current_period_end if possible
                    user.subscription_status = "active"
                    # invoice may have period_end on lines->data->period->end or we can fetch subscription
                    period_end_ts = None
                    try:
                        # Try invoice.lines.data[0].period.end
                        lines = invoice.get("lines", {}).get("data", [])
                        if lines and isinstance(lines, list):
                            period_end_ts = lines[0].get("period", {}).get("end")
                    except Exception:
                        period_end_ts = None

                    if not period_end_ts:
                        # fetch subscription object for accurate current_period_end
                        try:
                            sub_obj = stripe.Subscription.retrieve(subscription_id)
                            period_end_ts = sub_obj.get("current_period_end")
                        except Exception:
                            logger.exception("Failed to retrieve subscription %s from stripe", subscription_id)

                    if period_end_ts:
                        user.current_period_end = safe_dt_from_ts(period_end_ts)
                    # mark trial ended as None (optional)
                    user.trial_end = None
                    db.commit()
                    logger.info("Marked subscription active for user %s (sub=%s)", user.email, subscription_id)

        # Subscription deleted / canceled
        elif etype == "customer.subscription.deleted":
            sub = data_obj
            subscription_id = sub.get("id")
            user = None
            if subscription_id:
                user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()

            if not user:
                customer_id = sub.get("customer")
                if customer_id:
                    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()

            if user:
                user.subscription_status = "canceled"
                user.trial_end = None
                user.current_period_end = None
                db.commit()
                logger.info("Subscription canceled for user %s", user.email)
            else:
                logger.warning("customer.subscription.deleted: no user found for subscription %s", subscription_id)

        # Add other event types as needed...
        else:
            logger.info("Unhandled event type: %s", etype)

    except Exception as e:
        logger.exception("Error handling webhook event %s: %s", etype, str(e))
        return JSONResponse(status_code=200, content={"status": "error", "message": "handled with errors"})

    return JSONResponse(status_code=200, content={"status": "success"})