from collections import Counter

from app.validation import (
    enrich_rows,
    find_duplicate_emails,
    invalid_email_rows,
    is_valid_email,
    validate_row,
)


def test_is_valid_email():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("not-an-email")
    assert not is_valid_email("")
    assert not is_valid_email(None)


def test_validate_row_flags():
    counts = Counter({"a@example.com": 2})
    issues = validate_row("Alice", "a@example.com", counts)
    assert "duplicate_email" in issues
    issues = validate_row("", "bad", counts)
    assert "missing_name" in issues
    assert "invalid_email" in issues


def test_enrich_rows_and_duplicates():
    rows = [
        {"name": "A", "email": "x@example.com"},
        {"name": "B", "email": "x@example.com"},
        {"name": "C", "email": "invalid"},
        {"name": "D", "email": ""},
    ]
    enriched = enrich_rows(rows)
    assert enriched[0]["issues"] == ["duplicate_email"]
    assert enriched[2]["issues"] == ["invalid_email"]
    assert enriched[3]["issues"] == ["missing_email"]
    assert find_duplicate_emails(rows) == ["x@example.com"]
    bad = invalid_email_rows(rows)
    assert len(bad) == 2
