import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import (
    CertificateJob,
    CertificateRecipient,
    JobStatus,
    RecipientStatus,
)
from app.services.generator import generate_certificate
from app.services.job_service import refresh_job_status


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2


def process_one_recipient() -> bool:
    """Process one pending recipient and isolate individual failures."""
    with SessionLocal() as db:
        recipient = db.scalars(
            select(CertificateRecipient)
            .join(
                CertificateJob,
                CertificateRecipient.job_id == CertificateJob.id,
            )
            .where(
                CertificateRecipient.status == RecipientStatus.PENDING,
                CertificateJob.status.in_(
                    [JobStatus.QUEUED, JobStatus.PROCESSING]
                ),
            )
            .order_by(CertificateRecipient.created_at)
            .limit(1)
        ).first()

        if recipient is None:
            return False

        recipient_id = recipient.id
        job_id = recipient.job_id

        # Mark the recipient and job as processing before generation.
        recipient.status = RecipientStatus.PROCESSING

        job = db.get(CertificateJob, job_id)
        if job is not None:
            job.status = JobStatus.PROCESSING
            job.completed_at = None

        db.commit()

        # Generate outside the claim transaction.
        recipient_name = recipient.name
        event_name = job.event_name if job else None
        completion_date = job.completion_date if job else None

        try:
            if event_name is None or completion_date is None:
                raise RuntimeError("Certificate job was not found")

            certificate_id = str(uuid.uuid4())

            output_path = generate_certificate(
                recipient_name=recipient_name,
                event_name=event_name,
                completion_date=completion_date,
                certificate_id=certificate_id,
            )

            # Persist the successful result.
            recipient = db.get(CertificateRecipient, recipient_id)

            if recipient is None:
                logger.error(
                    "Recipient %s disappeared after generation",
                    recipient_id,
                )
                return True

            recipient.certificate_id = certificate_id
            recipient.file_path = str(output_path.resolve())
            recipient.status = RecipientStatus.COMPLETED
            recipient.error_message = None
            recipient.completed_at = datetime.now(timezone.utc)

            db.commit()

            logger.info(
                "Generated certificate for recipient %s",
                recipient_id,
            )

        except Exception:
            logger.exception(
                "Certificate generation failed for recipient %s",
                recipient_id,
            )

            # Reload the record in case the SQLAlchemy session
            # needs to recover after a database error.
            db.rollback()
            recipient = db.get(CertificateRecipient, recipient_id)

            if recipient is not None:
                recipient.status = RecipientStatus.FAILED
                recipient.error_message = (
                    "Certificate generation failed."
                )
                recipient.completed_at = datetime.now(timezone.utc)

                try:
                    db.commit()
                except Exception:
                    db.rollback()
                    logger.exception(
                        "Could not persist failure for recipient %s",
                        recipient_id,
                    )
                    raise

        refresh_job_status(db, job_id)
        return True


def main() -> None:
    logger.info("Certificate worker started.")

    while True:
        try:
            processed = process_one_recipient()

            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)

        except Exception:
            logger.exception("Worker iteration failed.")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
