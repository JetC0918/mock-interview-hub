import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, Participant } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, Loader2 } from 'lucide-react';

interface ChatPanelProps {
  messages: ChatMessage[];
  participants: Participant[];
  onSendMessage: (message: string) => Promise<void>;
  currentUserId: string;
  isAILoading?: boolean;
  disabled?: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  participants,
  onSendMessage,
  currentUserId,
  isAILoading = false,
  disabled = false,
}) => {
  const [newMessage, setNewMessage] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isAILoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim() && !disabled) {
      try {
        await onSendMessage(newMessage.trim());
        setNewMessage('');
      } catch {
        // Keep the draft visible when the server rejects the send.
      }
    }
  };

  const getParticipantColor = (participantId: string) => {
    if (participantId === 'ai-assistant') {
      return 'hsl(280 70% 60%)'; // Purple for AI
    }
    const participant = participants.find((p) => p.id === participantId);
    return participant?.color || 'hsl(var(--muted-foreground))';
  };

  const isAIMessage = (participantId: string) => participantId === 'ai-assistant';

  return (
    <div className="flex flex-col h-full bg-card rounded-lg border border-border">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold">Chat</h3>
        <span className="text-xs text-muted-foreground">Type @AI for help</span>
      </div>

      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-3">
          {messages.length === 0 ? (
            <p className="text-muted-foreground text-sm text-center py-4">
              No messages yet. Type @AI to ask for help!
            </p>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex flex-col ${message.participantId === currentUserId ? 'items-end' : 'items-start'
                  }`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 ${message.participantId === currentUserId
                      ? 'bg-primary text-primary-foreground'
                      : isAIMessage(message.participantId)
                        ? 'bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30'
                        : 'bg-secondary'
                    }`}
                >
                  {message.participantId !== currentUserId && (
                    <span
                      className="text-xs font-medium block mb-1 flex items-center gap-1"
                      style={{ color: getParticipantColor(message.participantId) }}
                    >
                      {isAIMessage(message.participantId) && (
                        <Bot className="h-3 w-3" />
                      )}
                      {message.username}
                    </span>
                  )}
                  <p className="text-sm whitespace-pre-wrap">{message.message}</p>
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
          {isAILoading && (
            <div className="flex flex-col items-start">
              <div className="max-w-[85%] rounded-lg px-3 py-2 bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30">
                <span className="text-xs font-medium block mb-1 flex items-center gap-1 text-purple-400">
                  <Bot className="h-3 w-3" />
                  AI Assistant
                </span>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Thinking...
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmit} className="p-3 border-t border-border flex gap-2">
        <Input
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type @AI for help..."
          className="flex-1"
          disabled={disabled}
        />
        <Button type="submit" size="icon" disabled={!newMessage.trim() || isAILoading || disabled}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
};

export default ChatPanel;
