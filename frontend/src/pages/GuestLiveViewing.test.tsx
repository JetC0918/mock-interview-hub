import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '@/App';

vi.mock('@/lib/api', () => ({
  api: {
    auth: {
      getCurrentUser: vi.fn().mockResolvedValue(null),
    },
    spectator: {
      watch: vi.fn().mockResolvedValue(null),
    },
    utils: {
      getSupportedLanguages: () => [
        { value: 'typescript', label: 'TypeScript' },
      ],
    },
  },
}));

vi.mock('@monaco-editor/react', () => ({
  default: ({ value, options }: { value: string; options?: { readOnly?: boolean } }) => (
    <textarea aria-label="Live code" value={value} readOnly={options?.readOnly} />
  ),
}));

describe('guest live viewing', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/spectate/live-1');
  });

  it('opens an ongoing interview in read-only spectator mode without signing in', async () => {
    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Senior Frontend Interview' })).toBeInTheDocument();
    expect(screen.getByText('Watching as guest')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Merge Intervals' })).toBeInTheDocument();
    expect(screen.getByLabelText('Live code')).toHaveAttribute('readonly');
    expect(screen.getByText('Can you walk me through the complexity?')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /run/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/join session/i)).not.toBeInTheDocument();
  });
});
