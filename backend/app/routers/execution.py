"""
Code Execution Router - DISABLED FOR SECURITY

These endpoints are kept for API compatibility but return 503. No browser or
server-side interpreter is loaded by this application.
"""
from fastapi import APIRouter, HTTPException
from ..models.execution import ExecutionRequest, TestRequest, ExecutionResult

router = APIRouter(prefix="/execution", tags=["Execution"])


@router.post("/run", response_model=ExecutionResult)
def run_code(body: ExecutionRequest):
    """
    Code execution is disabled on the server for security reasons.
    An isolated execution service is required before code can run.
    """
    raise HTTPException(
        status_code=503,
        detail="Code execution is disabled until an isolated runtime is available."
    )


@router.post("/test", response_model=ExecutionResult)
def run_tests(body: TestRequest):
    """
    Test execution is disabled on the server for security reasons.
    An isolated execution service is required before tests can run.
    """
    raise HTTPException(
        status_code=503,
        detail="Test execution is disabled until an isolated runtime is available."
    )
