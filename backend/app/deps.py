from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import ALGORITHM, SECRET_KEY
from app.db import get_db_pool
from app.utils.users import normalize_user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить пользователя",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT id, email, full_name, role, brand_name, division_name, consent_to_processing
            FROM users
            WHERE id = $1
            """,
            user_id,
        )
        if not record:
            raise credentials_exception
        return normalize_user(record)


def require_roles(*roles: str):
    async def dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия")
        return current_user

    return dependency
