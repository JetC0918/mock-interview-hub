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
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should show navigation links', () => {
    render(<Header />);
    expect(screen.getByText('Sessions')).toBeInTheDocument();
    expect(screen.getByText('Spectate')).toBeInTheDocument();
  });
});
