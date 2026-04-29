from typing import Any

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import ALGORITHM, SECRET_KEY
from app.db import get_db_pool
from app.utils.users import normalize_user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def load_user_from_token(token: str) -> dict[str, Any]:
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


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    return await load_user_from_token(token)


async def get_current_user_from_header_or_query(
    header_token: str | None = Depends(optional_oauth2_scheme),
    access_token: str | None = Query(default=None),
) -> dict[str, Any]:
    token = header_token or access_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось подтвердить пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await load_user_from_token(token)


def require_roles(*roles: str):
    async def dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия")
        return current_user

    return dependency
