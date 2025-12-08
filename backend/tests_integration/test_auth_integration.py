"""Integration tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestAuthIntegration:
    """Integration tests for the auth workflow."""

    def test_signup_creates_user(self, client: TestClient):
        """Test that signup creates a new user successfully."""
        signup_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        response = client.post("/auth/signup", json=signup_data)
        
        assert response.status_code == 201
        user = response.json()
        assert user["username"] == "newuser"
        assert user["email"] == "newuser@example.com"
        assert "id" in user
        assert "password" not in user  # Password should not be returned

    def test_signup_duplicate_email_fails(self, client: TestClient):
        """Test that signup fails with duplicate email."""
        signup_data = {
            "username": "firstuser",
            "email": "duplicate@example.com",
            "password": "password123"
        }
        # First signup should succeed
        response = client.post("/auth/signup", json=signup_data)
        assert response.status_code == 201
        
        # Second signup with same email should fail
        duplicate_data = {
            "username": "seconduser",
            "email": "duplicate@example.com",
            "password": "differentpassword"
        }
        response = client.post("/auth/signup", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_with_valid_credentials(self, client: TestClient):
        """Test that login works with valid credentials."""
        # First signup
        signup_data = {
            "username": "logintest",
            "email": "logintest@example.com",
            "password": "mypassword"
        }
        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 201
        user_id = signup_response.json()["id"]
        
        # Then login
        login_data = {
            "email": "logintest@example.com",
            "password": "mypassword"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        logged_in_user = response.json()
        assert logged_in_user["id"] == user_id
        assert logged_in_user["email"] == "logintest@example.com"

    def test_login_with_wrong_password(self, client: TestClient):
        """Test that login fails with incorrect password."""
        # First signup
        signup_data = {
            "username": "wrongpwtest",
            "email": "wrongpw@example.com",
            "password": "correctpassword"
        }
        client.post("/auth/signup", json=signup_data)
        
        # Try login with wrong password
        login_data = {
            "email": "wrongpw@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect password" in response.json()["detail"].lower()

    def test_login_with_nonexistent_user(self, client: TestClient):
        """Test that login fails for non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_guest_login(self, client: TestClient):
        """Test that guest login creates a user without email."""
        guest_data = {"username": "GuestPlayer"}
        response = client.post("/auth/guest", json=guest_data)
        
        assert response.status_code == 201
        guest = response.json()
        assert guest["username"] == "GuestPlayer"
        assert guest["email"] is None

    def test_logout(self, client: TestClient):
        """Test that logout endpoint returns success."""
        response = client.post("/auth/logout")
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    def test_full_auth_workflow(self, client: TestClient):
        """Test complete auth workflow: signup -> login -> me -> logout."""
        # Signup
        signup_data = {
            "username": "workflowuser",
            "email": "workflow@example.com",
            "password": "workflowpass"
        }
        signup_response = client.post("/auth/signup", json=signup_data)
        assert signup_response.status_code == 201
        
        # Login
        login_data = {
            "email": "workflow@example.com",
            "password": "workflowpass"
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Get current user (me)
        me_response = client.get("/auth/me")
        assert me_response.status_code == 200
        
        # Logout
        logout_response = client.post("/auth/logout")
        assert logout_response.status_code == 200
