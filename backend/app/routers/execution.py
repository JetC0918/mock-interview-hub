from fastapi import APIRouter, HTTPException
from ..models.execution import ExecutionRequest, TestRequest, ExecutionResult, TestResult
from ..services.mock_db import db
import random
import time

router = APIRouter(prefix="/execution", tags=["Execution"])

@router.post("/run", response_model=ExecutionResult)
def run_code(body: ExecutionRequest):
    # Mock execution logic
    time.sleep(0.5) # Simulate delay
    
    # Simple mock response based on code content
    if "error" in body.code:
        return ExecutionResult(
            stdout="",
            stderr="SyntaxError: invalid syntax",
            exitCode=1,
            executionTime=0.1
        )
    
    return ExecutionResult(
        stdout="Hello World\n",
        stderr="",
        exitCode=0,
        executionTime=0.2
    )

@router.post("/test", response_model=ExecutionResult)
def run_tests(body: TestRequest):
    time.sleep(1)
    
    # Mock tests based on problem
    # For now simply return passed
    test_results = [
        TestResult(
            passed=True,
            input="nums = [2,7], target = 9",
            expected="[0,1]",
            actual="[0,1]"
        ),
        TestResult(
            passed=True,
            input="[3,2,4], 6",
            expected="[1,2]",
            actual="[1,2]"
        )
    ]
    
    return ExecutionResult(
        stdout="Ran 2 tests in 0.001s",
        stderr="",
        exitCode=0,
        executionTime=1.0,
        testResults=test_results
    )
