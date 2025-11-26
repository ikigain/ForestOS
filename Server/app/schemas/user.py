from pydantic import BaseModel, EmailStr, constr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[constr(min_length=8)] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    id: int

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


# Response schema (alias for User)
UserResponse = User


# Token schemas for authentication
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
