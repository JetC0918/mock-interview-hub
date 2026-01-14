"""
Code Execution Router - DISABLED FOR SECURITY

Code execution now happens client-side via WebAssembly (Pyodide).
These endpoints are kept for API compatibility but return 503.
"""
from fastapi import APIRouter, HTTPException
from ..models.execution import ExecutionRequest, TestRequest, ExecutionResult

router = APIRouter(prefix="/execution", tags=["Execution"])


@router.post("/run", response_model=ExecutionResult)
def run_code(body: ExecutionRequest):
    """
    Code execution is disabled on the server for security reasons.
    Please use the browser-based code execution (WebAssembly).
    """
    raise HTTPException(
        status_code=503,
        detail="Server-side code execution is disabled for security. Code runs in your browser instead."
    )


@router.post("/test", response_model=ExecutionResult)
def run_tests(body: TestRequest):
    """
    Test execution is disabled on the server for security reasons.
    Please use the browser-based test execution (WebAssembly).
    """
    raise HTTPException(
        status_code=503,
        detail="Server-side test execution is disabled for security. Tests run in your browser instead."
    )
