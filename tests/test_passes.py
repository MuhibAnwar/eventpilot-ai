from unittest.mock import patch

from app.documents import build_certificate_pdf, build_pass_pdf, pass_qr_payload


def test_pass_pdf_and_qr_payload():
    payload = pass_qr_payload(3, "tok123")
    assert "event_pass" in payload
    pdf = build_pass_pdf(name="Test", email="t@example.com", participant_id=3, pass_token="tok123")
    assert pdf[:4] == b"%PDF"
    cert = build_certificate_pdf(name="Test", participant_id=3)
    assert cert[:4] == b"%PDF"


@patch("app.services.send_pass_email")
def test_send_pass_requires_confirmed(mock_send, client):
    mock_send.return_value = {"sent": True, "detail": "Pass PDF emailed to x@example.com"}
    from app.services import save_participants

    save_participants([{"name": "A", "email": "a@example.com"}], skip_invalid=True)
    pid = client.get("/api/participants").json()["participants"][0]["id"]
    r = client.post(
        f"/api/participants/{pid}/send-pass",
        json={"idempotency_key": "pass-key-123456789"},
    )
    assert r.status_code == 400
