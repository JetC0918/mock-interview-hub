import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '@/App';

vi.mock('@/lib/api', () => ({
  api: {
    auth: {
      getCurrentUser: vi.fn().mockResolvedValue(null),
    },
    spectator: {
      watch: vi.fn().mockResolvedValue({
        id: 'live-1',
        pin: '',
        hostId: '',
        title: 'Senior Frontend Interview',
        description: 'Live coding interview',
        language: 'typescript',
        participants: [{
          id: 'participant-1',
          username: 'Maya',
          role: 'host',
          color: '#2563eb',
          joinedAt: new Date('2026-08-10T05:00:00Z'),
        }],
        code: 'function mergeIntervals() {}',
        codeRevision: 1,
        status: 'active',
        createdAt: new Date('2026-08-10T05:00:00Z'),
        problem: {
          id: 'problem-1',
          title: 'Merge Intervals',
          description: 'Merge all overlapping intervals.',
          examples: [],
          constraints: [],
          difficulty: 'medium',
        },
      }),
      getMessages: vi.fn().mockResolvedValue([{
        id: 'message-1',
        participantId: 'participant-1',
        username: 'Maya',
        message: 'Can you walk me through the complexity?',
        timestamp: new Date('2026-08-10T05:01:00Z'),
      }]),
    },
    utils: {
      getSupportedLanguages: () => [
        { value: 'typescript', label: 'TypeScript' },
      ],
    },
  },
}));

vi.mock('@monaco-editor/react', () => ({
  loader: { config: vi.fn() },
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
