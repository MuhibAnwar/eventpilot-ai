from app.hackathon import parse_pass_qr_payload
from app.services import check_in_participant, confirm_participant, save_participants


def test_parse_pass_qr():
    raw = '{"type":"event_pass","participant_id":1,"token":"abc"}'
    assert parse_pass_qr_payload(raw)["token"] == "abc"
    assert parse_pass_qr_payload("not json") is None


def test_check_in_flow(client):
    save_participants([{"name": "Door Test", "email": "door@example.com"}], skip_invalid=True)
    pid = client.get("/api/participants").json()["participants"][0]["id"]
    key = "checkin-confirm-key-123456789"
    client.post(f"/api/participants/{pid}/confirm", json={"idempotency_key": key})
    from app.services import ensure_pass_token

    token = ensure_pass_token(pid)
    r1 = check_in_participant(pid, token)
    assert r1["ok"] is True
    assert r1["already_checked_in"] is False
    r2 = check_in_participant(pid, token)
    assert r2["already_checked_in"] is True
