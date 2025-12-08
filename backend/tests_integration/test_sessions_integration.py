"""Integration tests for session endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestSessionIntegration:
    """Integration tests for session workflows."""

    def test_create_session(self, client: TestClient):
        """Test creating a new session."""
        # First create a user so there's a host
        client.post("/auth/signup", json={
            "username": "sessionhost",
            "email": "sessionhost@example.com",
            "password": "hostpass"
        })
        
        session_data = {
            "title": "Python Interview",
            "language": "python"
        }
        response = client.post("/sessions/", json=session_data)
        
        assert response.status_code == 201
        session = response.json()
        assert session["title"] == "Python Interview"
        assert session["language"] == "python"
        assert session["status"] == "waiting"
        assert "id" in session
        assert "pin" in session
        assert len(session["pin"]) == 4  # PIN should be 4 digits

    def test_get_session_by_id(self, client: TestClient):
        """Test retrieving a session by ID."""
        # Create user and session
        client.post("/auth/signup", json={
            "username": "gethost",
            "email": "gethost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "Get Test Session",
            "language": "javascript"
        })
        session_id = create_response.json()["id"]
        
        # Get the session
        response = client.get(f"/sessions/{session_id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == session_id
        assert response.json()["title"] == "Get Test Session"

    def test_get_nonexistent_session(self, client: TestClient):
        """Test getting a session that doesn't exist."""
        response = client.get("/sessions/nonexistent-id")
        
        assert response.status_code == 404

    def test_join_session_with_valid_pin(self, client: TestClient):
        """Test joining a session with correct PIN."""
        # Create host and session
        client.post("/auth/signup", json={
            "username": "joinhost",
            "email": "joinhost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "Join Test Session",
            "language": "python"
        })
        session = create_response.json()
        session_id = session["id"]
        pin = session["pin"]
        
        # Create a participant user
        client.post("/auth/signup", json={
            "username": "participant",
            "email": "participant@example.com",
            "password": "pass"
        })
        
        # Join the session
        response = client.post(f"/sessions/{session_id}/join", json={"pin": pin})
        
        assert response.status_code == 200
        updated_session = response.json()
        assert len(updated_session["participants"]) >= 1

    def test_join_session_with_invalid_pin(self, client: TestClient):
        """Test joining a session with wrong PIN."""
        # Create host and session
        client.post("/auth/signup", json={
            "username": "badpinhost",
            "email": "badpinhost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "Bad PIN Session",
            "language": "python"
        })
        session_id = create_response.json()["id"]
        
        # Try to join with wrong PIN
        response = client.post(f"/sessions/{session_id}/join", json={"pin": "9999"})
        
        assert response.status_code == 403
        assert "invalid pin" in response.json()["detail"].lower()

    def test_update_session_code(self, client: TestClient):
        """Test updating code in a session."""
        # Create session
        client.post("/auth/signup", json={
            "username": "codehost",
            "email": "codehost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "Code Update Session",
            "language": "python"
        })
        session_id = create_response.json()["id"]
        
        # Update code
        new_code = "def hello():\n    return 'world'"
        response = client.put(f"/sessions/{session_id}/code", json={"code": new_code})
        
        assert response.status_code == 200
        
        # Verify code was updated
        get_response = client.get(f"/sessions/{session_id}")
        assert get_response.json()["code"] == new_code

    def test_update_session_language(self, client: TestClient):
        """Test updating language in a session."""
        # Create session with Python
        client.post("/auth/signup", json={
            "username": "langhost",
            "email": "langhost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "Language Update Session",
            "language": "python"
        })
        session_id = create_response.json()["id"]
        
        # Update to JavaScript
        response = client.put(f"/sessions/{session_id}/language", json={"language": "javascript"})
        
        assert response.status_code == 200
        
        # Verify language was updated
        get_response = client.get(f"/sessions/{session_id}")
        assert get_response.json()["language"] == "javascript"

    def test_end_session(self, client: TestClient):
        """Test ending a session."""
        # Create session
        client.post("/auth/signup", json={
            "username": "endhost",
            "email": "endhost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "End Test Session",
            "language": "python"
        })
        session_id = create_response.json()["id"]
        
        # End session
        response = client.post(f"/sessions/{session_id}/end")
        
        assert response.status_code == 200
        
        # Verify session is ended
        get_response = client.get(f"/sessions/{session_id}")
        assert get_response.json()["status"] == "ended"

    def test_session_chat_messages(self, client: TestClient):
        """Test sending and retrieving chat messages in a session."""
        # Create session
        client.post("/auth/signup", json={
            "username": "chathost",
            "email": "chathost@example.com",
            "password": "pass"
        })
        create_response = client.post("/sessions/", json={
            "title": "Chat Test Session",
            "language": "python"
        })
        session_id = create_response.json()["id"]
        
        # Send a message
        msg_response = client.post(
            f"/sessions/{session_id}/messages",
            json={"message": "Hello, world!"}
        )
        
        assert msg_response.status_code == 201
        message = msg_response.json()
        assert message["message"] == "Hello, world!"
        
        # Get messages
        get_response = client.get(f"/sessions/{session_id}/messages")
        
        assert get_response.status_code == 200
        messages = get_response.json()
        assert len(messages) >= 1
        assert messages[0]["message"] == "Hello, world!"

    def test_get_all_sessions(self, client: TestClient):
        """Test retrieving all sessions."""
        # Create a user
        client.post("/auth/signup", json={
            "username": "allhost",
            "email": "allhost@example.com",
            "password": "pass"
        })
        
        # Create multiple sessions
        client.post("/sessions/", json={"title": "Session 1", "language": "python"})
        client.post("/sessions/", json={"title": "Session 2", "language": "javascript"})
        
        # Get all sessions
        response = client.get("/sessions/")
        
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 2

    def test_full_session_workflow(self, client: TestClient):
        """Test complete session workflow."""
        # Create host
        host_response = client.post("/auth/signup", json={
            "username": "workflowhost",
            "email": "workflowhost@example.com",
            "password": "pass"
        })
        assert host_response.status_code == 201
        
        # Create session
        session_response = client.post("/sessions/", json={
            "title": "Full Workflow Session",
            "language": "python"
        })
        assert session_response.status_code == 201
        session = session_response.json()
        session_id = session["id"]
        
        # Create participant and join
        client.post("/auth/signup", json={
            "username": "workflowparticipant",
            "email": "workflowp@example.com",
            "password": "pass"
        })
        join_response = client.post(
            f"/sessions/{session_id}/join",
            json={"pin": session["pin"]}
        )
        assert join_response.status_code == 200
        
        # Update code
        code_response = client.put(
            f"/sessions/{session_id}/code",
            json={"code": "print('hello')"}
        )
        assert code_response.status_code == 200
        
        # Send chat message
        msg_response = client.post(
            f"/sessions/{session_id}/messages",
            json={"message": "Let's solve this!"}
        )
        assert msg_response.status_code == 201
        
        # End session
        end_response = client.post(f"/sessions/{session_id}/end")
        assert end_response.status_code == 200
        
        # Verify final state
        final_session = client.get(f"/sessions/{session_id}").json()
        assert final_session["status"] == "ended"
        assert final_session["code"] == "print('hello')"
