import React from 'react';
import { Participant } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Crown, Eye, User } from 'lucide-react';

interface ParticipantListProps {
  participants: Participant[];
  currentUserId: string;
}

const ParticipantList: React.FC<ParticipantListProps> = ({
  participants,
  currentUserId,
}) => {
  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'host':
        return <Crown className="h-3 w-3" />;
      case 'spectator':
        return <Eye className="h-3 w-3" />;
      default:
        return <User className="h-3 w-3" />;
    }
  };

  return (
    <div className="bg-card rounded-lg border border-border">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold">Participants</h3>
        <Badge variant="secondary">{participants.length}</Badge>
      </div>
      <ScrollArea className="h-[200px]">
        <div className="p-2 space-y-1">
          {participants.map((participant) => (
            <div
              key={participant.id}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                participant.id === currentUserId
                  ? 'bg-primary/10'
                  : 'hover:bg-secondary'
              }`}
            >
              <div
                className="h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium"
                style={{ backgroundColor: participant.color + '33', color: participant.color }}
              >
                {participant.username.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate">
                    {participant.username}
                    {participant.id === currentUserId && (
                      <span className="text-muted-foreground"> (you)</span>
                    )}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  {getRoleIcon(participant.role)}
                  <span className="capitalize">{participant.role}</span>
                  {participant.isTyping && (
                    <span className="ml-2 text-primary animate-pulse">typing...</span>
                  )}
                </div>
              </div>
              <div
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: participant.color }}
              />
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

export default ParticipantList;
