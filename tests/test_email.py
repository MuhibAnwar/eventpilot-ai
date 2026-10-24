from unittest.mock import MagicMock, patch

from app.email_service import build_confirmation_preview, send_confirmation_email, send_email, smtp_configured


def test_smtp_not_configured(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)
    assert not smtp_configured()
    preview = build_confirmation_preview("A", "a@example.com")
    assert "DRY-RUN" not in preview["body"]
    result = send_confirmation_email("A", "a@example.com")
    assert result["sent"] is False


@patch("app.email_service.smtplib.SMTP")
def test_send_via_smtp(mock_smtp, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_FROM", "user@example.com")

    server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = server

    result = send_confirmation_email("Alice", "guest@example.com")
    assert result["sent"] is True
    server.starttls.assert_called_once()
    server.login.assert_called_once()
