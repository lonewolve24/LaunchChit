import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.otp import OTPCode
from app.schemas.auth import RequestOTPInput, VerifyOTPInput, TokenResponse, UserResponse
from app.services import otp_sender
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_EXPIRE_MINUTES = 10


@router.post("/request-otp")
async def request_otp(body: RequestOTPInput, db: AsyncSession = Depends(get_db)):
    # Find or create user
    if body.email:
        stmt = select(User).where(User.email == body.email)
        contact = body.email
        send_fn = otp_sender.send_email_otp
    else:
        stmt = select(User).where(User.phone == body.phone)
        contact = body.phone
        send_fn = otp_sender.send_sms_otp

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(name=body.name, email=body.email, phone=body.phone)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate 6-digit OTP
    code = str(secrets.randbelow(900000) + 100000)
    expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    otp = OTPCode(user_id=user.id, code=code, contact=contact, expires_at=expires)
    db.add(otp)
    await db.commit()

    await send_fn(contact, code)

    return {"detail": "OTP sent"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(body: VerifyOTPInput, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)

    if body.email:
        stmt = select(User).where(User.email == body.email)
    else:
        stmt = select(User).where(User.phone == body.phone)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    contact = body.email or body.phone
    otp_stmt = (
        select(OTPCode)
        .where(
            OTPCode.user_id == user.id,
            OTPCode.contact == contact,
            OTPCode.code == body.code,
            OTPCode.used == False,  # noqa: E712
            OTPCode.expires_at > now,
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    otp_result = await db.execute(otp_stmt)
    otp = otp_result.scalar_one_or_none()
    if otp is None:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    otp.used = True
    await db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
    )
