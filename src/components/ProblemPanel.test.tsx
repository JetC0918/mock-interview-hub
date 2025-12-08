import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import ProblemPanel from './ProblemPanel';

describe('ProblemPanel', () => {
  const mockProblem = {
    id: '1',
    title: 'Two Sum',
    description: 'Find two numbers that add up to target.',
    examples: [
      { input: '[2,7,11,15], target=9', output: '[0,1]', explanation: 'nums[0] + nums[1] = 9' },
      { input: '[3,2,4], target=6', output: '[1,2]' },
    ],
    constraints: ['2 <= nums.length <= 10^4'],
    difficulty: 'easy' as const,
  };

  it('should render problem title', () => {
    render(<ProblemPanel problem={mockProblem} />);
    
    expect(screen.getByText('Two Sum')).toBeInTheDocument();
  });

  it('should render problem description', () => {
    render(<ProblemPanel problem={mockProblem} />);
    
    expect(screen.getByText('Find two numbers that add up to target.')).toBeInTheDocument();
  });

  it('should render examples', () => {
    render(<ProblemPanel problem={mockProblem} />);
    
    expect(screen.getByText(/\[2,7,11,15\]/)).toBeInTheDocument();
    expect(screen.getByText(/\[0,1\]/)).toBeInTheDocument();
  });

  it('should render constraints', () => {
    render(<ProblemPanel problem={mockProblem} />);
    
    expect(screen.getByText('2 <= nums.length <= 10^4')).toBeInTheDocument();
  });

  it('should show difficulty badge', () => {
    render(<ProblemPanel problem={mockProblem} />);
    
    expect(screen.getByText('easy')).toBeInTheDocument();
  });

  it('should show loading state when no problem', () => {
    render(<ProblemPanel problem={undefined} />);
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
