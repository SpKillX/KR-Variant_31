from pydantic import BaseModel
from ..models.user import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    role: UserRole | None = None

class UserCreate(BaseModel):
    username: str
    password: str
    phone: str | None = None
    role: UserRole = UserRole.CLIENT

class UserRead(BaseModel):
    id: int
    username: str
    phone: str | None = None
    role: UserRole
    
    class Config:
        from_attributes = True
