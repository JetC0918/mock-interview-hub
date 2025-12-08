from fastapi import APIRouter, HTTPException
from ..models.execution import ExecutionRequest, TestRequest, ExecutionResult, TestResult
from ..services.code_executor import execute_python_code, execute_with_input
from ..services.mock_db import db
import json

router = APIRouter(prefix="/execution", tags=["Execution"])

@router.post("/run", response_model=ExecutionResult)
def run_code(body: ExecutionRequest):
    """Actually execute the submitted code and return real output."""
    
    if body.language != "python":
        # For non-Python, return a message that only Python is supported
        return ExecutionResult(
            stdout="",
            stderr=f"Language '{body.language}' is not yet supported. Only Python execution is available.",
            exitCode=1,
            executionTime=0.0
        )
    
    stdout, stderr, exit_code, execution_time = execute_python_code(body.code)
    
    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        exitCode=exit_code,
        executionTime=execution_time
    )

@router.post("/test", response_model=ExecutionResult)
def run_tests(body: TestRequest):
    """Run the code against the problem's test cases."""
    
    if body.language != "python":
        return ExecutionResult(
            stdout="",
            stderr=f"Language '{body.language}' is not yet supported for testing. Only Python is available.",
            exitCode=1,
            executionTime=0.0
        )
    
    if not body.problem or not body.problem.examples:
        return ExecutionResult(
            stdout="No test cases available for this problem.",
            stderr="",
            exitCode=0,
            executionTime=0.0
        )
    
    test_results = []
    all_passed = True
    total_time = 0.0
    
    for i, example in enumerate(body.problem.examples):
        # Parse the input string - extract variable assignments
        input_str = example.input
        expected_output = example.output.strip()
        
        # Execute the code with this test case
        stdout, stderr, exit_code = execute_with_input(body.code, input_str)
        
        # Check if output matches expected
        # Normalize outputs for comparison (handle list format variations)
        actual_normalized = stdout.strip().replace(" ", "")
        expected_normalized = expected_output.replace(" ", "")
        
        passed = (actual_normalized == expected_normalized) and exit_code == 0
        
        if not passed:
            all_passed = False
        
        test_results.append(TestResult(
            passed=passed,
            input=input_str,
            expected=expected_output,
            actual=stdout if stdout else stderr
        ))
    
    # Build summary stdout
    passed_count = sum(1 for t in test_results if t.passed)
    total_count = len(test_results)
    
    return ExecutionResult(
        stdout=f"Ran {total_count} tests: {passed_count}/{total_count} passed",
        stderr="",
        exitCode=0 if all_passed else 1,
        executionTime=total_time,
        testResults=test_results
    )
