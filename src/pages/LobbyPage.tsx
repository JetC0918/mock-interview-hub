import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { api, Session, SupportedLanguage } from '@/lib/api';
import Header from '@/components/Header';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Plus, Link as LinkIcon, Hash, Users, Clock, Copy, Check, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const LobbyPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [joinDialogOpen, setJoinDialogOpen] = useState(false);
  
  const [newSessionTitle, setNewSessionTitle] = useState('');
  const [newSessionLanguage, setNewSessionLanguage] = useState<SupportedLanguage>('javascript');
  const [joinPin, setJoinPin] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const activeSessions = await api.sessions.getActive();
      setSessions(activeSessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!newSessionTitle.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a session title',
        variant: 'destructive',
      });
      return;
    }

    setIsCreating(true);
    try {
      const session = await api.sessions.create(newSessionTitle, newSessionLanguage);
      toast({
        title: 'Session created!',
        description: `PIN: ${session.pin}`,
      });
      setCreateDialogOpen(false);
      navigate(`/session/${session.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create session',
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinSession = async () => {
    if (!joinPin.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a session PIN',
        variant: 'destructive',
      });
      return;
    }

    try {
      const session = await api.sessions.joinByPin(joinPin);
      toast({
        title: 'Joined session!',
        description: session.title,
      });
      setJoinDialogOpen(false);
      navigate(`/session/${session.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to join session',
        variant: 'destructive',
      });
    }
  };

  const copyShareLink = (session: Session) => {
    const link = api.utils.generateShareableLink(session.id);
    navigator.clipboard.writeText(`${link} | PIN: ${session.pin}`);
    setCopiedId(session.id);
    toast({
      title: 'Copied!',
      description: 'Session link and PIN copied to clipboard',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const languages = api.utils.getSupportedLanguages();

  if (!user) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 pt-24">
          <Card className="max-w-md mx-auto text-center">
            <CardHeader>
              <CardTitle>Sign in to continue</CardTitle>
              <CardDescription>
                Create an account to host sessions
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-3 justify-center">
              <Button onClick={() => navigate('/login')}>Sign In</Button>
              <Button variant="outline" onClick={() => navigate('/signup')}>Sign Up</Button>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 pt-24 pb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">Session Lobby</h1>
            <p className="text-muted-foreground mt-1">Create or join a coding interview session</p>
          </div>
          <div className="flex gap-3">
            <Dialog open={joinDialogOpen} onOpenChange={setJoinDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Hash className="mr-2 h-4 w-4" />
                  Join with PIN
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Join a Session</DialogTitle>
                  <DialogDescription>
                    Enter the 6-digit PIN shared by the host
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="pin">Session PIN</Label>
                    <Input
                      id="pin"
                      type="text"
                      placeholder="123456"
                      value={joinPin}
                      onChange={(e) => setJoinPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      maxLength={6}
                      className="text-center text-2xl tracking-widest font-mono"
                    />
                  </div>
                  <Button onClick={handleJoinSession} className="w-full" variant="hero">
                    Join Session
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="hero">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Session
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Session</DialogTitle>
                  <DialogDescription>
                    Set up a new coding interview session
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Session Title</Label>
                    <Input
                      id="title"
                      placeholder="Technical Interview - Frontend"
                      value={newSessionTitle}
                      onChange={(e) => setNewSessionTitle(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Language</Label>
                    <Select value={newSessionLanguage} onValueChange={(v) => setNewSessionLanguage(v as SupportedLanguage)}>
                      <SelectTrigger>
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
                  </div>
                  <Button onClick={handleCreateSession} className="w-full" variant="hero" disabled={isCreating}>
                    {isCreating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      'Create Session'
                    )}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : sessions.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <div className="flex justify-center mb-4">
                <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                  <Users className="h-8 w-8 text-muted-foreground" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">No active sessions</h3>
              <p className="text-muted-foreground mb-4">Create a session to get started</p>
              <Button variant="hero" onClick={() => setCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Session
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <Card key={session.id} className="group hover:border-primary/50 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{session.title}</CardTitle>
                      <CardDescription className="flex items-center gap-2 mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-secondary text-xs font-medium">
                          {languages.find(l => l.value === session.language)?.label}
                        </span>
                      </CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyShareLink(session)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      {copiedId === session.id ? (
                        <Check className="h-4 w-4 text-success" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                    <div className="flex items-center gap-1">
                      <Hash className="h-4 w-4" />
                      <span className="font-mono">{session.pin}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      <span>{session.participants.length}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(session.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      className="flex-1"
                      onClick={() => navigate(`/session/${session.id}`)}
                    >
                      <LinkIcon className="mr-2 h-4 w-4" />
                      Join
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default LobbyPage;
