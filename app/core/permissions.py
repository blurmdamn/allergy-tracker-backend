from fastapi import Depends, HTTPException
from app.core.deps import get_current_user
from app.models.users import User

def require_role(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker

require_admin = require_role("admin")
require_doctor = require_role("doctor", "admin")
require_patient = require_role("patient", "admin")
