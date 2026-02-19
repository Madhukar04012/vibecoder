"""
User Schemas - Pydantic models for API validation
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Optional

# Password constraints for security
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 128


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=MIN_PASSWORD_LEN, max_length=MAX_PASSWORD_LEN)
    name: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    email: str
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LEN)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: Optional[str]
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
