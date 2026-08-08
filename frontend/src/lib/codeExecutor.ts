/**
 * Collaborative code execution is intentionally disabled until it can run in
 * a separately isolated origin/service with resource limits.
 *
 * Never reintroduce eval, Function, or a browser-context interpreter here:
 * shared participant code is attacker-controlled input.
 */

import type { ExecutionResult, Problem, SupportedLanguage } from './api';

const DISABLED_MESSAGE =
  'Code execution is temporarily disabled until a fully isolated runtime is available.';

function disabledResult(): ExecutionResult {
  return {
    stdout: '',
    stderr: DISABLED_MESSAGE,
    exitCode: 1,
    executionTime: 0,
  };
}

export async function executeCode(
  _code: string,
  _language: SupportedLanguage,
): Promise<ExecutionResult> {
  return disabledResult();
}

export async function runTests(
  _code: string,
  _language: SupportedLanguage,
  _problem: Problem,
): Promise<ExecutionResult> {
  return disabledResult();
}

export function isPyodideLoaded(): boolean {
  return false;
}

export async function preloadPyodide(): Promise<void> {
  throw new Error(DISABLED_MESSAGE);
}
