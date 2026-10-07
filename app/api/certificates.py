from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import CertificateRecipient, RecipientStatus
from app.services.generator import DEFAULT_STORAGE_DIR


router = APIRouter(
    prefix="/api/v1/certificates",
    tags=["Certificates"],
)

STORAGE_ROOT = DEFAULT_STORAGE_DIR.resolve()


@router.get("/{certificate_id}")
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    recipient = db.scalars(
        select(CertificateRecipient).where(
            CertificateRecipient.certificate_id == certificate_id
        )
    ).first()

    if recipient is None or recipient.status != RecipientStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    if not recipient.file_path:
        raise HTTPException(
            status_code=404,
            detail="Certificate file is unavailable",
        )

    file_path = Path(recipient.file_path).resolve()

    # Ensure the stored path cannot escape the certificate directory.
    if not file_path.is_relative_to(STORAGE_ROOT):
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found",
        )

    if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"certificate-{certificate_id}.pdf",
    )
