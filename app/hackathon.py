"""Demo-ready summaries and exports for hackathon judges."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.event_config import event_date, event_name, event_venue
from app.services import list_participants


def export_participants_csv() -> str:
    rows = list_participants()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "sheet_id",
            "name",
            "email",
            "status",
            "pass_sent",
            "certificate_sent",
            "checked_in",
            "created_at",
        ]
    )
    for p in rows:
        writer.writerow(
            [
                p.get("sheet_id") or "",
                p.get("name") or "",
                p.get("email") or "",
                p.get("status") or "",
                "yes" if p.get("pass_sent_at") else "no",
                "yes" if p.get("certificate_sent_at") else "no",
                "yes" if p.get("checked_in_at") else "no",
                p.get("created_at") or "",
            ]
        )
    return buf.getvalue()


def build_judge_summary() -> dict[str, Any]:
    rows = list_participants()
    total = len(rows)
    confirmed = sum(1 for r in rows if r.get("status") == "confirmed")
    pending = total - confirmed
    checked_in = sum(1 for r in rows if r.get("checked_in_at"))
    passes_sent = sum(1 for r in rows if r.get("pass_sent_at"))
    certs_sent = sum(1 for r in rows if r.get("certificate_sent_at"))

    conversion = round(100.0 * confirmed / total, 1) if total else 0.0
    attendance_rate = round(100.0 * checked_in / confirmed, 1) if confirmed else 0.0

    narrative = (
        f"{event_name()} ({event_date()} @ {event_venue()}): "
        f"{total} registrations, {confirmed} confirmed ({conversion}%), "
        f"{checked_in} checked in at the door ({attendance_rate}% of confirmed), "
        f"{passes_sent} passes and {certs_sent} certificates emailed. "
        f"Gemma 4 routes organizer questions to safe Python tools; SMTP sends three separate emails "
        f"(confirm → pass → certificate) with idempotent actions and audit logs."
    )

    return {
        "event": event_name(),
        "narrative": narrative,
        "highlights": [
            "AI tool router (Gemma 4) — no arbitrary code from the model",
            "3-email workflow: confirm, pass PDF + QR, certificate PDF",
            "Live QR check-in validates pass tokens server-side",
            "Sheet ID column preserved from Excel import",
            "Full action audit log for judges",
        ],
        "metrics": {
            "total": total,
            "confirmed": confirmed,
            "pending": pending,
            "checked_in": checked_in,
            "passes_sent": passes_sent,
            "certificates_sent": certs_sent,
            "conversion_rate": conversion,
            "attendance_rate": attendance_rate,
        },
    }


def parse_pass_qr_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("type") != "event_pass":
        return None
    return data
