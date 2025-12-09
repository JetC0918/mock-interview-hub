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


def execute_javascript_code(code: str) -> Tuple[str, str, int, float]:
    """
    Execute JavaScript code using Node.js and return (stdout, stderr, exit_code, execution_time).
    Uses subprocess with timeout for basic safety.
    """
    start_time = time.time()
    
    # Create a temporary file with the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Run the code in a subprocess using Node.js
        result = subprocess.run(
            ['node', temp_file],
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
    except FileNotFoundError:
        execution_time = time.time() - start_time
        return (
            "",
            "Node.js is not installed. JavaScript execution is not available.",
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


def execute_javascript_with_input(code: str, test_input: str) -> Tuple[str, str, int]:
    """
    Execute JavaScript code with a specific input, capturing the output.
    For testing purposes - wraps the user's function and calls it.
    """
    # Create a wrapper that calls the function with the test input
    # Parse the input string to extract variable assignments
    wrapper_code = f'''
{code}

// Test runner
try {{
    // Parse input string
    const inputStr = `{test_input}`;
    
    // Extract variable assignments from the input
    // e.g., "nums = [2,7,11,15], target = 9" -> nums=[2,7,11,15], target=9
    const vars = {{}};
    const assignments = inputStr.split(',').map(s => s.trim());
    
    for (const assignment of assignments) {{
        const match = assignment.match(/^(\\w+)\\s*=\\s*(.+)$/);
        if (match) {{
            const [, name, value] = match;
            try {{
                vars[name] = eval(value);
            }} catch (e) {{
                vars[name] = value;
            }}
        }}
    }}
    
    // Find the main function (first defined function in the code)
    // Look for common function patterns
    const funcNames = Object.keys(this).filter(k => typeof this[k] === 'function');
    
    // Try common LeetCode-style function names first
    const commonNames = ['solution', 'twoSum', 'two_sum', 'solve', 'main'];
    let func = null;
    
    for (const name of commonNames) {{
        if (typeof global[name] === 'function') {{
            func = global[name];
            break;
        }}
    }}
    
    // If no common name found, try to find any user-defined function
    if (!func) {{
        // Look for function defined in global scope
        const match = `{code}`.match(/function\\s+(\\w+)/);
        if (match && typeof global[match[1]] === 'function') {{
            func = global[match[1]];
        }}
    }}
    
    if (func) {{
        // Call the function with the parsed variables as arguments
        const args = Object.values(vars);
        const result = func(...args);
        console.log(JSON.stringify(result));
    }} else {{
        console.log("No function found");
    }}
}} catch (e) {{
    console.error("Error: " + e.message);
    process.exit(1);
}}
'''
    
    stdout, stderr, exit_code, _ = execute_javascript_code(wrapper_code)
    return stdout.strip(), stderr.strip(), exit_code

