from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import (
    CertificateJob,
    CertificateRecipient,
    JobStatus,
    RecipientStatus,
)
from app.workers import certificate_worker


@pytest.fixture
def test_session_factory(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    TestSession = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    monkeypatch.setattr(
        certificate_worker,
        "SessionLocal",
        TestSession,
    )

    yield TestSession

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_one_failure_does_not_stop_other_recipients(
    test_session_factory,
    monkeypatch,
    tmp_path,
):
    with test_session_factory() as db:
        job = CertificateJob(
            event_name="Python Workshop",
            completion_date=date.today().isoformat(),
            status=JobStatus.QUEUED,
            total_count=2,
        )
        job.recipients = [
            CertificateRecipient(
                name="Omkar",
                email="omkar@example.com",
                status=RecipientStatus.PENDING,
            ),
            CertificateRecipient(
                name="Rahul",
                email="rahul@example.com",
                status=RecipientStatus.PENDING,
            ),
        ]
        db.add(job)
        db.commit()
        job_id = job.id

    def fake_generate_certificate(
        recipient_name,
        event_name,
        completion_date,
        certificate_id,
        output_dir=None,
    ):
        if recipient_name == "Omkar":
            raise RuntimeError("Simulated PDF failure")

        output_path = tmp_path / f"{certificate_id}.pdf"
        output_path.write_bytes(b"%PDF-1.4 test")
        return output_path

    monkeypatch.setattr(
        certificate_worker,
        "generate_certificate",
        fake_generate_certificate,
    )

    assert certificate_worker.process_one_recipient() is True
    assert certificate_worker.process_one_recipient() is True
    assert certificate_worker.process_one_recipient() is False

    with test_session_factory() as db:
        job = db.get(CertificateJob, job_id)
        recipients = db.scalars(
            select(CertificateRecipient).where(
                CertificateRecipient.job_id == job_id
            )
        ).all()

        by_name = {recipient.name: recipient for recipient in recipients}

        assert by_name["Omkar"].status == RecipientStatus.FAILED
        assert by_name["Omkar"].error_message is not None

        assert by_name["Rahul"].status == RecipientStatus.COMPLETED
        assert by_name["Rahul"].certificate_id is not None
        assert Path(by_name["Rahul"].file_path).is_file()

        assert job.status == JobStatus.COMPLETED_WITH_ERRORS
        assert job.success_count == 1
        assert job.failure_count == 1