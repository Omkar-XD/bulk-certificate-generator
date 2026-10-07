from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    CertificateJob,
    CertificateRecipient,
    JobStatus,
    RecipientStatus,
)


def refresh_job_status(db: Session, job_id: str) -> None:
    """Recalculate job progress from its recipient records."""
    job = db.get(CertificateJob, job_id)

    if job is None:
        return

    recipients = db.scalars(
        select(CertificateRecipient).where(
            CertificateRecipient.job_id == job_id
        )
    ).all()

    job.total_count = len(recipients)
    job.success_count = sum(
        recipient.status == RecipientStatus.COMPLETED
        for recipient in recipients
    )
    job.failure_count = sum(
        recipient.status == RecipientStatus.FAILED
        for recipient in recipients
    )

    has_pending_work = any(
        recipient.status in (
            RecipientStatus.PENDING,
            RecipientStatus.PROCESSING,
        )
        for recipient in recipients
    )

    if has_pending_work:
        job.status = JobStatus.PROCESSING
        job.completed_at = None
    else:
        job.status = (
            JobStatus.COMPLETED_WITH_ERRORS
            if job.failure_count
            else JobStatus.COMPLETED
        )
        job.completed_at = datetime.now(timezone.utc)

    db.commit()
