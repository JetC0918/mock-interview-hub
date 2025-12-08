import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import OutputPanel from './OutputPanel';

describe('OutputPanel', () => {
  it('should render stdout output', () => {
    const result = {
      stdout: 'Hello, World!',
      stderr: '',
      exitCode: 0,
      executionTime: 15,
    };
    
    render(<OutputPanel result={result} isRunning={false} />);
    
    expect(screen.getByText('Hello, World!')).toBeInTheDocument();
  });

  it('should render stderr output', () => {
    const result = {
      stdout: '',
      stderr: 'Error: Something went wrong',
      exitCode: 1,
      executionTime: 5,
    };
    
    render(<OutputPanel result={result} isRunning={false} />);
    
    expect(screen.getByText('Error: Something went wrong')).toBeInTheDocument();
  });

  it('should show execution time', () => {
    const result = {
      stdout: 'Output',
      stderr: '',
      exitCode: 0,
      executionTime: 123,
    };
    
    render(<OutputPanel result={result} isRunning={false} />);
    
    expect(screen.getByText(/123/)).toBeInTheDocument();
  });

  it('should show running state', () => {
    render(<OutputPanel result={null} isRunning={true} />);
    
    expect(screen.getByText(/running/i)).toBeInTheDocument();
  });

  it('should render test results', () => {
    const result = {
      stdout: '',
      stderr: '',
      exitCode: 0,
      executionTime: 50,
      testResults: [
        { passed: true, input: '[1,2]', expected: '3', actual: '3' },
        { passed: false, input: '[3,4]', expected: '7', actual: '6' },
      ],
    };
    
    render(<OutputPanel result={result} isRunning={false} />);
    
    expect(screen.getByText(/passed/i)).toBeInTheDocument();
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
  });

  it('should show placeholder when no output', () => {
    render(<OutputPanel result={null} isRunning={false} />);
    
    expect(screen.getByText(/run your code/i)).toBeInTheDocument();
  });
});
