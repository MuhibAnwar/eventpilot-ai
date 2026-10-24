"""Business logic for participants and NL tools."""

from __future__ import annotations

import secrets
from typing import Any

from app.database import db_session
from app.documents import build_certificate_pdf, build_pass_pdf
from app.email_service import send_certificate_email, send_confirmation_email, send_pass_email
from app.validation import (
    enrich_rows,
    find_duplicate_emails,
    invalid_email_rows,
    normalize_email,
    normalize_sheet_id,
)


def row_to_dict(row) -> dict[str, Any]:
    return dict(row)


def list_participants(
    search: str = "",
    status: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if search.strip():
        clauses.append("(name LIKE ? OR email LIKE ? OR sheet_id LIKE ?)")
        q = f"%{search.strip()}%"
        params.extend([q, q, q])
    if status in ("pending", "confirmed"):
        clauses.append("status = ?")
        params.append(status)
    sql = f"""
        SELECT * FROM participants WHERE {' AND '.join(clauses)}
        ORDER BY
            CASE WHEN sheet_id GLOB '[0-9]*' THEN CAST(sheet_id AS INTEGER) ELSE 999999999 END,
            sheet_id,
            id
    """
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_dict(r) for r in rows]


def save_participants(rows: list[dict[str, Any]], skip_invalid: bool = True) -> dict[str, Any]:
    enriched = enrich_rows(rows)
    to_save = [r for r in enriched if r["valid"]] if skip_invalid else enriched
    inserted = 0
    skipped = 0
    with db_session() as conn:
        for r in to_save:
            norm = normalize_email(r["email"])
            sid = normalize_sheet_id(r.get("sheet_id")) or None
            try:
                conn.execute(
                    "INSERT INTO participants (name, email, status, sheet_id) VALUES (?, ?, 'pending', ?)",
                    (r["name"], norm, sid),
                )
                inserted += 1
            except Exception:
                skipped += 1
    return {
        "inserted": inserted,
        "skipped": skipped,
        "preview": enriched,
    }


def replace_with_sample(rows: list[dict[str, Any]]) -> dict[str, Any]:
    with db_session() as conn:
        conn.execute("DELETE FROM action_logs")
        conn.execute("DELETE FROM confirm_idempotency")
        conn.execute("DELETE FROM participants")
    return save_participants(rows, skip_invalid=False)


def ensure_pass_token(participant_id: int) -> str:
    with db_session() as conn:
        row = conn.execute(
            "SELECT pass_token FROM participants WHERE id = ?", (participant_id,)
        ).fetchone()
        if not row:
            raise ValueError("not_found")
        if row["pass_token"]:
            return row["pass_token"]
        token = secrets.token_urlsafe(18)
        conn.execute(
            "UPDATE participants SET pass_token = ? WHERE id = ?",
            (token, participant_id),
        )
        return token


def _check_idempotency(conn, *, table: str, idempotency_key: str) -> bool:
    existing = conn.execute(
        f"SELECT participant_id FROM {table} WHERE idempotency_key = ?",
        (idempotency_key,),
    ).fetchone()
    return existing is not None


def _record_idempotency(
    conn, *, table: str, idempotency_key: str, participant_id: int
) -> None:
    conn.execute(
        f"INSERT INTO {table} (idempotency_key, participant_id) VALUES (?, ?)",
        (idempotency_key, participant_id),
    )


def get_participant(participant_id: int) -> dict[str, Any] | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM participants WHERE id = ?", (participant_id,)
        ).fetchone()
    return row_to_dict(row) if row else None


def confirm_participant(participant_id: int, idempotency_key: str) -> dict[str, Any]:
    with db_session() as conn:
        existing = conn.execute(
            "SELECT participant_id FROM confirm_idempotency WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            pid = existing["participant_id"]
            p = conn.execute("SELECT * FROM participants WHERE id = ?", (pid,)).fetchone()
            return {
                "ok": True,
                "already_done": True,
                "participant": row_to_dict(p) if p else None,
            }

        p = conn.execute(
            "SELECT * FROM participants WHERE id = ?", (participant_id,)
        ).fetchone()
        if not p:
            return {"ok": False, "error": "not_found"}
        if p["status"] == "confirmed":
            conn.execute(
                "INSERT OR IGNORE INTO confirm_idempotency (idempotency_key, participant_id) VALUES (?, ?)",
                (idempotency_key, participant_id),
            )
            return {
                "ok": True,
                "already_done": True,
                "participant": row_to_dict(p),
            }

        conn.execute(
            "UPDATE participants SET status = 'confirmed', confirmed_at = datetime('now') WHERE id = ?",
            (participant_id,),
        )
        conn.execute(
            "INSERT INTO confirm_idempotency (idempotency_key, participant_id) VALUES (?, ?)",
            (idempotency_key, participant_id),
        )
        updated = conn.execute(
            "SELECT * FROM participants WHERE id = ?", (participant_id,)
        ).fetchone()
        participant = row_to_dict(updated)
        name, em = participant["name"], participant["email"]

    ensure_pass_token(participant_id)
    confirm_delivery = send_confirmation_email(name, em)
    with db_session() as conn:
        conn.execute(
            "INSERT INTO action_logs (participant_id, action, detail) VALUES (?, ?, ?)",
            (
                participant_id,
                "confirm_registration",
                confirm_delivery.get("detail", "Registration confirmed"),
            ),
        )
        participant = row_to_dict(
            conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
        )
    return {
        "ok": True,
        "already_done": False,
        "participant": participant,
        "email_delivery": confirm_delivery,
        "email_step": "confirm",
    }


def send_pass(participant_id: int, idempotency_key: str) -> dict[str, Any]:
    with db_session() as conn:
        if _check_idempotency(conn, table="pass_idempotency", idempotency_key=idempotency_key):
            p = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
            return {
                "ok": True,
                "already_done": True,
                "participant": row_to_dict(p) if p else None,
            }
        p = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
        if not p:
            return {"ok": False, "error": "not_found"}
        if p["status"] != "confirmed":
            return {"ok": False, "error": "not_confirmed"}
        _record_idempotency(
            conn,
            table="pass_idempotency",
            idempotency_key=idempotency_key,
            participant_id=participant_id,
        )
        name, em = p["name"], p["email"]

    token = ensure_pass_token(participant_id)
    pdf = build_pass_pdf(
        name=name,
        email=em,
        participant_id=participant_id,
        pass_token=token,
    )
    delivery = send_pass_email(name, em, pdf)
    with db_session() as conn:
        if delivery.get("sent"):
            conn.execute(
                "UPDATE participants SET pass_sent_at = datetime('now') WHERE id = ?",
                (participant_id,),
            )
        conn.execute(
            "INSERT INTO action_logs (participant_id, action, detail) VALUES (?, ?, ?)",
            (participant_id, "send_pass", delivery.get("detail", "Pass send attempted")),
        )
        updated = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
    return {
        "ok": True,
        "already_done": False,
        "participant": row_to_dict(updated),
        "email_delivery": delivery,
        "email_step": "pass",
    }


def send_certificate(participant_id: int, idempotency_key: str) -> dict[str, Any]:
    with db_session() as conn:
        if _check_idempotency(
            conn, table="certificate_idempotency", idempotency_key=idempotency_key
        ):
            p = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
            return {
                "ok": True,
                "already_done": True,
                "participant": row_to_dict(p) if p else None,
            }
        p = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
        if not p:
            return {"ok": False, "error": "not_found"}
        if p["status"] != "confirmed":
            return {"ok": False, "error": "not_confirmed"}
        _record_idempotency(
            conn,
            table="certificate_idempotency",
            idempotency_key=idempotency_key,
            participant_id=participant_id,
        )
        name, em = p["name"], p["email"]

    pdf = build_certificate_pdf(name=name, participant_id=participant_id)
    delivery = send_certificate_email(name, em, pdf)
    with db_session() as conn:
        if delivery.get("sent"):
            conn.execute(
                "UPDATE participants SET certificate_sent_at = datetime('now') WHERE id = ?",
                (participant_id,),
            )
        conn.execute(
            "INSERT INTO action_logs (participant_id, action, detail) VALUES (?, ?, ?)",
            (
                participant_id,
                "send_certificate",
                delivery.get("detail", "Certificate send attempted"),
            ),
        )
        updated = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
    return {
        "ok": True,
        "already_done": False,
        "participant": row_to_dict(updated),
        "email_delivery": delivery,
        "email_step": "certificate",
    }


def check_in_participant(participant_id: int, token: str) -> dict[str, Any]:
    with db_session() as conn:
        p = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
        if not p:
            return {"ok": False, "error": "not_found"}
        if p["status"] != "confirmed":
            return {"ok": False, "error": "not_confirmed"}
        if not p["pass_token"] or p["pass_token"] != token:
            return {"ok": False, "error": "invalid_token"}
        already = bool(p["checked_in_at"])
        if not already:
            conn.execute(
                "UPDATE participants SET checked_in_at = datetime('now') WHERE id = ?",
                (participant_id,),
            )
            conn.execute(
                "INSERT INTO action_logs (participant_id, action, detail) VALUES (?, ?, ?)",
                (participant_id, "check_in", f"QR check-in successful for {p['name']}"),
            )
        updated = conn.execute("SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()
    return {
        "ok": True,
        "already_checked_in": already,
        "participant": row_to_dict(updated),
    }


def bulk_send_passes() -> dict[str, Any]:
    import secrets

    targets = [
        p
        for p in list_participants()
        if p.get("status") == "confirmed" and not p.get("pass_sent_at")
    ]
    sent = 0
    failed = 0
    for p in targets:
        key = f"bulk-pass-{p['id']}-{secrets.token_urlsafe(12)}"
        result = send_pass(int(p["id"]), key)
        if result.get("ok") and not result.get("already_done"):
            delivery = result.get("email_delivery") or {}
            if delivery.get("sent"):
                sent += 1
            else:
                failed += 1
    return {"queued": len(targets), "sent": sent, "failed": failed}


def list_action_logs(limit: int = 100) -> list[dict[str, Any]]:
    sql = """
        SELECT l.id, l.participant_id, l.action, l.detail, l.created_at,
               p.name AS participant_name, p.email AS participant_email
        FROM action_logs l
        LEFT JOIN participants p ON p.id = l.participant_id
        ORDER BY l.id DESC
        LIMIT ?
    """
    with db_session() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [row_to_dict(r) for r in rows]


def run_tool(tool: str, participants: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = participants if participants is not None else list_participants()
    if tool == "show_all":
        return {"tool": tool, "count": len(rows), "participants": rows}
    if tool == "invalid_emails":
        bad = invalid_email_rows(rows)
        return {"tool": tool, "count": len(bad), "participants": bad}
    if tool == "find_duplicates":
        dups = find_duplicate_emails(rows)
        dup_rows = [r for r in rows if normalize_email(r.get("email")) in dups]
        return {"tool": tool, "emails": dups, "count": len(dup_rows), "participants": dup_rows}
    if tool == "count_participants":
        return {"tool": tool, "count": len(rows)}
    return {
        "tool": "none",
        "message": "I couldn't map that request to a dashboard action. Try asking to count participants, list everyone, or find invalid or duplicate emails.",
    }
