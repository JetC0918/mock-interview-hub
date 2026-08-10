import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { Play, Copy, Check, Share2, Loader2, Hash, TestTube, Radio } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';

const getErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback;

const getErrorStatus = (error: unknown) => {
  if (typeof error !== 'object' || error === null) return undefined;
  const status = (error as Record<string, unknown>).status;
  return typeof status === 'number' ? status : undefined;
};

const SessionPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user, isLoading: authLoading, guestJoinSession } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isAILoading, setIsAILoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Guest join state
  const [guestName, setGuestName] = useState('');
  const [joinPin, setJoinPin] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [canJoinExisting, setCanJoinExisting] = useState(false);
  const codeTimerRef = useRef<number | null>(null);
  const codeQueueRef = useRef<Promise<void>>(Promise.resolve());
  const latestCodeRef = useRef('');
  const codeDirtyRef = useRef(false);
  const sessionRef = useRef<Session | null>(null);
  const revisionRef = useRef(0);
  const mountedRef = useRef(true);
  const aiRequestIdsRef = useRef(new Map<string, string>());

  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  useEffect(() => () => {
    mountedRef.current = false;
    if (codeTimerRef.current !== null) {
      window.clearTimeout(codeTimerRef.current);
    }
    const current = sessionRef.current;
    if (current && current.status !== 'ended' && codeDirtyRef.current) {
      const codeToFlush = latestCodeRef.current;
      // SPA navigation does not fire beforeunload. Queue the latest dirty
      // document so leaving the page cannot silently discard the edit.
      void codeQueueRef.current.then(async () => {
        try {
          const nextRevision = await api.sessions.updateCode(current.id, codeToFlush, revisionRef.current);
          revisionRef.current = nextRevision;
          if (latestCodeRef.current === codeToFlush) codeDirtyRef.current = false;
        } catch {
          // The beforeunload warning already surfaced the unsaved state; a
          // failed background flush must not create an unhandled rejection.
        }
      });
    }
  }, []);

  useEffect(() => {
    const warnOnUnsaved = (event: BeforeUnloadEvent) => {
      if (!codeDirtyRef.current) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warnOnUnsaved);
    return () => window.removeEventListener('beforeunload', warnOnUnsaved);
  }, []);

  const loadSession = useCallback(async () => {
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
      latestCodeRef.current = sessionData.code;
      codeDirtyRef.current = false;
      revisionRef.current = sessionData.codeRevision;
      setSession(sessionData);

      const messages = await api.chat.getMessages(sessionId!);
      setChatMessages(messages);
    } catch (error: unknown) {
      if (getErrorStatus(error) === 403) {
        setCanJoinExisting(true);
        return;
      }
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to load session'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [navigate, sessionId, toast]);

  useEffect(() => {
    if (sessionId && user) void loadSession();
  }, [loadSession, sessionId, user]);

  // Polling refreshes both the session and the bounded chat page. Local code
  // remains authoritative until its queued write has completed.
  useEffect(() => {
    const interval = setInterval(async () => {
      if (!sessionRef.current) return;
      try {
        const sessionData = await api.sessions.get(sessionId!);
        if (sessionData) {
          revisionRef.current = Math.max(revisionRef.current, sessionData.codeRevision);
          setSession((current) => {
            if (!current) return sessionData;
            if (codeDirtyRef.current) {
              return { ...sessionData, code: latestCodeRef.current };
            }
            latestCodeRef.current = sessionData.code;
            return sessionData;
          });
          const messages = await api.chat.getMessages(sessionId!);
          setChatMessages((current) => {
            const byId = new Map(current.map((message) => [message.id, message]));
            messages.forEach((message) => byId.set(message.id, message));
            return Array.from(byId.values()).sort(
              (left, right) => left.timestamp.getTime() - right.timestamp.getTime(),
            );
          });
        }
      } catch (error) {
        if (getErrorStatus(error) !== 404) {
          toast({ title: 'Session refresh failed', description: 'The latest session state could not be loaded.', variant: 'destructive' });
        }
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId, toast]);

  const handleGuestJoin = async () => {
    if (!user && !guestName.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter your name',
        variant: 'destructive',
      });
      return;
    }

    setIsJoining(true);
    try {
      if (!joinPin.trim()) {
        toast({ title: 'Join secret required', description: 'Paste the session join secret shared by the host.', variant: 'destructive' });
        return;
      }
      // Authenticated non-members use the normal membership admission path;
      // only unauthenticated viewers receive a durable guest identity.
      const joined = user
        ? await api.sessions.join(sessionId!, joinPin.trim())
        : await guestJoinSession(sessionId!, guestName.trim(), joinPin.trim());
      setCanJoinExisting(false);
      setSession(joined);
      sessionRef.current = joined;
      latestCodeRef.current = joined.code;
      revisionRef.current = joined.codeRevision;
      codeDirtyRef.current = false;
      setChatMessages(await api.chat.getMessages(sessionId!));
      setIsLoading(false);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to join session'),
        variant: 'destructive',
      });
    } finally {
      setIsJoining(false);
    }
  };

  const handleCodeChange = useCallback((code: string) => {
    const current = sessionRef.current;
    if (!current || current.status === 'ended') return;
    latestCodeRef.current = code;
    codeDirtyRef.current = true;
    setSession((previous) => previous ? { ...previous, code } : previous);

    if (codeTimerRef.current !== null) {
      window.clearTimeout(codeTimerRef.current);
    }
    codeTimerRef.current = window.setTimeout(() => {
      const codeToSend = latestCodeRef.current;
      codeQueueRef.current = codeQueueRef.current.then(async () => {
        try {
          const nextRevision = await api.sessions.updateCode(current.id, codeToSend, revisionRef.current);
          revisionRef.current = nextRevision;
          setSession((previous) => previous ? { ...previous, codeRevision: nextRevision } : previous);
          if (latestCodeRef.current === codeToSend) codeDirtyRef.current = false;
        } catch (error: unknown) {
          if (mountedRef.current) {
            const status = getErrorStatus(error);
            toast({ title: status === 409 ? 'Code changed remotely' : 'Code save failed', description: status === 409 ? 'Your unsaved edit is preserved; reload or merge the newer revision before retrying.' : getErrorMessage(error, 'Your latest code was not saved.'), variant: 'destructive' });
          }
        }
      });
    }, 250);
  }, [toast]);

  const handleLanguageChange = async (language: SupportedLanguage) => {
    const current = sessionRef.current;
    if (!current || current.status === 'ended') return;
    try {
      const nextRevision = await api.sessions.updateLanguage(current.id, language, revisionRef.current);
      revisionRef.current = nextRevision;
      setSession((previous) => previous ? { ...previous, language, codeRevision: nextRevision } : previous);
    } catch (error: unknown) {
      toast({ title: 'Language update failed', description: getErrorMessage(error, 'The session language was not changed.'), variant: 'destructive' });
    }
  };

  const handleRunCode = async () => {
    if (!session) return;
    setIsRunning(true);
    setExecutionResult(null);

    try {
      const result = await api.execution.run(session.code, session.language);
      setExecutionResult(result);
    } catch (error: unknown) {
      toast({
        title: 'Execution failed',
        description: getErrorMessage(error, 'The code could not be executed.'),
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
      const result = await api.execution.test(session.code, session.language, session.problem);
      setExecutionResult(result);
    } catch (error: unknown) {
      toast({
        title: 'Test execution failed',
        description: getErrorMessage(error, 'The tests could not be executed.'),
        variant: 'destructive',
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!session) return;
    const trimmed = message.trim();
    // AI exchanges are atomic on the server: the endpoint persists both the
    // prompt and assistant reply. Never pre-send the prompt through /chat or
    // it will appear twice in the shared transcript.
    if (/^@ai(?:\s|$)/i.test(trimmed)) {
      await handleAIAssist(trimmed);
      const refreshed = await api.chat.getMessages(session.id);
      setChatMessages(refreshed);
      return;
    }
    try {
      const chatMessage = await api.chat.send(session.id, trimmed);
      setChatMessages((prev) => [...prev, chatMessage]);
    } catch (error: unknown) {
      toast({
        title: 'Message not sent',
        description: getErrorMessage(error, 'The message could not be sent.'),
        variant: 'destructive',
      });
      throw error;
    }
  };

  const handleAIAssist = async (message: string) => {
    if (!session) return;

    setIsAILoading(true);
    try {
      const aiResponse = await api.ai.getGuidance(
        session.id,
        message,
        session.problem,
        aiRequestIdsRef.current.get(message) || (() => {
          const id = crypto.randomUUID().replace(/-/g, '');
          aiRequestIdsRef.current.set(message, id);
          return id;
        })(),
      );
      setChatMessages((prev) => [...prev, aiResponse]);
    } catch (error: unknown) {
      toast({
        title: 'AI Assistant Error',
        description: getErrorMessage(error, 'Failed to get AI guidance'),
        variant: 'destructive',
      });
    } finally {
      setIsAILoading(false);
    }
  };

  const copyShareInfo = async () => {
    if (!session) return;
    const link = api.utils.generateShareableLink(session.id);
    try {
      await navigator.clipboard.writeText(`Join my CodioLive session:\n${link}\nJoin secret: ${session.pin}`);
      setCopied(true);
      toast({ title: 'Copied!', description: 'Share link and join secret copied to clipboard' });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: 'Copy failed', description: 'Copy the share link and secret manually.', variant: 'destructive' });
    }
  };

  const handleStartSession = async () => {
    if (!session || !user || session.status !== 'waiting' || session.hostId !== user.id) return;
    setIsStarting(true);
    try {
      await api.sessions.start(session.id);
      setSession((current) => current ? { ...current, status: 'active' } : current);
      toast({ title: 'Session started', description: 'The interview is now live for participants and spectators.' });
    } catch (error: unknown) {
      toast({ title: 'Unable to start session', description: getErrorMessage(error, 'The session could not be started.'), variant: 'destructive' });
    } finally {
      setIsStarting(false);
    }
  };

  const languages = api.utils.getSupportedLanguages();
  const allParticipants = session ? session.participants : [];
  const isEnded = session?.status === 'ended';

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
      </div>
    );
  }

  // Guest and authenticated non-member admission share the validated flow.
  if (!user || canJoinExisting) {
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
              {user ? 'Enter the session join secret to continue' : 'Enter your name and join secret to enter as a guest'}
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
              <Label htmlFor="pin">Session join secret</Label>
              <Input
                id="pin"
                placeholder="Paste the join secret"
                value={joinPin}
                onChange={(e) => setJoinPin(e.target.value.slice(0, 128))}
                maxLength={128}
                className="text-center text-lg tracking-wide font-mono"
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
      <header className="min-h-14 border-b border-border bg-card flex flex-wrap items-center justify-between gap-2 px-3 sm:px-4 shrink-0">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/lobby')}>
            ← Lobby
          </Button>
          <div className="hidden md:block">
            <h1 className="font-semibold">{session.title}</h1>
            <Badge variant={isEnded ? 'secondary' : 'default'} className="mt-1 text-[10px] uppercase tracking-wide">
              {isEnded ? 'Ended · read only' : session.status}
            </Badge>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Hash className="h-3 w-3" />
              <span className="font-mono">{session.pin}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 min-w-0">
          {session.status === 'waiting' && session.hostId === user.id && (
            <Button
              variant="secondary"
              size="sm"
              onClick={async () => {
                try {
                  await api.sessions.start(session.id);
                  setSession((current) => current ? { ...current, status: 'active' } : current);
                } catch (error) {
                  toast({ title: 'Could not start session', description: getErrorMessage(error, 'Try again.'), variant: 'destructive' });
                }
              }}
            >
              Start session
            </Button>
          )}
          <Select value={session.language} onValueChange={handleLanguageChange} disabled={isEnded}>
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

          <Button variant="outline" size="sm" onClick={copyShareInfo} disabled={isEnded}>
            {copied ? (
              <Check className="h-4 w-4 mr-2" />
            ) : (
              <Share2 className="h-4 w-4 mr-2" />
            )}
            Share
          </Button>

          {session.status === 'waiting' && session.hostId === user?.id && (
            <Button onClick={handleStartSession} disabled={isStarting} size="sm">
              {isStarting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Radio className="h-4 w-4 mr-2" />}
              Start interview
            </Button>
          )}

          <Button onClick={handleRunCode} disabled={isRunning || isEnded} size="sm">
            {isRunning ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Run
          </Button>

          {session.problem && (
            <Button onClick={handleRunTests} disabled={isRunning || isEnded} variant="secondary" size="sm">
              <TestTube className="h-4 w-4 mr-2" />
              Test
            </Button>
          )}
        </div>
      </header>

      <div className="flex-1 min-h-0">
        <ResizablePanelGroup direction="horizontal" className="h-full min-w-0 overflow-x-auto">
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
                    readOnly={isEnded}
                    onCursorChange={(position) => {
                      if (!isEnded) {
                        void api.sessions.updateCursor(session.id, position).catch(() => undefined);
                      }
                    }}
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
                    isAILoading={isAILoading}
                    disabled={isEnded}
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
