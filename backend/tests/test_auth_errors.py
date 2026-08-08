from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    response = client.post("/auth/login", json={"email": "algo@example.com", "password": "password"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "algo@example.com"
    assert data["username"] == "AlgoGuru"


def test_login_user_not_found(client: TestClient):
    response = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_wrong_password(client: TestClient):
    response = client.post("/auth/login", json={"email": "algo@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
