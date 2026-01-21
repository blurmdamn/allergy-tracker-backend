from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from jose import jwt, JWTError

from app.core.config import settings
from app.core.deps import get_db, get_current_user
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
)
from app.core.emails import send_email
from app.models.users import User
from app.schemas.users import (
    UserOut,
    UserRegister,
    UserLogin,
    TokenPair,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # проверяем email
    res = await db.execute(select(User).where(User.email == payload.email))
    existing = res.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # admin через публичный register запрещаем
    if payload.role not in ("patient", "doctor"):
        raise HTTPException(status_code=400, detail="role must be 'patient' or 'doctor'")

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
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user_id=user.id, role=user.role)
    refresh = create_refresh_token(user_id=user.id, role=user.role)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Stateless refresh (без хранения refresh-токенов в БД).
    Для MVP ок. Позже можно добавить хранение/отзыв refresh токенов.
    """
    try:
        data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = int(data.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # доп. защита: проверяем, что пользователь существует и активен
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token(user_id=user.id, role=user.role)
    refresh = create_refresh_token(user_id=user.id, role=user.role)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, role=user.role)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Всегда отвечает одинаково, чтобы не палить существование email.
    Если пользователь найден и активен — отправляем письмо со ссылкой сброса.
    """
    res = await db.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()

    # одинаковый ответ всегда
    generic_resp = {"message": "If the email exists, a reset link was sent"}

    if not user or not user.is_active:
        return generic_resp

    token = create_password_reset_token(user.id)
    reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"

    # отправка через EMAIL_PROVIDER (sendgrid/console)
    await send_email(
        to_email=payload.email,
        subject="Сброс пароля — Allergy Tracker",
        html=f"""
        <p>Вы запросили сброс пароля.</p>
        <p>Ссылка действительна ограниченное время.</p>
        <p><a href="{reset_link}">Сбросить пароль</a></p>
        <p>Если это были не вы — просто игнорируйте письмо.</p>
        """,
        text=f"Сброс пароля: {reset_link}",
    )

    return generic_resp


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if data.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")

        user_id = int(data.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.password_hash = hash_password(payload.new_password)
    await db.commit()

    return {"message": "Password successfully updated"}
