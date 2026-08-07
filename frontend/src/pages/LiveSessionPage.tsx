import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Clock3,
  Code2,
  Eye,
  Loader2,
  Lock,
  MessageSquare,
  Radio,
  Users,
} from 'lucide-react';
import { api, type ChatMessage, type Session } from '@/lib/api';
import CodeEditor from '@/components/CodeEditor';
import OutputPanel from '@/components/OutputPanel';
import ParticipantList from '@/components/ParticipantList';
import ProblemPanel from '@/components/ProblemPanel';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  demoExecutionResult,
  getDemoLiveMessages,
  getDemoLiveSession,
} from '@/data/liveSessions';

const viewerCounts: Record<string, number> = {
  'live-1': 24,
  'live-2': 17,
  'live-3': 31,
};

const formatElapsed = (startedAt: Date, now: number) => {
  const totalMinutes = Math.max(0, Math.floor((now - startedAt.getTime()) / 60_000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
};

const LiveSessionPage: React.FC = () => {
  const { sessionId = '' } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    let isCurrent = true;

    const loadSession = async () => {
      const demoSession = getDemoLiveSession(sessionId);
      const liveSession = demoSession ?? await api.spectator.watch(sessionId);

      if (!isCurrent) return;
      setSession(liveSession);
      setMessages(getDemoLiveMessages(sessionId));
      setIsLoading(false);
    };

    loadSession();
    return () => {
      isCurrent = false;
    };
  }, [sessionId]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const languageLabel = useMemo(
    () => api.utils.getSupportedLanguages().find((language) => language.value === session?.language)?.label,
    [session?.language],
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-9 w-9 animate-spin text-primary mx-auto mb-3" />
          <p className="text-muted-foreground">Joining live view…</p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="max-w-md text-center">
          <Radio className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
          <h1 className="text-2xl font-semibold mb-2">This session is no longer live</h1>
          <p className="text-muted-foreground mb-6">The interview may have ended or the viewing link is invalid.</p>
          <Button onClick={() => navigate('/spectate')}>Browse live sessions</Button>
        </div>
      </div>
    );
  }

  const viewers = viewerCounts[session.id] ?? Math.max(1, session.participants.length * 2);

  return (
    <div className="min-h-screen xl:h-screen flex flex-col bg-background">
      <header className="border-b border-border bg-card/95 px-3 sm:px-5 py-3 shrink-0">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/spectate')}
              aria-label="Back to live sessions"
              className="shrink-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-destructive">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-destructive opacity-70" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-destructive" />
                  </span>
                  Live
                </span>
                <span className="text-border">/</span>
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock3 className="h-3 w-3" />
                  {formatElapsed(session.createdAt, now)} elapsed
                </span>
              </div>
              <h1 className="truncate text-base sm:text-lg font-semibold">{session.title}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3 ml-12 sm:ml-0">
            <Badge variant="secondary" className="hidden sm:inline-flex gap-1.5 font-mono font-normal">
              <Code2 className="h-3 w-3" />
              {languageLabel ?? session.language}
            </Badge>
            <span className="hidden md:flex items-center gap-1.5 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              {viewers} watching
            </span>
            <Badge className="gap-1.5 bg-primary/10 text-primary hover:bg-primary/10">
              <Eye className="h-3.5 w-3.5" />
              Watching as guest
            </Badge>
          </div>
        </div>
      </header>

      <div className="flex items-center justify-center gap-2 border-b border-primary/15 bg-primary/[0.06] px-4 py-2 text-xs text-primary">
        <Lock className="h-3.5 w-3.5" />
        <span><strong className="font-semibold">Spectator mode</strong> · This workspace is live and read-only.</span>
      </div>

      <main className="flex-1 min-h-0 p-2 sm:p-3 overflow-auto xl:overflow-hidden">
        <div className="grid min-h-full gap-3 xl:h-full xl:grid-cols-[minmax(250px,0.82fr)_minmax(460px,1.8fr)_minmax(280px,0.9fr)]">
          <section className="min-h-[420px] xl:min-h-0" aria-label="Interview problem">
            {session.problem ? (
              <ProblemPanel problem={session.problem} />
            ) : (
              <div className="h-full min-h-[240px] rounded-lg border border-border bg-card flex items-center justify-center p-6 text-center">
                <div>
                  <Code2 className="h-7 w-7 text-muted-foreground mx-auto mb-3" />
                  <p className="font-medium">Open coding discussion</p>
                  <p className="text-sm text-muted-foreground mt-1">No challenge brief is attached.</p>
                </div>
              </div>
            )}
          </section>

          <section className="grid min-h-[620px] grid-rows-[minmax(390px,1fr)_190px] gap-3 xl:min-h-0" aria-label="Live coding workspace">
            <div className="min-h-0 flex flex-col rounded-lg border border-border bg-card overflow-hidden">
              <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <Code2 className="h-4 w-4 text-primary" />
                  <h2 className="text-sm font-semibold">Live code</h2>
                </div>
                <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Lock className="h-3 w-3" />
                  Read only
                </span>
              </div>
              <div className="flex-1 min-h-0 p-1.5">
                <CodeEditor
                  code={session.code}
                  language={session.language}
                  onChange={() => undefined}
                  participants={session.participants}
                  currentUserId="guest-spectator"
                  readOnly
                />
              </div>
            </div>
            <OutputPanel
              result={session.id === 'live-1' ? demoExecutionResult : null}
              isRunning={false}
            />
          </section>

          <aside className="grid min-h-[560px] grid-rows-[auto_minmax(320px,1fr)] gap-3 xl:min-h-0" aria-label="Session activity">
            <ParticipantList participants={session.participants} currentUserId="guest-spectator" />
            <div className="min-h-0 flex flex-col rounded-lg border border-border bg-card overflow-hidden">
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <h2 className="flex items-center gap-2 font-semibold">
                  <MessageSquare className="h-4 w-4" />
                  Conversation
                </h2>
                <Badge variant="outline" className="font-normal">Live transcript</Badge>
              </div>
              <ScrollArea className="flex-1 min-h-0 p-4">
                {messages.length > 0 ? (
                  <div className="space-y-4">
                    {messages.map((message) => {
                      const participant = session.participants.find((item) => item.id === message.participantId);
                      return (
                        <div key={message.id} className="flex gap-2.5">
                          <div
                            className="h-7 w-7 shrink-0 rounded-full flex items-center justify-center text-[11px] font-semibold"
                            style={{
                              backgroundColor: `${participant?.color ?? 'hsl(var(--primary))'}33`,
                              color: participant?.color ?? 'hsl(var(--primary))',
                            }}
                          >
                            {message.username.charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-baseline gap-x-2">
                              <span className="text-xs font-semibold">{message.username}</span>
                              <time className="text-[10px] text-muted-foreground">
                                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </time>
                            </div>
                            <p className="mt-1 text-sm leading-relaxed text-foreground/90">{message.message}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="h-full min-h-[220px] flex items-center justify-center text-center">
                    <div>
                      <MessageSquare className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
                      <p className="text-sm text-muted-foreground">No transcript messages yet.</p>
                    </div>
                  </div>
                )}
              </ScrollArea>
              <div className="border-t border-border px-4 py-2 text-center text-xs text-muted-foreground">
                Guests can view the conversation but cannot send messages.
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default LiveSessionPage;
