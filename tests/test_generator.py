from pypdf import PdfReader

from app.services.generator import generate_certificate


def test_generate_certificate(tmp_path):
    output_path = generate_certificate(
        recipient_name="Omkar Chavan",
        event_name="Python Development Workshop",
        completion_date="2026-10-07",
        certificate_id="CERT-001",
        output_dir=tmp_path,
    )

    assert output_path.exists()
    assert output_path.suffix == ".pdf"
    assert output_path.read_bytes().startswith(b"%PDF")

    reader = PdfReader(str(output_path))
    text = reader.pages[0].extract_text()

    assert "Omkar Chavan" in text
    assert "Python Development Workshop" in text
    assert "CERT-001" in text


def test_reject_empty_recipient_name(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="Recipient name"):
        generate_certificate(
            recipient_name=" ",
            event_name="Python Workshop",
            completion_date="2026-10-07",
            certificate_id="CERT-002",
            output_dir=tmp_path,
        )


def test_reject_invalid_certificate_id(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="certificate ID"):
        generate_certificate(
            recipient_name="Omkar Chavan",
            event_name="Python Workshop",
            completion_date="2026-10-07",
            certificate_id="../unsafe",
            output_dir=tmp_path,
        )
