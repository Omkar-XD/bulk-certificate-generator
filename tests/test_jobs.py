
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import (
    CertificateJob,
    CertificateRecipient,
    JobStatus,
    RecipientStatus,
)


def test_create_job_with_recipients():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    with TestSession() as db:
        job = CertificateJob(
            event_name="Python Workshop",
            completion_date="2026-10-07",
            status=JobStatus.QUEUED,
            total_count=2,
        )

        job.recipients = [
            CertificateRecipient(
                name="Omkar Chavan",
                email="omkar@example.com",
                status=RecipientStatus.PENDING,
            ),
            CertificateRecipient(
                name="Rahul Sharma",
                email="rahul@example.com",
                status=RecipientStatus.PENDING,
            ),
        ]

        db.add(job)
        db.commit()

        saved_job = db.get(CertificateJob, job.id)

        assert saved_job is not None
        assert saved_job.total_count == 2
        assert len(saved_job.recipients) == 2
        assert saved_job.status == JobStatus.QUEUED

    Base.metadata.drop_all(engine)
    engine.dispose()
