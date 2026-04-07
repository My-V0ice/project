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
    brand_name: str = Field(default="ТОГУ", max_length=150)
    division_name: str = Field(default="Цифровая кафедра", max_length=150)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value: date, info) -> date:
        start_date = info.data.get("start_date")
        if start_date and value < start_date:
            raise ValueError("Дата окончания не может быть раньше даты начала")
        return value


class ParticipantCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=150)
    email: EmailStr
    status: str = Field(default="Подтвержден")
    achievement: str = Field(default="", max_length=1000)
    hours: int = Field(default=0, ge=0, le=1000)
    award_category: str = Field(default="Участник")

    @field_validator("award_category")
    @classmethod
    def validate_award_category(cls, value: str) -> str:
        if value not in AWARD_CATEGORIES:
            raise ValueError("Недопустимая категория награды")
        return value


class ParticipantImport(BaseModel):
    participants: list[ParticipantCreate]
