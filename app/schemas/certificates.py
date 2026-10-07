from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    email: EmailStr


class CreateCertificateJobRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_name: str = Field(min_length=1, max_length=200)
    completion_date: date
    recipients: list[RecipientInput] = Field(
        min_length=1,
        max_length=1000,
    )

    @field_validator("recipients")
    @classmethod
    def reject_duplicate_emails(cls, recipients):
        emails = [r.email.lower() for r in recipients]

        if len(emails) != len(set(emails)):
            raise ValueError("Duplicate recipient emails are not allowed")

        return recipients
