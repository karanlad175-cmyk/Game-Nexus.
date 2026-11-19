import hashlib, hmac, json
import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import Subscription, Payment
from app.schemas import CheckoutIn
from app.security import get_current_user

router = APIRouter(prefix="/api/payments", tags=["payments"])

def client():
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail="Razorpay is not configured. Add TEST credentials to backend/.env.")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))

@router.get("/config")
def payment_config():
    return {"key_id": settings.razorpay_key_id or None, "currency": "INR",
            "plans": {"monthly": bool(settings.razorpay_monthly_plan_id), "yearly": bool(settings.razorpay_yearly_plan_id)}}

@router.post("/subscriptions")
def create_subscription(data: CheckoutIn, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    plan_id = settings.razorpay_monthly_plan_id if data.plan == "monthly" else settings.razorpay_yearly_plan_id
    if not plan_id:
        raise HTTPException(status_code=503, detail=f"Razorpay {data.plan} plan ID is not configured.")
    result = client().subscription.create({
        "plan_id": plan_id,
        "customer_notify": 1,
        "quantity": 1,
        "total_count": 120 if data.plan == "monthly" else 10,
        "notes": {"user_id": str(user.id), "plan": data.plan},
    })
    sub = Subscription(user_id=user.id, plan=data.plan,
                       provider_subscription_id=result["id"], status=result.get("status", "created"))
    db.add(sub)
    db.commit()
    return {"subscription_id": result["id"], "short_url": result.get("short_url"),
            "key_id": settings.razorpay_key_id, "status": result.get("status")}

@router.post("/verify")
async def verify_payment(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    data = await request.json()
    payment_id = data.get("razorpay_payment_id", "")
    subscription_id = data.get("razorpay_subscription_id", "")
    signature = data.get("razorpay_signature", "")
    if not payment_id or not subscription_id or not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay verification fields.")
    message = f"{payment_id}|{subscription_id}".encode()
    expected = hmac.new(settings.razorpay_key_secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed.")
    sub = db.query(Subscription).filter(
        Subscription.provider_subscription_id == subscription_id,
        Subscription.user_id == user.id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found for this account.")
    # Signature confirms the checkout response. Webhooks are authoritative for lifecycle state.
    if sub.status in ("created", "authenticated"):
        sub.status = "authenticated"
    db.commit()
    return {"message": "Payment signature verified. Subscription status will be finalized by Razorpay webhook.",
            "subscription_status": sub.status}

@router.get("/me")
def my_subscription(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(["active", "authenticated", "created", "pending"])
    ).order_by(Subscription.created_at.desc()).first()
    return {"has_subscription": bool(sub and sub.status == "active"),
            "plan": sub.plan if sub else None, "status": sub.status if sub else "none"}

@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not settings.razorpay_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured.")
    expected = hmac.new(settings.razorpay_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    event = json.loads(body)
    event_name = event.get("event", "")
    payload = event.get("payload", {})
    entity = (payload.get("subscription") or {}).get("entity") or {}
    subscription_id = entity.get("id")
    if subscription_id:
        sub = db.query(Subscription).filter(Subscription.provider_subscription_id == subscription_id).first()
        if sub:
            status_map = {
                "subscription.activated": "active",
                "subscription.authenticated": "authenticated",
                "subscription.pending": "pending",
                "subscription.halted": "halted",
                "subscription.cancelled": "cancelled",
                "subscription.completed": "completed",
                "subscription.paused": "paused",
                "subscription.resumed": "active",
            }
            if event_name in status_map:
                sub.status = status_map[event_name]
                db.commit()
    return {"received": True}
