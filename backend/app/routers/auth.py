import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from app.email_utils import send_password_reset_email
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from app.config import settings
from app.database import get_db
from app.models import User, PasswordResetToken
from app.schemas import RegisterIn, LoginIn, UserOut
from app.security import hash_password, verify_password, set_auth_cookie, get_current_user, COOKIE_NAME

class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

class ProfileUpdateIn(BaseModel):
    gamer_tag: str = Field(min_length=3, max_length=40)
    email: str = Field(
        min_length=5,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

class ForgotPasswordIn(BaseModel):
    email: str = Field(min_length=5, max_length=320)


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
oauth = OAuth()
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, response: Response, db: Session = Depends(get_db)):
    email = data.email.lower()
    tag = data.gamer_tag.strip()
    if db.query(User).filter(or_(User.email == email, User.gamer_tag == tag)).first():
        raise HTTPException(status_code=409, detail="Email or gamer tag is already registered.")
    user = User(email=email, gamer_tag=tag, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    set_auth_cookie(response, user.id)
    return user

@router.post("/login", response_model=UserOut)
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    set_auth_cookie(response, user.id, remember_me=data.remember_me)

    return user

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")
    return {"message": "Signed out."}

@router.get("/me", response_model=UserOut)
def get_me(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    return user

@router.put("/profile", response_model=UserOut)
def update_profile(
    data: ProfileUpdateIn,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    email = data.email.strip().lower()
    tag = data.gamer_tag.strip()

    if len(tag) < 3 or len(tag) > 40:
        raise HTTPException(
            status_code=422,
            detail="Gamer tag must contain 3 to 40 characters."
        )

    existing_user = db.query(User).filter(
        or_(
            User.email == email,
            User.gamer_tag == tag
        ),
        User.id != user.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email or gamer tag is already in use."
        )

    user.email = email
    user.gamer_tag = tag

    db.commit()
    db.refresh(user)

    return user

@router.put("/change-password")
def change_password(
    data: PasswordChangeIn,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if not user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="This account uses Google login and has no password set."
        )

    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )

    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password."
        )

    user.password_hash = hash_password(data.new_password)

    db.commit()

    return {"message": "Password changed successfully."}

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordIn,
    db: Session = Depends(get_db)
):
    email = data.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    # Always return the same response to protect account privacy.
    if not user:
        return {
            "message": "If an account exists with this email, a reset link will be sent."
        }

    # Invalidate previous unused reset tokens.
    old_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).all()

    for old_token in old_tokens:
        old_token.used_at = datetime.now(timezone.utc)

    # Generate a secure random token.
    raw_token = secrets.token_urlsafe(32)

    # Store only its SHA-256 hash in the database.
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
    )

    db.add(reset_token)
    db.commit()

    reset_link = (
        settings.frontend_origin.rstrip("/")
        + "/reset-password.html?token="
        + raw_token
    )

    
    try:
        send_password_reset_email(user.email, reset_link)

    except Exception as e:
        logging.exception("PASSWORD RESET EMAIL ERROR")
        raise HTTPException(
            status_code=500,
            detail="Password reset email could not be sent. Please try again later."
        ) from e

    return {
        "message": "If an account exists with this email, a reset link will be sent."
    }


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordIn,
    db: Session = Depends(get_db)
):
    # Hash the token received from the reset link.
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None)
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already used reset link."
        )

    now = datetime.now(timezone.utc)
    expiry = reset_token.expires_at

    # Handle databases that return timezone-naive datetimes.
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry <= now:
        raise HTTPException(
            status_code=400,
            detail="Reset link has expired. Please request a new one."
        )

    user = db.query(User).filter(
        User.id == reset_token.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Account not found."
        )

    # Update the password and mark the token as used.
    user.password_hash = hash_password(data.new_password)
    reset_token.used_at = now

    # Invalidate any other outstanding reset tokens for this user.
    other_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_token.id,
        PasswordResetToken.used_at.is_(None)
    ).all()

    for token in other_tokens:
        token.used_at = now

    db.commit()

    return {
        "message": "Password reset successfully. Please log in with your new password."
    }

@router.get("/google/start")
async def google_start(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google login is not configured yet.")
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = await oauth.google.parse_id_token(request, token)
        email = (userinfo.get("email") or "").lower()
        google_sub = userinfo.get("sub")
        if not email or not google_sub or not userinfo.get("email_verified", False):
            raise HTTPException(status_code=400, detail="Google account email could not be verified.")
        user = db.query(User).filter(User.email == email).first()
        if user:
            if user.google_sub and user.google_sub != google_sub:
                raise HTTPException(status_code=409, detail="This email is linked to another Google account.")
            user.google_sub = google_sub
        else:
            base_tag = (userinfo.get("name") or email.split("@")[0]).strip()
            base_tag = "".join(c for c in base_tag if c.isalnum() or c in "_- ")[:35] or "Gamer"
            tag = base_tag
            suffix = 1
            while db.query(User).filter(User.gamer_tag == tag).first():
                suffix += 1
                tag = f"{base_tag[:34]}{suffix}"
            user = User(email=email, gamer_tag=tag, google_sub=google_sub, password_hash=None)
            db.add(user)
        db.commit()
        db.refresh(user)
        response = RedirectResponse(url="/index.html", status_code=303)
        set_auth_cookie(response, user.id)
        return response
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Google sign-in failed. Please try again.")
