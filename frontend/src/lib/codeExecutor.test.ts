import { describe, expect, it } from 'vitest';
import { executeCode, runTests } from './codeExecutor';

describe('collaborative code executor safety boundary', () => {
  it('returns a disabled result instead of executing shared JavaScript', async () => {
    const result = await executeCode('fetch("/auth/me")', 'javascript');

    expect(result.exitCode).toBe(1);
    expect(result.stderr).toContain('fully isolated runtime');
  });

  it('does not execute shared code while running tests', async () => {
    const result = await runTests('window.localStorage.clear()', 'javascript', {
      id: 'problem',
      title: 'Problem',
      description: '',
      examples: [],
      constraints: [],
      difficulty: 'easy',
    });

    expect(result.exitCode).toBe(1);
    expect(result.stderr).toContain('fully isolated runtime');
  });
});
