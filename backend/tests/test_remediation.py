from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.database.models import AuthSessionModel, GuestAdmissionAttemptModel, SessionModel, UserModel
from tests.conftest import TestingSessionLocal


def login(client, email="host@example.com"):
    response = client.post("/auth/login", json={"email": email, "password": "password"})
    assert response.status_code == 200


def create_session(client, title="Secure session"):
    response = client.post("/sessions/", json={"title": title, "language": "python"})
    assert response.status_code == 201
    return response.json()


def test_guest_admission_is_atomic_and_idempotent(client):
    login(client)
    session = create_session(client)
    before = TestingSessionLocal().query(UserModel).count()
    client.post("/auth/logout")

    bad = client.post(f"/sessions/{session['id']}/guest-join", json={
        "username": "Guest", "pin": "wrong_secret", "attemptId": "attempt_1234567890",
        "attemptSecret": "secret_123456789012345678901234567890",
    })
    assert bad.status_code == 403
    db = TestingSessionLocal()
    try:
        assert db.query(UserModel).count() == before
        assert db.query(GuestAdmissionAttemptModel).count() == 0
    finally:
        db.close()

    body = {
        "username": "Guest", "pin": session["pin"], "attemptId": "attempt_1234567890",
        "attemptSecret": "secret_123456789012345678901234567890",
    }
    first = client.post(f"/sessions/{session['id']}/guest-join", json=body)
    assert first.status_code == 200
    first_user = first.json()["user"]["id"]
    client.cookies.clear()  # Simulate a committed response whose cookie was lost.
    replay = client.post(f"/sessions/{session['id']}/guest-join", json=body)
    assert replay.status_code == 200
    assert replay.json()["user"]["id"] == first_user
    assert client.get("/auth/me").json()["id"] == first_user
    mismatch = client.post(f"/sessions/{session['id']}/guest-join", json={
        **body, "attemptSecret": "different_123456789012345678901234567",
    })
    assert mismatch.status_code == 409
    db = TestingSessionLocal()
    try:
        assert db.query(GuestAdmissionAttemptModel).count() == 1
        assert db.query(UserModel).count() == before + 1
        assert db.query(AuthSessionModel).filter(AuthSessionModel.user_id == first_user).count() == 1
    finally:
        db.close()


def test_guest_replay_cannot_reopen_ended_session(client):
    login(client)
    session = create_session(client)
    client.post("/auth/logout")
    body = {
        "username": "Replay Guest", "pin": session["pin"],
        "attemptId": "ended_replay_123456", "attemptSecret": "secret_123456789012345678901234567890",
    }
    first = client.post(f"/sessions/{session['id']}/guest-join", json=body)
    assert first.status_code == 200
    login(client)
    assert client.post(f"/sessions/{session['id']}/end").status_code == 200
    replay = client.post(f"/sessions/{session['id']}/guest-join", json=body)
    assert replay.status_code == 410


def test_authenticated_non_member_uses_secret_membership_join(client):
    login(client)
    session = create_session(client)
    signup = client.post("/auth/signup", json={
        "username": "Member", "email": "member@example.com", "password": "password",
    })
    assert signup.status_code == 201
    joined = client.post(f"/sessions/{session['id']}/join", json={"pin": session["pin"]})
    assert joined.status_code == 200
    assert any(item["username"] == "Member" for item in joined.json()["participants"])


def test_revision_compare_and_swap_and_ended_precedence(client):
    login(client)
    session = create_session(client)
    updated = client.put(f"/sessions/{session['id']}/code", json={"code": "one", "baseRevision": 0})
    assert updated.status_code == 200
    assert updated.json() == {"codeRevision": 1}
    conflict = client.put(f"/sessions/{session['id']}/code", json={"code": "stale", "baseRevision": 0})
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["currentRevision"] == 1
    assert client.post(f"/sessions/{session['id']}/end").status_code == 200
    ended = client.put(f"/sessions/{session['id']}/code", json={"code": "late", "baseRevision": 0})
    assert ended.status_code == 410


def test_expired_secret_is_forbidden_without_guest_side_effect(client):
    login(client)
    session = create_session(client)
    db = TestingSessionLocal()
    try:
        row = db.query(SessionModel).filter(SessionModel.id == session["id"]).one()
        row.join_secret_created_at = datetime.now(UTC) - timedelta(days=2)
        db.commit()
        before = db.query(UserModel).count()
    finally:
        db.close()
    client.post("/auth/logout")
    response = client.post(f"/sessions/{session['id']}/guest-join", json={
        "username": "Too Late", "pin": session["pin"], "attemptId": "expired_attempt_123",
        "attemptSecret": "secret_123456789012345678901234567890",
    })
    assert response.status_code == 403
    db = TestingSessionLocal()
    try:
        assert db.query(UserModel).count() == before
    finally:
        db.close()


def test_ai_exchange_is_persisted_once_and_replayed(client):
    login(client)
    session = create_session(client)
    provider = SimpleNamespace(get_guidance=AsyncMock(return_value="Consider a hash map."))
    payload = {
        "sessionId": session["id"], "message": "@AI What structure should I use?",
        "requestId": "ai_request_1234567890",
    }
    with patch("app.routers.ai.get_ai_service", return_value=provider):
        first = client.post("/ai/assist", json=payload)
        replay = client.post("/ai/assist", json=payload)
    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json()["id"] == replay.json()["id"]
    assert first.json()["authorType"] == "assistant"
    provider.get_guidance.assert_awaited_once()
    messages = client.get(f"/sessions/{session['id']}/messages").json()
    assert [message["authorType"] for message in messages[-2:]] == ["user", "assistant"]
    assert messages[-2]["message"] == payload["message"]


def test_timestamps_are_unambiguous_utc(client):
    login(client)
    session = create_session(client)
    assert session["createdAt"].endswith("Z")
    assert all(participant["joinedAt"].endswith("Z") for participant in session["participants"])


def test_oversized_request_is_rejected_before_route(client):
    response = client.post("/auth/signup", content=b"x" * (1_048_576 + 1), headers={"content-type": "application/json"})
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"
