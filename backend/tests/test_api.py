from fastapi.testclient import TestClient
from app.models.session import SessionStatus

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to CodioLive API"}

def test_auth_workflow(client: TestClient):
    # Signup
    signup_data = {"username": "testuser", "email": "test@example.com", "password": "password"}
    response = client.post("/auth/signup", json=signup_data)
    assert response.status_code == 201
    user = response.json()
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"

    # Login
    login_data = {"email": "test@example.com", "password": "password"}
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    logged_in_user = response.json()
    assert logged_in_user["id"] == user["id"]

    # Guest identities cannot be created outside validated session admission.
    response = client.post("/auth/guest", json={"username": "GuestUser"})
    assert response.status_code == 404


def test_auth_cookie_is_opaque_and_revocable(client: TestClient):
    response = client.post("/auth/login", json={"email": "algo@example.com", "password": "password"})
    assert response.status_code == 200
    token = response.cookies.get("session_token")
    assert token
    assert len(token) >= 40
    assert token != response.json()["id"]

    assert client.get("/auth/me").status_code == 200
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401


def test_forged_identity_cookie_is_rejected(client: TestClient):
    client.cookies.set("session_token", "known-user-id")
    assert client.get("/auth/me").status_code == 401

def test_session_workflow(client: TestClient):
    # Log in first
    login_data = {"email": "host@example.com", "password": "password"}
    client.post("/auth/login", json=login_data)
    
    # Create Session
    session_data = {"title": "Test Session", "language": "python"}
    response = client.post("/sessions/", json=session_data)
    assert response.status_code == 201
    session = response.json()
    assert session["title"] == "Test Session"
    assert session["status"] == SessionStatus.WAITING
    session_id = session["id"]

    # Get Session
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id
    assert "pin" not in response.json()
    assert "hostId" not in response.json()

    # Join Session
    # Need new user
    response = client.post(
        "/auth/signup",
        json={"username": "participant", "email": "p@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    
    join_data = {"pin": session["pin"]}
    response = client.post(f"/sessions/{session_id}/join", json=join_data)
    assert response.status_code == 200
    assert len(response.json()["participants"]) >= 2

    # Chat
    msg_data = {"message": "Hello World"}
    response = client.post(f"/sessions/{session_id}/messages", json=msg_data)
    assert response.status_code == 201
    
    response = client.get(f"/sessions/{session_id}/messages")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["message"] == "Hello World"


def test_ended_session_rejects_mutations(client: TestClient):
    client.post("/auth/login", json={"email": "host@example.com", "password": "password"})
    session = client.post("/sessions/", json={"title": "Ended", "language": "python"}).json()
    session_id = session["id"]
    assert client.post(f"/sessions/{session_id}/end").status_code == 200
    assert client.put(
        f"/sessions/{session_id}/code",
        json={"code": "bad", "baseRevision": session["codeRevision"]},
    ).status_code == 410
    assert client.post("/sessions/join-by-pin", json={"pin": session["pin"]}).status_code == 410


def test_host_can_rotate_join_secret(client: TestClient):
    client.post("/auth/login", json={"email": "host@example.com", "password": "password"})
    session = client.post("/sessions/", json={"title": "Rotate", "language": "python"}).json()
    old_secret = session["pin"]

    response = client.post(f"/sessions/{session['id']}/join-secret/rotate")

    assert response.status_code == 200
    new_secret = response.json()["pin"]
    assert new_secret != old_secret
    assert client.post("/sessions/join-by-pin", json={"pin": old_secret}).status_code == 403

def test_execution(client: TestClient):
    # Run Code
    code_data = {"code": "print('hello')", "language": "python"}
    response = client.post("/execution/run", json=code_data)
    # Server-side execution is disabled, expect 503
    assert response.status_code == 503
    assert "disabled" in response.json()["detail"].lower()
