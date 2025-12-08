"""
Code Execution Service
Uses subprocess to actually run Python code with safety limits.
"""
import subprocess
import sys
import tempfile
import os
import time
from typing import Optional, Tuple

# Timeout in seconds
EXECUTION_TIMEOUT = 5

def execute_python_code(code: str) -> Tuple[str, str, int, float]:
    """
    Execute Python code and return (stdout, stderr, exit_code, execution_time).
    Uses subprocess with timeout for basic safety.
    """
    start_time = time.time()
    
    # Create a temporary file with the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Run the code in a subprocess
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            cwd=tempfile.gettempdir()  # Run in temp dir for isolation
        )
        
        execution_time = time.time() - start_time
        return (
            result.stdout,
            result.stderr,
            result.returncode,
            execution_time
        )
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return (
            "",
            f"Execution timed out after {EXECUTION_TIMEOUT} seconds",
            1,
            execution_time
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return (
            "",
            f"Execution error: {str(e)}",
            1,
            execution_time
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass


def execute_with_input(code: str, test_input: str) -> Tuple[str, str, int]:
    """
    Execute Python code with a specific input, capturing the output.
    For testing purposes - wraps the user's function and calls it.
    """
    # Create a wrapper that calls the function with the test input
    wrapper_code = f'''
{code}

# Test runner
import sys
import json

try:
    # Parse input
    input_str = """{test_input}"""
    
    # Try to execute the input as Python code to get the actual values
    # e.g., "nums = [2,7,11,15], target = 9" -> nums=[2,7,11,15], target=9
    local_vars = {{}}
    exec(input_str, {{}}, local_vars)
    
    # Find the main function (first defined function)
    import types
    func = None
    for name, obj in list(globals().items()):
        if isinstance(obj, types.FunctionType) and not name.startswith('_'):
            func = obj
            break
    
    if func:
        # Get argument names from the input
        result = func(**local_vars)
        print(json.dumps(result) if not isinstance(result, str) else result)
    else:
        print("No function found")
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
    
    stdout, stderr, exit_code, _ = execute_python_code(wrapper_code)
    return stdout.strip(), stderr.strip(), exit_code
