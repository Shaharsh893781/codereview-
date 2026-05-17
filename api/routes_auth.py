from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.security import authenticate_user, create_access_token, hash_password
from database.session import get_db
from models.schemas import PasswordResetConfirm, PasswordResetRequest, PasswordResetRequestResult, Token, UserCreate, UserLogin
from models.user import User


router = APIRouter(prefix="/api/auth", tags=["auth"])
password_reset_tokens: dict[str, tuple[str, datetime]] = {}
RESET_TOKEN_EXPIRE_MINUTES = 15


@router.post("/register", response_model=Token)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email.lower(), full_name=payload.full_name, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    return Token(access_token=create_access_token(user.email))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.email))


@router.post("/forgot-password", response_model=PasswordResetRequestResult)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> PasswordResetRequestResult:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        return PasswordResetRequestResult(message="If that email exists, a reset token has been created.")

    reset_token = token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    password_reset_tokens[reset_token] = (user.email, expires_at)
    return PasswordResetRequestResult(
        message="Use this reset token to set a new password.",
        reset_token=reset_token,
    )


@router.post("/reset-password", response_model=Token)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> Token:
    reset_record = password_reset_tokens.get(payload.token)
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    email, expires_at = reset_record
    if datetime.now(timezone.utc) > expires_at:
        password_reset_tokens.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        password_reset_tokens.pop(payload.token, None)
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(payload.password)
    db.commit()
    password_reset_tokens.pop(payload.token, None)
    return Token(access_token=create_access_token(user.email))
