"""Participant row validation helpers."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_email(email: str | None) -> bool:
    if email is None:
        return False
    text = email.strip()
    if not text:
        return False
    return EMAIL_RE.match(text) is not None


def normalize_email(email: str | None) -> str:
    if not email:
        return ""
    return email.strip().lower()


def normalize_sheet_id(sheet_id: str | None) -> str:
    if sheet_id is None:
        return ""
    if isinstance(sheet_id, (int, float)):
        if isinstance(sheet_id, float) and sheet_id.is_integer():
            return str(int(sheet_id))
        return str(sheet_id).strip()
    return str(sheet_id).strip()


def build_sheet_id_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    ids = [normalize_sheet_id(r.get("sheet_id")) for r in rows]
    return Counter(i for i in ids if i)


def validate_row(
    name: str | None,
    email: str | None,
    email_counts: Counter[str],
    sheet_id_counts: Counter[str] | None = None,
    sheet_id: str | None = None,
) -> list[str]:
    """Return human-readable validation issues for a single row."""
    issues: list[str] = []
    name_text = (name or "").strip()
    email_text = (email or "").strip()
    norm = normalize_email(email)

    if not name_text:
        issues.append("missing_name")
    if not email_text:
        issues.append("missing_email")
    elif not is_valid_email(email_text):
        issues.append("invalid_email")
    if norm and email_counts[norm] > 1:
        issues.append("duplicate_email")
    sid = normalize_sheet_id(sheet_id)
    if sheet_id_counts is not None and sid and sheet_id_counts[sid] > 1:
        issues.append("duplicate_sheet_id")
    return issues


def issue_labels(issues: list[str]) -> str:
    labels = {
        "missing_name": "Missing name",
        "missing_email": "Missing email",
        "invalid_email": "Invalid email",
        "duplicate_email": "Duplicate email",
        "duplicate_sheet_id": "Duplicate sheet ID",
    }
    return "; ".join(labels.get(i, i) for i in issues)


def build_email_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    emails = [normalize_email(r.get("email")) for r in rows]
    return Counter(e for e in emails if e)


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add validation flags to each row dict."""
    counts = build_email_counts(rows)
    sheet_counts = build_sheet_id_counts(rows)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        name = row.get("name")
        email = row.get("email")
        sid = normalize_sheet_id(row.get("sheet_id"))
        issues = validate_row(name, email, counts, sheet_counts, sid or None)
        enriched.append(
            {
                **row,
                "sheet_id": sid,
                "name": (name or "").strip(),
                "email": (email or "").strip(),
                "issues": issues,
                "issue_text": issue_labels(issues),
                "valid": len(issues) == 0,
            }
        )
    return enriched


def find_duplicate_emails(rows: list[dict[str, Any]]) -> list[str]:
    counts = build_email_counts(rows)
    return sorted(e for e, c in counts.items() if c > 1)


def invalid_email_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if not is_valid_email(r.get("email"))]
