
import pytest
from pydantic import ValidationError

from app.schemas.certificates import CreateCertificateJobRequest


def test_valid_bulk_request():
    request = CreateCertificateJobRequest(
        event_name="Python Workshop",
        completion_date="2026-10-07",
        recipients=[
            {"name": "Omkar Chavan", "email": "omkar@example.com"},
            {"name": "Rahul Sharma", "email": "rahul@example.com"},
        ],
    )

    assert len(request.recipients) == 2


def test_reject_empty_recipient_list():
    with pytest.raises(ValidationError):
        CreateCertificateJobRequest(
            event_name="Python Workshop",
            completion_date="2026-10-07",
            recipients=[],
        )


def test_reject_duplicate_emails():
    with pytest.raises(ValidationError, match="Duplicate recipient emails"):
        CreateCertificateJobRequest(
            event_name="Python Workshop",
            completion_date="2026-10-07",
            recipients=[
                {"name": "Omkar", "email": "omkar@example.com"},
                {"name": "Another Name", "email": "omkar@example.com"},
            ],
        )


def test_reject_invalid_email():
    with pytest.raises(ValidationError):
        CreateCertificateJobRequest(
            event_name="Python Workshop",
            completion_date="2026-10-07",
            recipients=[
                {"name": "Omkar", "email": "not-an-email"},
            ],
        )
