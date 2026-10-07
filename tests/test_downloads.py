from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import (
    CertificateJob,
    CertificateRecipient,
    JobStatus,
    RecipientStatus,
)
from app.main import app
import app.api.certificates as certificates_api


def test_download_completed_certificate(tmp_path, monkeypatch):
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

    certificate_id = "CERT-DOWNLOAD-001"
    pdf_path = tmp_path / f"{certificate_id}.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test certificate")

    with TestSession() as db:
        job = CertificateJob(
            event_name="Python Workshop",
            completion_date="2026-10-07",
            status=JobStatus.COMPLETED,
            total_count=1,
            success_count=1,
            failure_count=0,
        )
        recipient = CertificateRecipient(
            name="Omkar",
            email="omkar@example.com",
            status=RecipientStatus.COMPLETED,
            certificate_id=certificate_id,
            file_path=str(pdf_path.resolve()),
        )
        job.recipients = [recipient]
        db.add(job)
        db.commit()

    monkeypatch.setattr(
        certificates_api,
        "STORAGE_ROOT",
        tmp_path.resolve(),
    )

    def override_get_db():
        with TestSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/v1/certificates/{certificate_id}"
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert response.content.startswith(b"%PDF-1.4")

            missing = client.get(
                "/api/v1/certificates/DOES-NOT-EXIST"
            )
            assert missing.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()