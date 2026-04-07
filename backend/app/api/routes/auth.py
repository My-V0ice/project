from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db import get_db_pool
from app.deps import get_current_user
from app.schemas.auth import Token, UserCreate, UserResponse
from app.services.audit import add_audit_log
from app.utils.users import normalize_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate) -> UserResponse:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        existing = await connection.fetchrow("SELECT id FROM users WHERE email = $1", user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

        record = await connection.fetchrow(
            """
            INSERT INTO users (email, full_name, hashed_password, role, brand_name, division_name)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, email, full_name, role, brand_name, division_name, consent_to_processing
            """,
            user.email,
            user.full_name,
            get_password_hash(user.password),
            user.role,
            user.brand_name,
            user.division_name,
        )
        normalized = normalize_user(record)
        await add_audit_log(
            connection,
            actor=normalized,
            action="user.registered",
            entity_type="user",
            entity_id=record["id"],
            details={"email": user.email, "role": user.role},
        )
        return UserResponse(**normalized)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT id, email, full_name, hashed_password, role, brand_name, division_name, consent_to_processing
            FROM users
            WHERE email = $1
            """,
            form_data.username,
        )
        if not record or not verify_password(form_data.password, record["hashed_password"]):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")

        user = normalize_user(record)
        access_token = create_access_token({"sub": user["email"], "user_id": user["id"], "role": user["role"]})
        await add_audit_log(
            connection,
            actor=user,
            action="user.logged_in",
            entity_type="user",
            entity_id=user["id"],
            details={"email": user["email"]},
        )
        return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def auth_me(current_user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**current_user)
