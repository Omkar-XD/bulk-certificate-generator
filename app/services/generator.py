import os
import re
import tempfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


DEFAULT_STORAGE_DIR = Path("storage") / "certificates"


def generate_certificate(
    recipient_name: str,
    event_name: str,
    completion_date: str,
    certificate_id: str,
    output_dir: Path | str = DEFAULT_STORAGE_DIR,
) -> Path:
    """
    Generate one personalized PDF certificate.

    Returns the path to the generated PDF.
    """
    if not recipient_name.strip():
        raise ValueError("Recipient name cannot be empty")

    if not event_name.strip():
        raise ValueError("Event name cannot be empty")

    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", certificate_id):
        raise ValueError("Invalid certificate ID")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{certificate_id}.pdf"

    width, height = landscape(A4)

    # Write to a temporary file so an incomplete PDF is
    # not exposed at the final destination.
    fd, temporary_name = tempfile.mkstemp(
        suffix=".pdf",
        dir=output_dir,
    )
    os.close(fd)

    temporary_path = Path(temporary_name)

    try:
        pdf = canvas.Canvas(
            str(temporary_path),
            pagesize=(width, height),
        )

        # Background
        pdf.setFillColor(colors.HexColor("#FAF8F0"))
        pdf.rect(0, 0, width, height, fill=1, stroke=0)

        # Decorative borders
        pdf.setStrokeColor(colors.HexColor("#17365D"))
        pdf.setLineWidth(4)
        pdf.rect(24, 24, width - 48, height - 48)

        pdf.setStrokeColor(colors.HexColor("#C49A45"))
        pdf.setLineWidth(1.5)
        pdf.rect(34, 34, width - 68, height - 68)

        # Certificate heading
        pdf.setFillColor(colors.HexColor("#17365D"))
        pdf.setFont("Helvetica-Bold", 29)
        pdf.drawCentredString(
            width / 2,
            height - 105,
            "CERTIFICATE OF COMPLETION",
        )

        pdf.setFillColor(colors.HexColor("#555555"))
        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(
            width / 2,
            height - 140,
            "This certificate is proudly presented to",
        )

        # Recipient
        pdf.setFillColor(colors.HexColor("#17365D"))
        pdf.setFont("Helvetica-Bold", 26)
        pdf.drawCentredString(
            width / 2,
            height - 190,
            recipient_name.strip()[:100],
        )

        # Event details
        pdf.setFillColor(colors.HexColor("#444444"))
        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(
            width / 2,
            height - 225,
            "for successfully completing",
        )

        pdf.setFillColor(colors.HexColor("#17365D"))
        pdf.setFont("Helvetica-Bold", 19)
        pdf.drawCentredString(
            width / 2,
            height - 258,
            event_name.strip()[:120],
        )

        pdf.setFillColor(colors.HexColor("#444444"))
        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(
            width / 2,
            height - 290,
            f"Completion Date: {completion_date}",
        )

        # Certificate identifier
        pdf.setStrokeColor(colors.HexColor("#C49A45"))
        pdf.line(
            width / 2 - 100,
            100,
            width / 2 + 100,
            100,
        )

        pdf.setFillColor(colors.HexColor("#555555"))
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(
            width / 2,
            82,
            f"Certificate ID: {certificate_id}",
        )

        pdf.save()

        # Atomic replacement prevents clients from seeing
        # a partially written file.
        temporary_path.replace(output_path)

        return output_path

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
