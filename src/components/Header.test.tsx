import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import Header from './Header';

// Mock the AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    isLoading: false,
    logout: vi.fn(),
  })),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

describe('Header Component', () => {
  it('should render the logo', () => {
    render(<Header />);
    expect(screen.getByText('CodioLive')).toBeInTheDocument();
  });

  it('should show login button when not authenticated', () => {
    render(<Header />);
    expect(screen.getByRole('link', { name: /log in/i })).toBeInTheDocument();
  });

  it('should show navigation links', () => {
    render(<Header />);
    expect(screen.getByText('Lobby')).toBeInTheDocument();
    expect(screen.getByText('Spectate')).toBeInTheDocument();
    expect(screen.getByText('Leaderboard')).toBeInTheDocument();
  });
});
