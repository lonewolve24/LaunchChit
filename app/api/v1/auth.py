"""New auth routes: signup, login, activation (password-based)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import SignupInput, LoginInput, TokenResponse, UserResponse
from app.core.password import hash_password, verify_password
from app.core.security import create_access_token
from app.services.activation_token import (
    generate_activation_token,
    verify_activation_token,
    consume_activation_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupInput, db: AsyncSession = Depends(get_db)):
    """Register a new user and return activation email (activation link needed to login)."""
    stmt = select(User).where(
        or_(User.username == body.username, User.email == body.email)
    )
    existing = await db.execute(stmt)
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Username or email already taken")

    hashed = hash_password(body.password)
    user = User(username=body.username, email=body.email, password_hash=hashed, is_active=False)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = generate_activation_token(user.email)
    activation_link = f"http://your-app.com/api/v1/auth/activate?email={user.email}&token={token}"
    # TODO: Send email with activation_link to user.email
    print(f"[TEMP] Activation link: {activation_link}")

    return TokenResponse(access_token="")


@router.get("/activate")
async def activate(email: str, token: str, db: AsyncSession = Depends(get_db)):
    """Activate user account by email + token."""
    if not verify_activation_token(email, token):
        raise HTTPException(status_code=401, detail="Invalid or expired activation token")

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    await db.commit()
    consume_activation_token(email)

    return {"detail": "Account activated. You can now login."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginInput, db: AsyncSession = Depends(get_db)):
    """Login by username or email + password. User must be activated."""
    stmt = select(User).where(
        or_(User.username == body.email_or_username, User.email == body.email_or_username)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not activated. Check your email.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Get current user (requires Bearer token)."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
    )
