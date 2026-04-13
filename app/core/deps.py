from typing import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.users import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exc

        user_id_raw = payload.get("sub")
        user_id = int(user_id_raw)
    except (JWTError, TypeError, ValueError):
        raise credentials_exc

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exc

    return user