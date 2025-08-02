from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    is_host: bool = False
    is_verified: bool = False
    government_id_verified: bool = False


class UserCreate(UserBase):
    password_hash: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    is_host: Optional[bool] = None
    is_verified: Optional[bool] = None
    government_id_verified: Optional[bool] = None
    password_hash: Optional[str] = None


class UserInDB(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass