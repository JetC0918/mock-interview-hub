import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Session } from '@/lib/api';
import Header from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Eye, Users, Code2, Clock, Play, Loader2 } from 'lucide-react';

const SpectatePage: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const languages = api.utils.getSupportedLanguages();

  useEffect(() => {
    loadSessions();
    
    // Refresh periodically
    const interval = setInterval(loadSessions, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadSessions = async () => {
    try {
      const activeSessions = await api.spectator.getSessions();
      // Add mock active sessions for demo
      const mockSessions: Session[] = [
        {
          id: 'live-1',
          pin: '789456',
          hostId: 'host-1',
          title: 'Senior Frontend Interview',
          description: '',
          language: 'typescript',
          participants: [
            { id: 'p1', username: 'interviewer_jane', role: 'host', color: 'hsl(174 72% 50%)', joinedAt: new Date() },
            { id: 'p2', username: 'candidate_mike', role: 'participant', color: 'hsl(265 70% 60%)', joinedAt: new Date() },
          ],
          code: '',
          status: 'active',
          createdAt: new Date(Date.now() - 1800000),
        },
        {
          id: 'live-2',
          pin: '321654',
          hostId: 'host-2',
          title: 'Algorithm Challenge',
          description: '',
          language: 'python',
          participants: [
            { id: 'p3', username: 'coach_sara', role: 'host', color: 'hsl(174 72% 50%)', joinedAt: new Date() },
            { id: 'p4', username: 'student_alex', role: 'participant', color: 'hsl(38 92% 50%)', joinedAt: new Date() },
            { id: 'p5', username: 'student_emma', role: 'participant', color: 'hsl(330 80% 60%)', joinedAt: new Date() },
          ],
          code: '',
          status: 'active',
          createdAt: new Date(Date.now() - 2700000),
        },
        {
          id: 'live-3',
          pin: '654987',
          hostId: 'host-3',
          title: 'Bootcamp Live Session',
          description: '',
          language: 'javascript',
          participants: [
            { id: 'p6', username: 'instructor', role: 'host', color: 'hsl(174 72% 50%)', joinedAt: new Date() },
            { id: 'p7', username: 'student_1', role: 'participant', color: 'hsl(265 70% 60%)', joinedAt: new Date() },
            { id: 'p8', username: 'student_2', role: 'participant', color: 'hsl(38 92% 50%)', joinedAt: new Date() },
            { id: 'p9', username: 'student_3', role: 'participant', color: 'hsl(330 80% 60%)', joinedAt: new Date() },
          ],
          code: '',
          status: 'active',
          createdAt: new Date(Date.now() - 900000),
        },
      ];
      setSessions([...activeSessions, ...mockSessions]);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getTimeSince = (date: Date) => {
    const minutes = Math.floor((Date.now() - new Date(date).getTime()) / 60000);
    if (minutes < 60) return `${minutes}m`;
    return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 pt-24 pb-8">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold mb-3">
            <span className="text-gradient-primary">Spectate Live Sessions</span>
          </h1>
          <p className="text-muted-foreground max-w-md mx-auto">
            Watch ongoing coding interviews and learn from the best
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : sessions.length === 0 ? (
          <Card className="text-center py-12 max-w-md mx-auto">
            <CardContent>
              <div className="flex justify-center mb-4">
                <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                  <Eye className="h-8 w-8 text-muted-foreground" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">No live sessions</h3>
              <p className="text-muted-foreground mb-4">
                Check back later for active sessions to watch
              </p>
              <Button variant="outline" onClick={() => navigate('/lobby')}>
                Create Your Own Session
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <Card key={session.id} className="group relative overflow-hidden hover:border-primary/50 transition-all">
                {/* Live indicator */}
                <div className="absolute top-4 right-4 flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-destructive" />
                  </span>
                  <span className="text-xs font-medium text-destructive">LIVE</span>
                </div>

                <CardHeader className="pb-3">
                  <CardTitle className="text-lg pr-16">{session.title}</CardTitle>
                  <CardDescription className="flex items-center gap-2 flex-wrap">
                    <Badge variant="secondary" className="font-mono">
                      <Code2 className="h-3 w-3 mr-1" />
                      {languages.find(l => l.value === session.language)?.label}
                    </Badge>
                    <Badge variant="outline">
                      <Clock className="h-3 w-3 mr-1" />
                      {getTimeSince(session.createdAt)}
                    </Badge>
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <div className="mb-4">
                    <p className="text-sm text-muted-foreground mb-2">Participants</p>
                    <div className="flex items-center -space-x-2">
                      {session.participants.slice(0, 4).map((participant, index) => (
                        <div
                          key={participant.id}
                          className="h-8 w-8 rounded-full border-2 border-card flex items-center justify-center text-xs font-medium"
                          style={{ 
                            backgroundColor: participant.color + '33', 
                            color: participant.color,
                            zIndex: 10 - index,
                          }}
                          title={participant.username}
                        >
                          {participant.username.charAt(0).toUpperCase()}
                        </div>
                      ))}
                      {session.participants.length > 4 && (
                        <div className="h-8 w-8 rounded-full border-2 border-card bg-secondary flex items-center justify-center text-xs font-medium">
                          +{session.participants.length - 4}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Users className="h-4 w-4" />
                      <span>{session.participants.length}</span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Eye className="h-4 w-4" />
                      <span>{Math.floor(Math.random() * 50) + 5} watching</span>
                    </div>
                  </div>

                  <Button
                    className="w-full mt-4 opacity-0 group-hover:opacity-100 transition-opacity"
                    variant="hero"
                    onClick={() => navigate(`/session/${session.id}`)}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Watch Session
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default SpectatePage;
