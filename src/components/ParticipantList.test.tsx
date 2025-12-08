import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import ParticipantList from './ParticipantList';

describe('ParticipantList', () => {
  const mockParticipants = [
    {
      id: 'host1',
      username: 'HostUser',
      role: 'host' as const,
      color: '#00ff00',
      isTyping: false,
      joinedAt: new Date(),
    },
    {
      id: 'part1',
      username: 'Participant1',
      role: 'participant' as const,
      color: '#ff0000',
      isTyping: true,
      joinedAt: new Date(),
    },
    {
      id: 'spec1',
      username: 'Spectator1',
      role: 'spectator' as const,
      color: '#0000ff',
      isTyping: false,
      joinedAt: new Date(),
    },
  ];

  it('should render all participants', () => {
    render(<ParticipantList participants={mockParticipants} currentUserId="host1" />);
    
    expect(screen.getByText('HostUser')).toBeInTheDocument();
    expect(screen.getByText('Participant1')).toBeInTheDocument();
    expect(screen.getByText('Spectator1')).toBeInTheDocument();
  });

  it('should display host badge', () => {
    render(<ParticipantList participants={mockParticipants} currentUserId="host1" />);
    
    expect(screen.getByText('Host')).toBeInTheDocument();
  });

  it('should show typing indicator for typing participants', () => {
    render(<ParticipantList participants={mockParticipants} currentUserId="host1" />);
    
    expect(screen.getByText('typing...')).toBeInTheDocument();
  });

  it('should display participant count', () => {
    render(<ParticipantList participants={mockParticipants} currentUserId="host1" />);
    
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
