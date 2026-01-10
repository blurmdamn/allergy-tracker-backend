import asyncio
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.users import User

EMAIL = "admin@example.com"
PASSWORD = "admin12345" 

async def main():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(User).where(User.email == EMAIL))
        user = res.scalar_one_or_none()
        if user:
            user.role = "admin"
            user.password_hash = hash_password(PASSWORD)
        else:
            user = User(email=EMAIL, password_hash=hash_password(PASSWORD), role="admin", is_active=True)
            s.add(user)
        await s.commit()
    print("admin ready:", EMAIL)

if __name__ == "__main__":
    asyncio.run(main())
