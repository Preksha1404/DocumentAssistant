from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: EmailStr
    phone: Optional[PhoneNumber] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[PhoneNumber] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[EmailStr] = None