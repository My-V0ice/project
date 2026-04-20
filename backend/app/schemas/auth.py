from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain.constants import ROLE_LABELS


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=3, max_length=150)
    brand_name: str = Field(default="\u0422\u041e\u0413\u0423", max_length=150)
    division_name: str = Field(default="\u0426\u0438\u0444\u0440\u043e\u0432\u0430\u044f \u043a\u0430\u0444\u0435\u0434\u0440\u0430", max_length=150)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must contain at least 6 characters")
        return value


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in ROLE_LABELS:
            raise ValueError("Unknown role")
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
