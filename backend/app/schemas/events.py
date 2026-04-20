from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.constants import AWARD_CATEGORIES


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    organizer: str = Field(min_length=3, max_length=200)
    start_date: date
    end_date: date
    event_type: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=4000)
    contact_email: EmailStr
    brand_name: str = Field(default="\u0422\u041e\u0413\u0423", max_length=150)
    division_name: str = Field(default="\u0426\u0438\u0444\u0440\u043e\u0432\u0430\u044f \u043a\u0430\u0444\u0435\u0434\u0440\u0430", max_length=150)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and value < start_date:
            raise ValueError("End date cannot be earlier than start date")
        return value


class ParticipantCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=150)
    email: EmailStr
    status: str = Field(default="Confirmed")
    achievement: str = Field(default="", max_length=1000)
    hours: int = Field(default=0, ge=0, le=1000)
    award_category: str = Field(default_factory=lambda: AWARD_CATEGORIES[0] if AWARD_CATEGORIES else "")

    @field_validator("award_category")
    @classmethod
    def validate_award_category(cls, value: str) -> str:
        if value not in AWARD_CATEGORIES:
            raise ValueError("Invalid award category")
        return value


class ParticipantAssignUsers(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    status: str = Field(default="Confirmed")
    achievement: str = Field(default="", max_length=1000)
    hours: int = Field(default=0, ge=0, le=1000)
    award_category: str | None = Field(default=None)

    @field_validator("user_ids")
    @classmethod
    def validate_user_ids(cls, value: list[int]) -> list[int]:
        cleaned = list(dict.fromkeys(value))
        if not cleaned:
            raise ValueError("User list is empty")
        if any(item <= 0 for item in cleaned):
            raise ValueError("User IDs must be positive")
        return cleaned

    @field_validator("award_category")
    @classmethod
    def validate_award_category(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in AWARD_CATEGORIES:
            raise ValueError("Invalid award category")
        return value
