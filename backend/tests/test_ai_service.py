import pytest
from types import SimpleNamespace

import app.services.ai_service as ai_service_module
from app.services.ai_service import AIAssistantService


def test_ai_service_requires_deepseek_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        AIAssistantService()


def test_ai_service_calls_deepseek_v4_flash(monkeypatch):
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "Consider sorting the intervals first."}}]}

    def fake_post(url, *, headers, json, timeout):
        requests.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret")
    monkeypatch.setattr(ai_service_module, "httpx", SimpleNamespace(post=fake_post), raising=False)

    service = AIAssistantService()
    result = service.get_guidance("What should I do first?")

    assert result == "Consider sorting the intervals first."
    assert requests[0]["url"] == "https://api.deepseek.com/chat/completions"
    assert requests[0]["headers"]["Authorization"] == "Bearer test-secret"
    assert requests[0]["json"]["model"] == "deepseek-v4-flash"
    assert requests[0]["json"]["messages"][0]["role"] == "system"
    assert requests[0]["json"]["messages"][1]["role"] == "user"
