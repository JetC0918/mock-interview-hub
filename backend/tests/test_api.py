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

    # Guest Login
    guest_data = {"username": "GuestUser"}
    response = client.post("/auth/guest", json=guest_data)
    assert response.status_code == 201
    guest = response.json()
    assert guest["username"] == "GuestUser"

def test_session_workflow(client: TestClient):
    # Determine Host (ensure one exists first, we just signed up one)
    
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

    # Join Session
    # Need new user
    client.post("/auth/signup", json={"username": "participant", "email": "p@example.com", "password": "pw"})
    
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

def test_execution(client: TestClient):
    # Run Code
    code_data = {"code": "print('hello')", "language": "python"}
    response = client.post("/execution/run", json=code_data)
    assert response.status_code == 200
    result = response.json()
    assert result["stdout"] == "Hello World\n"
