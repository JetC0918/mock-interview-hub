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
        
        assert response.status_code == 200
        result = response.json()
        assert "Hello, Integration Test!" in result["stdout"]
        assert result["stderr"] == ""

    def test_run_python_code_with_calculation(self, client: TestClient):
        """Test running Python code with calculations."""
        code_data = {
            "code": "result = 2 + 2\nprint(f'2 + 2 = {result}')",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 200
        result = response.json()
        assert "2 + 2 = 4" in result["stdout"]

    def test_run_python_code_with_syntax_error(self, client: TestClient):
        """Test running Python code with syntax error."""
        code_data = {
            "code": "def broken(\n    print('missing closing paren'",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 200
        result = response.json()
        # Should have error in stderr
        assert result["stderr"] != "" or "SyntaxError" in result.get("stdout", "")

    def test_run_javascript_code(self, client: TestClient):
        """Test running JavaScript code."""
        code_data = {
            "code": "console.log('Hello from JS!')",
            "language": "javascript"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 200
        result = response.json()
        # JavaScript is now supported
        assert "Hello from JS!" in result["stdout"]
        assert result["exitCode"] == 0

    def test_unsupported_language_returns_error(self, client: TestClient):
        """Test that unsupported languages return proper error."""
        code_data = {
            "code": "public class Main { public static void main(String[] args) { System.out.println(\"Hello\"); } }",
            "language": "java"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 200
        result = response.json()
        assert "not yet supported" in result["stderr"].lower()
        assert result["exitCode"] == 1

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
        
        assert response.status_code == 200
        result = response.json()
        assert "Hello, Alice!" in result["stdout"]
        assert "Hello, Bob!" in result["stdout"]
        assert "Hello, Charlie!" in result["stdout"]

    def test_execution_returns_execution_time(self, client: TestClient):
        """Test that execution returns timing information."""
        code_data = {
            "code": "print('timing test')",
            "language": "python"
        }
        response = client.post("/execution/run", json=code_data)
        
        assert response.status_code == 200
        result = response.json()
        # Check that executionTime is present and is a number
        assert "executionTime" in result
        assert isinstance(result["executionTime"], (int, float))
        assert result["executionTime"] >= 0
