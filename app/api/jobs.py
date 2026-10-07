from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    CertificateJob,
    CertificateRecipient,
    JobStatus,
    RecipientStatus,
)
from app.schemas.certificates import CreateCertificateJobRequest


router = APIRouter(
    prefix="/api/v1/certificate-jobs",
    tags=["Certificate Jobs"],
)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_certificate_job(
    request: CreateCertificateJobRequest,
    db: Session = Depends(get_db),
):
    job = CertificateJob(
        event_name=request.event_name,
        completion_date=request.completion_date.isoformat(),
        status=JobStatus.QUEUED,
        total_count=len(request.recipients),
    )

    job.recipients = [
        CertificateRecipient(
            name=recipient.name,
            email=str(recipient.email),
            status=RecipientStatus.PENDING,
        )
        for recipient in request.recipients
    ]

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create certificate generation job",
        )

    return {
        "job_id": job.id,
        "status": job.status.value,
        "total_recipients": job.total_count,
        "status_url": f"/api/v1/certificate-jobs/{job.id}",
        "results_url": f"/api/v1/certificate-jobs/{job.id}/results",
    }


@router.get("/{job_id}")
def get_certificate_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.get(CertificateJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Certificate job not found",
        )

    processed_count = job.success_count + job.failure_count

    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "completion_date": job.completion_date,
        "status": job.status.value,
        "total_recipients": job.total_count,
        "processed_count": processed_count,
        "success_count": job.success_count,
        "failure_count": job.failure_count,
        "pending_count": max(job.total_count - processed_count, 0),
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }


@router.get("/{job_id}/results")
def get_certificate_job_results(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = db.get(CertificateJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Certificate job not found",
        )

    recipients = db.scalars(
        select(CertificateRecipient)
        .where(CertificateRecipient.job_id == job_id)
        .order_by(CertificateRecipient.created_at)
    ).all()

    return {
        "job_id": job.id,
        "status": job.status.value,
        "total_recipients": job.total_count,
        "success_count": job.success_count,
        "failure_count": job.failure_count,
        "results": [
            {
                "recipient_id": recipient.id,
                "name": recipient.name,
                "email": recipient.email,
                "status": recipient.status.value,
                "certificate_id": recipient.certificate_id,
                "download_url": (
                    f"/api/v1/certificates/{recipient.certificate_id}"
                    if recipient.status == RecipientStatus.COMPLETED
                    and recipient.certificate_id
                    else None
                ),
                "error": recipient.error_message,
            }
            for recipient in recipients
        ],
    }
