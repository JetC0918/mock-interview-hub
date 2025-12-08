import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, Participant } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send } from 'lucide-react';

interface ChatPanelProps {
  messages: ChatMessage[];
  participants: Participant[];
  onSendMessage: (message: string) => void;
  currentUserId: string;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  participants,
  onSendMessage,
  currentUserId,
}) => {
  const [newMessage, setNewMessage] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim()) {
      onSendMessage(newMessage.trim());
      setNewMessage('');
    }
  };

  const getParticipantColor = (participantId: string) => {
    const participant = participants.find((p) => p.id === participantId);
    return participant?.color || 'hsl(var(--muted-foreground))';
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-lg border border-border">
      <div className="px-4 py-3 border-b border-border">
        <h3 className="font-semibold">Chat</h3>
      </div>
      
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-3">
          {messages.length === 0 ? (
            <p className="text-muted-foreground text-sm text-center py-4">
              No messages yet
            </p>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex flex-col ${
                  message.participantId === currentUserId ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 ${
                    message.participantId === currentUserId
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary'
                  }`}
                >
                  {message.participantId !== currentUserId && (
                    <span
                      className="text-xs font-medium block mb-1"
                      style={{ color: getParticipantColor(message.participantId) }}
                    >
                      {message.username}
                    </span>
                  )}
                  <p className="text-sm">{message.message}</p>
                </div>
                <span className="text-xs text-muted-foreground mt-1">
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmit} className="p-3 border-t border-border flex gap-2">
        <Input
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          className="flex-1"
        />
        <Button type="submit" size="icon" disabled={!newMessage.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
};

export default ChatPanel;
