from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt
from passlib.context import CryptContext

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    normalized_password = plain_password or ""
    is_bcrypt_hash = isinstance(hashed_password, str) and hashed_password.startswith("$2")
    if is_bcrypt_hash and isinstance(normalized_password, str):
        password_bytes = normalized_password.encode("utf-8")
        if len(password_bytes) > 72:
            normalized_password = password_bytes[:72].decode("utf-8", errors="ignore")
        return bcrypt.checkpw(normalized_password.encode("utf-8"), hashed_password.encode("utf-8"))
    return pwd_context.verify(normalized_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password or "")


def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
