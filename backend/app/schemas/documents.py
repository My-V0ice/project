from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    orientation: str = Field(default="landscape", pattern="^(portrait|landscape)$")
    description: str = Field(default="", max_length=1200)
    allowed_fields: list[str] = Field(
        default_factory=lambda: [
            "full_name",
            "status",
            "event_title",
            "event_date",
            "hours",
            "document_number",
            "qr_link",
            "signatory_name",
            "signatory_position",
        ]
    )
    layout_config: dict = Field(default_factory=dict)


class TemplateLayoutUpdate(BaseModel):
    layout_config: dict = Field(default_factory=dict)


class IssueDocumentsRequest(BaseModel):
    event_id: int
    template_id: int
    signatory_name: str = Field(default="Ответственное лицо")
    signatory_position: str = Field(default="Руководитель проекта")
    signature_type: str = Field(default="УКЭП")
    send_email: bool = True


class ConsentUpdate(BaseModel):
    consent_to_processing: bool
