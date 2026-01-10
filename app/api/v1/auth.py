from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_user
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, create_password_reset_token
from app.models.users import User
from app.schemas.users import UserOut, UserRegister, UserLogin, TokenPair, RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest
from jose import jwt, JWTError
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # проверяем email
    res = await db.execute(select(User).where(User.email == payload.email))
    existing = res.scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Email already registered")

    if payload.role not in ("patient", "doctor"):
        raise HTTPException(400, "role must be 'patient' or 'doctor'")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(id=user.id, email=user.email, role=user.role)


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    access = create_access_token(user_id=user.id, role=user.role)
    refresh = create_refresh_token(user_id=user.id, role=user.role)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest):
    """
    Stateless refresh (без хранения refresh-токенов в БД).
    Для MVP нормально. Позже можно добавить таблицу token sessions и отзыв токенов.
    """
    try:
        data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if data.get("type") != "refresh":
            raise HTTPException(401, "Invalid refresh token")
        user_id = int(data.get("sub"))
        role = str(data.get("role", "patient"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(401, "Invalid refresh token")

    access = create_access_token(user_id=user_id, role=role)
    refresh = create_refresh_token(user_id=user_id, role=role)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, role=user.role)


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()

    # ВАЖНО: всегда отвечаем одинаково (без утечек)
    if not user:
        return {"message": "If the email exists, a reset link was sent"}

    token = create_password_reset_token(user.id)

    # здесь будет email / telegram / лог
    print(f"RESET TOKEN (dev): {token}")

    return {"message": "If the email exists, a reset link was sent"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = jwt.decode(
            payload.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if data.get("type") != "password_reset":
            raise HTTPException(400, "Invalid token")

        user_id = int(data.get("sub"))
    except Exception:
        raise HTTPException(400, "Invalid or expired token")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(400, "Invalid token")

    user.password_hash = hash_password(payload.new_password)
    await db.commit()

    return {"message": "Password successfully updated"}
