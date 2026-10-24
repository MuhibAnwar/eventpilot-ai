from app.services import confirm_participant, save_participants


def test_idempotent_confirm(client):
    save_participants([{"name": "Test User", "email": "test@example.com"}], skip_invalid=True)
    listing = client.get("/api/participants").json()["participants"]
    pid = listing[0]["id"]
    key = "test-idempotency-key-12345678"

    r1 = client.post(f"/api/participants/{pid}/confirm", json={"idempotency_key": key})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["already_done"] is False
    assert body1["participant"]["status"] == "confirmed"

    r2 = client.post(f"/api/participants/{pid}/confirm", json={"idempotency_key": key})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["already_done"] is True

    with __import__("app.database", fromlist=["db_session"]).db_session() as conn:
        logs = conn.execute("SELECT COUNT(*) AS c FROM action_logs WHERE participant_id = ?", (pid,)).fetchone()
    assert logs["c"] == 1
