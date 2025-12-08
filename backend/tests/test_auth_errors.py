from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/login", json={"email": "algo@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "algo@example.com"
    assert data["username"] == "AlgoGuru"

def test_login_user_not_found():
    response = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "password"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_login_wrong_password():
    response = client.post("/auth/login", json={"email": "algo@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"
