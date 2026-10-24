"""PDF passes (QR) and certificates."""

from __future__ import annotations

import io
import json

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.event_config import event_date, event_name, event_venue


def _qr_image_bytes(payload: str) -> io.BytesIO:
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    pil_img = img.get_image() if hasattr(img, "get_image") else img
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def pass_qr_payload(participant_id: int, pass_token: str) -> str:
    return json.dumps(
        {"type": "event_pass", "participant_id": participant_id, "token": pass_token},
        separators=(",", ":"),
    )


def build_pass_pdf(
    *,
    name: str,
    email: str,
    participant_id: int,
    pass_token: str,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    title = event_name()

    c.setFont("Helvetica-Bold", 22)
    c.drawString(1 * inch, height - 1 * inch, "Event Pass")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.35 * inch, title)
    c.drawString(1 * inch, height - 1.6 * inch, f"Date: {event_date()}")
    c.drawString(1 * inch, height - 1.85 * inch, f"Venue: {event_venue()}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 2.4 * inch, name or "Guest")
    c.setFont("Helvetica", 11)
    c.drawString(1 * inch, height - 2.65 * inch, email)
    c.drawString(1 * inch, height - 2.9 * inch, f"Pass ID: {pass_token[:12]}…")

    qr_buf = _qr_image_bytes(pass_qr_payload(participant_id, pass_token))
    c.drawImage(
        ImageReader(qr_buf),
        width - 2.5 * inch,
        height - 3.2 * inch,
        width=1.8 * inch,
        height=1.8 * inch,
    )
    c.setFont("Helvetica", 9)
    c.drawString(1 * inch, 0.75 * inch, "Present this QR code at check-in. — EventPilot AI")
    c.showPage()
    c.save()
    return buf.getvalue()


def build_certificate_pdf(*, name: str, participant_id: int) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    title = event_name()

    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 2 * inch, "Certificate of Participation")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 2.5 * inch, "This certifies that")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 3 * inch, name or "Participant")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 3.5 * inch, f"attended {title}")
    c.drawCentredString(width / 2, height - 3.85 * inch, f"on {event_date()} at {event_venue()}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 1.2 * inch, f"Certificate ref: EP-{participant_id:05d} — EventPilot AI")
    c.showPage()
    c.save()
    return buf.getvalue()
