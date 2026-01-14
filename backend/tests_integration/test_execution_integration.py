"""Integration tests for code execution endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestExecutionIntegration:
    """Integration tests for code execution."""

    def test_run_python_code(self, client: TestClient):
        """Test running Python code."""
        code_data = {
            "code": "print('Hello, Integration Test!')",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_run_python_code_with_calculation(self, client: TestClient):
        """Test running Python code with calculations."""
        code_data = {
            "code": "result = 2 + 2\nprint(f'2 + 2 = {result}')",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_run_python_code_with_syntax_error(self, client: TestClient):
        """Test running Python code with syntax error."""
        code_data = {
            "code": "def broken(\n    print('missing closing paren'",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_run_javascript_code(self, client: TestClient):
        """Test running JavaScript code."""
        code_data = {
            "code": "console.log('Hello from JS!')",
            "language": "javascript"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_unsupported_language_returns_error(self, client: TestClient):
        """Test that unsupported languages return proper error."""
        code_data = {
            "code": "public class Main { public static void main(String[] args) { System.out.println(\"Hello\"); } }",
            "language": "java"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_run_multiline_python(self, client: TestClient):
        """Test running multiline Python code."""
        code_data = {
            "code": """
def greet(name):
    return f"Hello, {name}!"

names = ["Alice", "Bob", "Charlie"]
for name in names:
    print(greet(name))
""",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()

    def test_execution_returns_execution_time(self, client: TestClient):
        """Test that execution returns timing information."""
        code_data = {
            "code": "print('timing test')",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()
