import asyncio
import pytest

import app.services.ai_service as ai_service_module
from app.services.ai_service import AIAssistantService


def test_ai_service_requires_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        AIAssistantService()


def test_ai_service_calls_gemini_flash(monkeypatch):
    requests = []

    class FakeResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        def raise_for_status(self):
            return None

        async def aiter_bytes(self):
            yield b'{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"Consider sorting the intervals first."}]}}]}'

    class FakeAsyncClient:
        def __init__(self, *, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        def stream(self, method, url, *, headers, json):
            requests.append({
                "method": method,
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": self.timeout,
            })
            return FakeResponse()

    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")
    monkeypatch.setattr(ai_service_module.httpx, "AsyncClient", FakeAsyncClient)

    service = AIAssistantService()
    result = asyncio.run(service.get_guidance("What should I do first?"))

    assert result == "Consider sorting the intervals first."
    assert requests[0]["method"] == "POST"
    assert requests[0]["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.6-flash:generateContent"
    )
    assert requests[0]["headers"]["x-goog-api-key"] == "test-secret"
    assert requests[0]["json"]["systemInstruction"]["parts"][0]["text"] == service.SYSTEM_PROMPT
    assert requests[0]["json"]["contents"][0]["role"] == "user"
    assert requests[0]["json"]["contents"][0]["parts"][0]["text"] == "User's question: What should I do first?"
    assert requests[0]["json"]["generationConfig"]["maxOutputTokens"] == 1_000
    assert requests[0]["json"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "minimal"
