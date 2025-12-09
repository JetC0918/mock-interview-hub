import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_service import AIAssistantService

client = TestClient(app)

@pytest.fixture
def mock_ai_service():
    with patch("app.routers.ai.get_ai_service") as mock_get:
        service_mock = MagicMock(spec=AIAssistantService)
        service_mock.get_guidance.return_value = "This is a mocked AI response."
        mock_get.return_value = service_mock
        yield service_mock

def test_ai_assist_endpoint_success(mock_ai_service):
    response = client.post(
        "/ai/assist",
        json={
            "sessionId": "test-session-id",
            "message": "@AI How do I solve this?",
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

def test_ai_assist_missing_message(mock_ai_service):
    response = client.post(
        "/ai/assist",
        json={
            "sessionId": "test-session-id",
            "message": "@AI"  # Empty message after tag
        }
    )
    
    # Should return 400 because message is empty after stripping tag
    assert response.status_code == 400

def test_ai_assist_no_tag(mock_ai_service):
    # Even without tag, if the frontend sends it to this endpoint, it should work
    # The endpoint strips @AI but does not strictly enforce its presence
    # BUT if stripping results in empty string, it fails.
    
    response = client.post(
        "/ai/assist",
        json={
            "sessionId": "test-session-id",
            "message": "Just a normal message"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "This is a mocked AI response."

def test_ai_service_not_configured():
    with patch("app.routers.ai.get_ai_service", side_effect=ValueError("GEMINI_API_KEY environment variable is not set")):
        response = client.post(
            "/ai/assist",
            json={
                "sessionId": "test-session-id",
                "message": "@AI help"
            }
        )
        
        assert response.status_code == 503
        assert "AI service is not configured" in response.json()["detail"]
