import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api, Session, ChatMessage, ExecutionResult, SupportedLanguage, Participant } from '@/lib/api';
import Header from '@/components/Header';
import CodeEditor from '@/components/CodeEditor';
import ChatPanel from '@/components/ChatPanel';
import ParticipantList from '@/components/ParticipantList';
import ProblemPanel from '@/components/ProblemPanel';
import OutputPanel from '@/components/OutputPanel';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, Copy, Check, Share2, Loader2, Hash, TestTube } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const SessionPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user, guestJoin } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [copied, setCopied] = useState(false);
  
  // Guest join state
  const [guestName, setGuestName] = useState('');
  const [joinPin, setJoinPin] = useState('');
  const [isJoining, setIsJoining] = useState(false);

  // Simulated collaborators
  const [mockParticipants, setMockParticipants] = useState<Participant[]>([]);

  useEffect(() => {
    if (sessionId && user) {
      loadSession();
    }
  }, [sessionId, user]);

  // Simulate other participants typing
  useEffect(() => {
    if (!session) return;

    const interval = setInterval(() => {
      setMockParticipants((prev) => {
        if (prev.length === 0) return prev;
        
        const randomIndex = Math.floor(Math.random() * prev.length);
        const updated = [...prev];
        updated[randomIndex] = {
          ...updated[randomIndex],
          isTyping: Math.random() > 0.7,
          cursorPosition: {
            line: Math.floor(Math.random() * 15) + 1,
            column: Math.floor(Math.random() * 40) + 1,
          },
        };
        return updated;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [session]);

  // Add mock participants after joining
  useEffect(() => {
    if (session && user) {
      const mockUsers: Participant[] = [
        {
          id: 'mock-1',
          username: 'alex_dev',
          role: 'participant',
          color: 'hsl(265 70% 60%)',
          joinedAt: new Date(),
          cursorPosition: { line: 5, column: 10 },
        },
        {
          id: 'mock-2',
          username: 'sarah_codes',
          role: 'spectator',
          color: 'hsl(38 92% 50%)',
          joinedAt: new Date(),
        },
      ];
      
      setTimeout(() => {
        setMockParticipants(mockUsers);
        toast({
          title: 'alex_dev joined',
          description: 'A participant has joined the session',
        });
      }, 3000);
    }
  }, [session, user]);

  const loadSession = async () => {
    try {
      const sessionData = await api.sessions.get(sessionId!);
      if (!sessionData) {
        toast({
          title: 'Session not found',
          description: 'This session may have ended',
          variant: 'destructive',
        });
        navigate('/lobby');
        return;
      }
      setSession(sessionData);
      
      const messages = await api.chat.getMessages(sessionId!);
      setChatMessages(messages);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load session',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestJoin = async () => {
    if (!guestName.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter your name',
        variant: 'destructive',
      });
      return;
    }

    setIsJoining(true);
    try {
      await guestJoin(guestName);
      
      if (joinPin) {
        const sessionData = await api.sessions.joinByPin(joinPin);
        setSession(sessionData);
      }
      
      await loadSession();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to join session',
        variant: 'destructive',
      });
    } finally {
      setIsJoining(false);
    }
  };

  const handleCodeChange = useCallback(async (code: string) => {
    if (session) {
      setSession({ ...session, code });
      await api.sessions.updateCode(session.id, code);
    }
  }, [session]);

  const handleLanguageChange = async (language: SupportedLanguage) => {
    if (session) {
      await api.sessions.updateLanguage(session.id, language);
      setSession({ ...session, language, code: api.utils.getCodeTemplate(language) });
    }
  };

  const handleRunCode = async () => {
    if (!session) return;
    setIsRunning(true);
    setExecutionResult(null);

    try {
      const result = await api.execution.run(session.code, session.language);
      setExecutionResult(result);
    } catch (error: any) {
      toast({
        title: 'Execution failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunTests = async () => {
    if (!session || !session.problem) return;
    setIsRunning(true);
    setExecutionResult(null);

    try {
      const result = await api.execution.runTests(session.code, session.language, session.problem);
      setExecutionResult(result);
    } catch (error: any) {
      toast({
        title: 'Test execution failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!session) return;
    try {
      const chatMessage = await api.chat.send(session.id, message);
      setChatMessages((prev) => [...prev, chatMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const copyShareInfo = () => {
    if (!session) return;
    const link = api.utils.generateShareableLink(session.id);
    navigator.clipboard.writeText(`Join my CodioLive session:\n${link}\nPIN: ${session.pin}`);
    setCopied(true);
    toast({
      title: 'Copied!',
      description: 'Share link and PIN copied to clipboard',
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const languages = api.utils.getSupportedLanguages();
  const allParticipants = session 
    ? [...session.participants, ...mockParticipants]
    : [];

  // Guest join screen
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-primary/5 blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-accent/5 blur-3xl" />
        </div>

        <Card className="w-full max-w-md relative animate-slide-up">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Join Session</CardTitle>
            <CardDescription>
              Enter your name to join as a guest
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="guestName">Your Name</Label>
              <Input
                id="guestName"
                placeholder="John Doe"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pin">Session PIN (optional)</Label>
              <Input
                id="pin"
                placeholder="123456"
                value={joinPin}
                onChange={(e) => setJoinPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="text-center text-xl tracking-widest font-mono"
              />
            </div>
            <Button
              onClick={handleGuestJoin}
              variant="hero"
              className="w-full"
              disabled={isJoining}
            >
              {isJoining ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Joining...
                </>
              ) : (
                'Join as Guest'
              )}
            </Button>
            <div className="text-center text-sm">
              <span className="text-muted-foreground">Have an account? </span>
              <Button variant="link" className="p-0" onClick={() => navigate('/login')}>
                Sign in
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading session...</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 pt-24">
          <Card className="max-w-md mx-auto text-center">
            <CardHeader>
              <CardTitle>Session Not Found</CardTitle>
              <CardDescription>
                This session may have ended or doesn't exist
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => navigate('/lobby')}>Back to Lobby</Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/lobby')}>
            ← Lobby
          </Button>
          <div className="hidden md:block">
            <h1 className="font-semibold">{session.title}</h1>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Hash className="h-3 w-3" />
              <span className="font-mono">{session.pin}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Select value={session.language} onValueChange={handleLanguageChange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  {lang.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" onClick={copyShareInfo}>
            {copied ? (
              <Check className="h-4 w-4 mr-2" />
            ) : (
              <Share2 className="h-4 w-4 mr-2" />
            )}
            Share
          </Button>

          <Button onClick={handleRunCode} disabled={isRunning} size="sm">
            {isRunning ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Run
          </Button>

          {session.problem && (
            <Button onClick={handleRunTests} disabled={isRunning} variant="secondary" size="sm">
              <TestTube className="h-4 w-4 mr-2" />
              Test
            </Button>
          )}
        </div>
      </header>

      <div className="flex-1 min-h-0">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Left Panel - Problem */}
          <ResizablePanel defaultSize={25} minSize={20} maxSize={40}>
            <div className="h-full p-2">
              {session.problem ? (
                <ProblemPanel problem={session.problem} />
              ) : (
                <div className="h-full bg-card rounded-lg border border-border flex items-center justify-center">
                  <p className="text-muted-foreground">No problem set</p>
                </div>
              )}
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle />

          {/* Center Panel - Editor */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <ResizablePanelGroup direction="vertical" className="h-full">
              <ResizablePanel defaultSize={65} minSize={40}>
                <div className="h-full p-2">
                  <CodeEditor
                    code={session.code}
                    language={session.language}
                    onChange={handleCodeChange}
                    participants={allParticipants}
                    currentUserId={user.id}
                  />
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle />

              <ResizablePanel defaultSize={35} minSize={20}>
                <div className="h-full p-2">
                  <OutputPanel result={executionResult} isRunning={isRunning} />
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </ResizablePanel>

          <ResizableHandle withHandle />

          {/* Right Panel - Participants & Chat */}
          <ResizablePanel defaultSize={25} minSize={20} maxSize={35}>
            <div className="h-full p-2">
              <Tabs defaultValue="participants" className="h-full flex flex-col">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="participants">Participants</TabsTrigger>
                  <TabsTrigger value="chat">Chat</TabsTrigger>
                </TabsList>
                <TabsContent value="participants" className="flex-1 mt-2 min-h-0">
                  <ParticipantList
                    participants={allParticipants}
                    currentUserId={user.id}
                  />
                </TabsContent>
                <TabsContent value="chat" className="flex-1 mt-2 min-h-0">
                  <ChatPanel
                    messages={chatMessages}
                    participants={allParticipants}
                    onSendMessage={handleSendMessage}
                    currentUserId={user.id}
                  />
                </TabsContent>
              </Tabs>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  );
};

export default SessionPage;
