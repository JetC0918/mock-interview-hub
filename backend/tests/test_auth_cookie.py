from fastapi import Response

from app.routers.auth import set_secure_cookie


def test_secure_cookie_uses_explicit_environment_flag(monkeypatch):
    monkeypatch.setenv("COOKIE_SECURE", "true")
    response = Response()

    set_secure_cookie(response, "user-123")

    assert "Secure" in response.headers["set-cookie"]
