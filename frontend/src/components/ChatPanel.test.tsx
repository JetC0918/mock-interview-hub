import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import ChatPanel from './ChatPanel';

describe('ChatPanel', () => {
  const mockMessages = [
    {
      id: '1',
      participantId: 'user1',
      username: 'Alice',
      message: 'Hello everyone!',
      timestamp: new Date('2024-01-01T10:00:00'),
    },
    {
      id: '2',
      participantId: 'user2',
      username: 'Bob',
      message: 'Hi Alice!',
      timestamp: new Date('2024-01-01T10:01:00'),
    },
  ];

  const mockParticipants = [
    { id: 'user1', username: 'Alice', role: 'host' as const, color: '#00ff00', joinedAt: new Date() },
    { id: 'user2', username: 'Bob', role: 'participant' as const, color: '#ff0000', joinedAt: new Date() },
  ];

  it('should render chat messages', () => {
    render(
      <ChatPanel
        messages={mockMessages}
        participants={mockParticipants}
        currentUserId="user1"
        onSendMessage={vi.fn()}
      />
    );
    
    expect(screen.getByText('Hello everyone!')).toBeInTheDocument();
    expect(screen.getByText('Hi Alice!')).toBeInTheDocument();
  });

  it('should display participant names', () => {
    render(
      <ChatPanel
        messages={mockMessages}
        participants={mockParticipants}
        currentUserId="user1"
        onSendMessage={vi.fn()}
      />
    );
    
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('should call onSendMessage when submitting', async () => {
    const user = userEvent.setup();
    const onSendMessage = vi.fn();
    
    render(
      <ChatPanel
        messages={[]}
        participants={[]}
        currentUserId="user1"
        onSendMessage={onSendMessage}
      />
    );
    
    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'New message');
    await user.keyboard('{Enter}');
    
    expect(onSendMessage).toHaveBeenCalledWith('New message');
  });

  it('should clear input after sending message', async () => {
    const user = userEvent.setup();
    
    render(
      <ChatPanel
        messages={[]}
        participants={[]}
        currentUserId="user1"
        onSendMessage={vi.fn()}
      />
    );
    
    const input = screen.getByPlaceholderText(/type a message/i) as HTMLInputElement;
    await user.type(input, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(input.value).toBe('');
  });
});
