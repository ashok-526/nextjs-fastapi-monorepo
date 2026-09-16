from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Union

from passlib.context import CryptContext
from authlib.jose import jwt

from app.core.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: Union[str, uuid.UUID], expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=1))
    sub = str(subject)

    header = {"alg": ALGORITHM}
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token: bytes = jwt.encode(header, payload, settings.JWT_SECRET)
    return token.decode("utf-8") if isinstance(token, (bytes, bytearray)) else token

