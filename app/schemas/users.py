from pydantic import BaseModel, EmailStr, Field

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str  # patient / doctor

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "patient"  # patient / doctor

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str
