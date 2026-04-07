from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain.constants import ROLE_LABELS


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=3, max_length=150)
    role: str = "division_admin"
    brand_name: str = Field(default="ТОГУ", max_length=150)
    division_name: str = Field(default="Цифровая кафедра", max_length=150)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in ROLE_LABELS:
            raise ValueError("Неизвестная роль")
        return value


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    role_label: str
    brand_name: str
    division_name: str
    consent_to_processing: bool
