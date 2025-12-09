/**
 * Browser-based Code Executor using WASM
 * 
 * Executes code in the browser for security:
 * - JavaScript: Web Worker for isolation
 * - Python: Pyodide WebAssembly runtime
 */

import type { ExecutionResult, TestResult, Problem, SupportedLanguage } from './api';

// Timeout for code execution in milliseconds
const EXECUTION_TIMEOUT = 5000;

// Pyodide instance (lazy loaded)
let pyodideInstance: any = null;
let pyodideLoadingPromise: Promise<any> | null = null;

/**
 * Load Pyodide WASM runtime (cached after first load)
 */
async function loadPyodide(): Promise<any> {
    if (pyodideInstance) {
        return pyodideInstance;
    }

    if (pyodideLoadingPromise) {
        return pyodideLoadingPromise;
    }

    pyodideLoadingPromise = (async () => {
        // Dynamic import of pyodide
        const { loadPyodide: loadPyodideModule } = await import('pyodide');
        pyodideInstance = await loadPyodideModule({
            indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/',
        });
        return pyodideInstance;
    })();

    return pyodideLoadingPromise;
}

/**
 * Execute Python code using Pyodide WASM
 */
async function executePython(code: string): Promise<ExecutionResult> {
    const startTime = performance.now();

    try {
        const pyodide = await loadPyodide();

        // Capture stdout and stderr
        let stdout = '';
        let stderr = '';

        // Set up stdout/stderr capture
        pyodide.setStdout({
            batched: (text: string) => {
                stdout += text + '\n';
            }
        });

        pyodide.setStderr({
            batched: (text: string) => {
                stderr += text + '\n';
            }
        });

        // Execute with timeout
        const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('Execution timed out')), EXECUTION_TIMEOUT);
        });

        const executionPromise = (async () => {
            await pyodide.runPythonAsync(code);
        })();

        await Promise.race([executionPromise, timeoutPromise]);

        const executionTime = performance.now() - startTime;

        return {
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: 0,
            executionTime,
        };
    } catch (error: any) {
        const executionTime = performance.now() - startTime;
        const errorMessage = error.message || String(error);

        return {
            stdout: '',
            stderr: errorMessage.includes('timed out')
                ? `Execution timed out after ${EXECUTION_TIMEOUT / 1000} seconds`
                : errorMessage,
            exitCode: 1,
            executionTime,
        };
    }
}

/**
 * Execute JavaScript code using a sandboxed Function
 * Note: For true isolation, consider using a Web Worker
 */
async function executeJavaScript(code: string): Promise<ExecutionResult> {
    const startTime = performance.now();

    try {
        // Capture console.log output
        let stdout = '';
        let stderr = '';

        const customConsole = {
            log: (...args: any[]) => {
                stdout += args.map(arg =>
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ') + '\n';
            },
            error: (...args: any[]) => {
                stderr += args.map(arg =>
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ') + '\n';
            },
            warn: (...args: any[]) => {
                stdout += args.map(arg =>
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ') + '\n';
            },
        };

        // Create a sandboxed execution environment
        // Using Function constructor for isolation from local scope
        const wrappedCode = `
      (function(console) {
        "use strict";
        ${code}
      })
    `;

        // Execute with timeout
        const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('Execution timed out')), EXECUTION_TIMEOUT);
        });

        const executionPromise = new Promise<void>((resolve, reject) => {
            try {
                const fn = eval(wrappedCode);
                fn(customConsole);
                resolve();
            } catch (e) {
                reject(e);
            }
        });

        await Promise.race([executionPromise, timeoutPromise]);

        const executionTime = performance.now() - startTime;

        return {
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: 0,
            executionTime,
        };
    } catch (error: any) {
        const executionTime = performance.now() - startTime;
        const errorMessage = error.message || String(error);

        return {
            stdout: '',
            stderr: errorMessage.includes('timed out')
                ? `Execution timed out after ${EXECUTION_TIMEOUT / 1000} seconds`
                : errorMessage,
            exitCode: 1,
            executionTime,
        };
    }
}

/**
 * Execute code in the browser
 */
export async function executeCode(code: string, language: SupportedLanguage): Promise<ExecutionResult> {
    switch (language) {
        case 'python':
            return executePython(code);
        case 'javascript':
            return executeJavaScript(code);
        default:
            return {
                stdout: '',
                stderr: `Language '${language}' is not yet supported for browser execution. Only JavaScript and Python are available.`,
                exitCode: 1,
                executionTime: 0,
            };
    }
}

/**
 * Execute Python code with test input
 */
async function executePythonWithInput(code: string, testInput: string): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    try {
        const pyodide = await loadPyodide();

        let stdout = '';
        let stderr = '';

        pyodide.setStdout({
            batched: (text: string) => {
                stdout += text + '\n';
            }
        });

        pyodide.setStderr({
            batched: (text: string) => {
                stderr += text + '\n';
            }
        });

        // Create wrapper code that executes the user's code and calls the function
        const wrapperCode = `
${code}

import json
import types

# Parse input
input_str = """${testInput}"""
local_vars = {}
exec(input_str, {}, local_vars)

# Find the main function
func = None
for name, obj in list(globals().items()):
    if isinstance(obj, types.FunctionType) and not name.startswith('_'):
        func = obj
        break

if func:
    result = func(**local_vars)
    print(json.dumps(result) if not isinstance(result, str) else result)
else:
    print("No function found")
`;

        await pyodide.runPythonAsync(wrapperCode);

        return {
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: stderr ? 1 : 0,
        };
    } catch (error: any) {
        return {
            stdout: '',
            stderr: error.message || String(error),
            exitCode: 1,
        };
    }
}

/**
 * Execute JavaScript code with test input
 */
async function executeJavaScriptWithInput(code: string, testInput: string): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    try {
        let stdout = '';
        let stderr = '';

        const customConsole = {
            log: (...args: any[]) => {
                stdout += args.map(arg =>
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ') + '\n';
            },
            error: (...args: any[]) => {
                stderr += args.map(arg =>
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ') + '\n';
            },
        };

        // Parse test input to extract variables
        const vars: Record<string, any> = {};
        const assignments = testInput.split(',').map(s => s.trim());

        for (const assignment of assignments) {
            const match = assignment.match(/^(\w+)\s*=\s*(.+)$/);
            if (match) {
                const [, name, value] = match;
                try {
                    vars[name] = eval(value);
                } catch {
                    vars[name] = value;
                }
            }
        }

        // Create wrapper that calls the function
        const wrapperCode = `
      (function(console, vars) {
        "use strict";
        ${code}
        
        // Find and call the main function
        const funcNames = ['solution', 'twoSum', 'two_sum', 'solve', 'main'];
        let func = null;
        
        for (const name of funcNames) {
          if (typeof eval(name) === 'function') {
            func = eval(name);
            break;
          }
        }
        
        // Try to find any function defined in the code
        if (!func) {
          const match = ${JSON.stringify(code)}.match(/function\\s+(\\w+)/);
          if (match) {
            func = eval(match[1]);
          }
        }
        
        if (func) {
          const args = Object.values(vars);
          const result = func(...args);
          console.log(JSON.stringify(result));
        } else {
          console.log("No function found");
        }
      })
    `;

        const fn = eval(wrapperCode);
        fn(customConsole, vars);

        return {
            stdout: stdout.trim(),
            stderr: stderr.trim(),
            exitCode: stderr ? 1 : 0,
        };
    } catch (error: any) {
        return {
            stdout: '',
            stderr: error.message || String(error),
            exitCode: 1,
        };
    }
}

/**
 * Run tests against a problem's test cases
 */
export async function runTests(code: string, language: SupportedLanguage, problem: Problem): Promise<ExecutionResult> {
    if (language !== 'python' && language !== 'javascript') {
        return {
            stdout: '',
            stderr: `Language '${language}' is not yet supported for testing. Only JavaScript and Python are available.`,
            exitCode: 1,
            executionTime: 0,
        };
    }

    if (!problem || !problem.examples || problem.examples.length === 0) {
        return {
            stdout: 'No test cases available for this problem.',
            stderr: '',
            exitCode: 0,
            executionTime: 0,
        };
    }

    const startTime = performance.now();
    const testResults: TestResult[] = [];
    let allPassed = true;

    for (const example of problem.examples) {
        const inputStr = example.input;
        const expectedOutput = example.output.trim();

        let result: { stdout: string; stderr: string; exitCode: number };

        if (language === 'python') {
            result = await executePythonWithInput(code, inputStr);
        } else {
            result = await executeJavaScriptWithInput(code, inputStr);
        }

        // Normalize outputs for comparison
        const actualNormalized = result.stdout.trim().replace(/\s/g, '');
        const expectedNormalized = expectedOutput.replace(/\s/g, '');

        const passed = actualNormalized === expectedNormalized && result.exitCode === 0;

        if (!passed) {
            allPassed = false;
        }

        testResults.push({
            passed,
            input: inputStr,
            expected: expectedOutput,
            actual: result.stdout || result.stderr,
        });
    }

    const executionTime = performance.now() - startTime;
    const passedCount = testResults.filter(t => t.passed).length;
    const totalCount = testResults.length;

    return {
        stdout: `Ran ${totalCount} tests: ${passedCount}/${totalCount} passed`,
        stderr: '',
        exitCode: allPassed ? 0 : 1,
        executionTime,
        testResults,
    };
}

/**
 * Check if Pyodide is loaded (for UI loading state)
 */
export function isPyodideLoaded(): boolean {
    return pyodideInstance !== null;
}

/**
 * Preload Pyodide (optional - call early to reduce first-run latency)
 */
export async function preloadPyodide(): Promise<void> {
    await loadPyodide();
}
