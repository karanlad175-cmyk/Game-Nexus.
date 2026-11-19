from app.database import get_db
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"
COOKIE_NAME = "gn_access_token"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def make_access_token(user_id: int, remember_me: bool = False) -> str:
    now = datetime.now(timezone.utc)

    token_minutes = (
        30 * 24 * 60 if remember_me
        else settings.jwt_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=token_minutes)
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)

def set_auth_cookie(response, user_id: int, remember_me: bool = False):
    token = make_access_token(user_id, remember_me)

    cookie_options = {
        "key": COOKIE_NAME,
        "value": token,
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }

    if remember_me:
        cookie_options["max_age"] = 30 * 24 * 60 * 60

    response.set_cookie(**cookie_options)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in.")
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Session expired. Please sign in.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    return user
def get_admin_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:

    user = get_current_user(request, db)

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )

    return user

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User | None:

    try:
        return get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401:
            return None
        raise