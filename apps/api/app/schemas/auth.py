from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email_or_username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

