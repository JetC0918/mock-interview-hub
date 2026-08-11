import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_service import AIAssistantService

# client = TestClient(app)  # Removed global client, using fixture instead

@pytest.fixture
def mock_ai_service():
    with patch("app.routers.ai.get_ai_service") as mock_get:
        service_mock = MagicMock(spec=AIAssistantService)
        service_mock.get_guidance.return_value = "This is a mocked AI response."
        mock_get.return_value = service_mock
        yield service_mock

def test_ai_assist_endpoint_success(client: TestClient, mock_ai_service):
    # Authenticate
    client.post("/auth/signup", json={"username": "ai_user", "email": "ai@example.com", "password": "password"})
    session_id = client.post("/sessions/", json={"title": "AI test", "language": "python"}).json()["id"]
    
    response = client.post(
        "/ai/assist",
        json={
            "sessionId": session_id,
            "message": "@AI How do I solve this?",
            "requestId": "ai_success_request_01",
            "problemContext": {
                "title": "Two Sum",
                "difficulty": "easy",
                "description": "Find indices of two numbers..."
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["participantId"] == "ai-assistant"
    assert data["username"] == "AI Assistant"
    assert data["message"] == "This is a mocked AI response."
    
    # Verify service was called with correct arguments
    mock_ai_service.get_guidance.assert_called_once()
    call_args = mock_ai_service.get_guidance.call_args
    assert call_args.kwargs["user_message"] == "How do I solve this?"
    assert call_args.kwargs["problem_context"]["title"] == "Two Sum"

def test_ai_assist_missing_message(client: TestClient, mock_ai_service):
    # Authenticate
    client.post("/auth/signup", json={"username": "ai_user_2", "email": "ai2@example.com", "password": "password"})
    session_id = client.post("/sessions/", json={"title": "AI test", "language": "python"}).json()["id"]
    
    response = client.post(
        "/ai/assist",
        json={
            "sessionId": session_id,
            "message": "@AI",  # Empty message after tag
            "requestId": "ai_empty_request_01",
        }
    )
    
    # Pydantic rejects a message that is empty after stripping the tag.
    assert response.status_code == 422

def test_ai_assist_no_tag(client: TestClient, mock_ai_service):
    # Authenticate
    client.post("/auth/signup", json={"username": "ai_user_3", "email": "ai3@example.com", "password": "password"})
    session_id = client.post("/sessions/", json={"title": "AI test", "language": "python"}).json()["id"]
    
    # Even without tag, if the frontend sends it to this endpoint, it should work
    # The endpoint strips @AI but does not strictly enforce its presence
    # BUT if stripping results in empty string, it fails.
    
    response = client.post(
        "/ai/assist",
        json={
            "sessionId": session_id,
            "message": "Just a normal message",
            "requestId": "ai_plain_request_01",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "This is a mocked AI response."

def test_ai_service_not_configured(client: TestClient):
    # Authenticate
    client.post("/auth/signup", json={"username": "ai_user_4", "email": "ai4@example.com", "password": "password"})
    session_id = client.post("/sessions/", json={"title": "AI test", "language": "python"}).json()["id"]
    
    with patch("app.routers.ai.get_ai_service", side_effect=ValueError("GEMINI_API_KEY environment variable is not set")):
        response = client.post(
            "/ai/assist",
            json={
                "sessionId": session_id,
                "message": "@AI help",
                "requestId": "ai_unconfigured_01",
            }
        )
        
        assert response.status_code == 503
        assert "AI service is temporarily unavailable" in response.json()["detail"]
