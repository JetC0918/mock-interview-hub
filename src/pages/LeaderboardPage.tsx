import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, LeaderboardEntry } from '@/lib/api';
import Header from '@/components/Header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy, Medal, Award, Clock, Target, TrendingUp, Loader2 } from 'lucide-react';

const LeaderboardPage: React.FC = () => {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const loadLeaderboard = async () => {
    try {
      const data = await api.leaderboard.get();
      setEntries(data);
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="h-6 w-6 text-warning" />;
      case 2:
        return <Medal className="h-6 w-6 text-muted-foreground" />;
      case 3:
        return <Award className="h-6 w-6 text-warning/70" />;
      default:
        return (
          <span className="h-6 w-6 flex items-center justify-center text-muted-foreground font-bold">
            {rank}
          </span>
        );
    }
  };

  const getRankStyles = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-warning/10 border-warning/30 shadow-lg';
      case 2:
        return 'bg-muted/50 border-muted-foreground/20';
      case 3:
        return 'bg-warning/5 border-warning/20';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 pt-24 pb-8">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold mb-3">
            <span className="text-gradient-primary">Leaderboard</span>
          </h1>
          <p className="text-muted-foreground max-w-md mx-auto">
            Top performers across all coding interview sessions
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-primary/20 flex items-center justify-center">
                  <Target className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Sessions</p>
                  <p className="text-2xl font-bold">
                    {entries.reduce((acc, e) => acc + e.sessionsCompleted, 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-accent/10 to-accent/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-accent/20 flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg Score</p>
                  <p className="text-2xl font-bold">
                    {entries.length > 0
                      ? (entries.reduce((acc, e) => acc + e.avgScore, 0) / entries.length).toFixed(1)
                      : 0}
                    %
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-success/10 to-success/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-success/20 flex items-center justify-center">
                  <Clock className="h-6 w-6 text-success" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Active Coders</p>
                  <p className="text-2xl font-bold">{entries.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-primary" />
                Rankings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {entries.map((entry) => (
                  <div
                    key={entry.userId}
                    className={`flex items-center gap-4 p-4 rounded-xl border transition-all hover:scale-[1.01] cursor-pointer ${getRankStyles(entry.rank)}`}
                  >
                    <div className="flex items-center justify-center w-10">
                      {getRankIcon(entry.rank)}
                    </div>
                    
                    <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center text-lg font-bold text-primary">
                      {entry.username.charAt(0).toUpperCase()}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{entry.username}</p>
                      <p className="text-sm text-muted-foreground">
                        {entry.sessionsCompleted} sessions completed
                      </p>
                    </div>
                    
                    <div className="hidden md:flex items-center gap-6">
                      <div className="text-center">
                        <p className="text-lg font-bold text-primary">{entry.avgScore}%</p>
                        <p className="text-xs text-muted-foreground">Avg Score</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold">{entry.totalTime}</p>
                        <p className="text-xs text-muted-foreground">Total Time</p>
                      </div>
                    </div>
                    
                    {entry.rank <= 3 && (
                      <Badge className={
                        entry.rank === 1 
                          ? 'bg-warning text-warning-foreground' 
                          : entry.rank === 2 
                            ? 'bg-muted text-muted-foreground' 
                            : 'bg-warning/50 text-warning-foreground'
                      }>
                        #{entry.rank}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
};

export default LeaderboardPage;
