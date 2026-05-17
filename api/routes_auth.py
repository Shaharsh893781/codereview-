from datetime import datetime, timedelta, timezone
from secrets import randbelow

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.security import authenticate_user, create_access_token, hash_password
from database.session import get_db
from models.schemas import PasswordResetConfirm, PasswordResetRequest, PasswordResetRequestResult, Token, UserCreate, UserLogin
from models.user import User
from services.email_service import EmailConfigurationError, GmailEmailService


router = APIRouter(prefix="/api/auth", tags=["auth"])
password_reset_otps: dict[str, tuple[str, datetime]] = {}
RESET_OTP_EXPIRE_MINUTES = 10
email_service = GmailEmailService()


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
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found for this email. Please register first.")

    otp = f"{randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_OTP_EXPIRE_MINUTES)
    try:
        email_service.send_password_reset_otp(user.email, otp)
    except EmailConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Gmail OTP delivery is not configured.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to send OTP email. Please try again later.") from exc

    password_reset_otps[email] = (otp, expires_at)
    return PasswordResetRequestResult(message="OTP sent to your Gmail address.")


@router.post("/reset-password", response_model=Token)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> Token:
    email = payload.email.lower()
    reset_record = password_reset_otps.get(email)
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    expected_otp, expires_at = reset_record
    if datetime.now(timezone.utc) > expires_at:
        password_reset_otps.pop(email, None)
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    if payload.otp != expected_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        password_reset_otps.pop(email, None)
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.hashed_password = hash_password(payload.password)
    db.commit()
    password_reset_otps.pop(email, None)
    return Token(access_token=create_access_token(user.email))
