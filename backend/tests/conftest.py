import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.mock_db import MockDB, db

@pytest.fixture(scope="module")
def client():
    # Reset db for tests if needed, but module scope is fine for simple tests
    # Ideally use a fresh db instance per test but we are using a global singleton
    # We can clear it
    db.users = {}
    db.sessions = {}
    db.messages = {}
    return TestClient(app)
