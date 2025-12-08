import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import Header from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Code2, 
  Users, 
  Zap, 
  Shield, 
  ArrowRight, 
  Play,
  Hash,
  Clock,
  Globe
} from 'lucide-react';

const Index: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const features = [
    {
      icon: <Users className="h-6 w-6" />,
      title: 'Real-time Collaboration',
      description: 'Multiple users edit code together with instant updates and visible cursors.',
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: 'In-Browser Execution',
      description: 'Run JavaScript and Python directly in the browser. No setup needed.',
    },
    {
      icon: <Hash className="h-6 w-6" />,
      title: 'Share with PIN',
      description: 'Generate a secure link and PIN. Candidates join instantly.',
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: 'Sandboxed & Safe',
      description: 'Code runs in isolated sandboxes. Your system stays protected.',
    },
    {
      icon: <Clock className="h-6 w-6" />,
      title: 'Session History',
      description: 'Logged-in users can save and review past interview sessions.',
    },
    {
      icon: <Globe className="h-6 w-6" />,
      title: 'Multiple Languages',
      description: 'Support for JavaScript, TypeScript, Python, Java, C++, and Go.',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-1/4 w-[500px] h-[500px] rounded-full bg-primary/10 blur-[120px]" />
          <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full bg-accent/10 blur-[100px]" />
        </div>

        <div className="container mx-auto relative">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6 animate-fade-in">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
              </span>
              Now in Early Access
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight animate-slide-up">
              Coding interviews
              <br />
              <span className="text-gradient-primary">that just work</span>
            </h1>

            <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '100ms' }}>
              Run real-time collaborative coding sessions in your browser. 
              No installs, no accounts for guests — just share a link and start coding.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
              <Button 
                variant="hero" 
                size="xl"
                onClick={() => navigate(user ? '/lobby' : '/signup')}
              >
                {user ? 'Go to Sessions' : 'Start for Free'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button 
                variant="outline" 
                size="xl"
                onClick={() => navigate('/spectate')}
              >
                <Play className="mr-2 h-5 w-5" />
                Watch Live Sessions
              </Button>
            </div>
          </div>

          {/* Mock editor preview */}
          <div className="mt-20 max-w-5xl mx-auto animate-slide-up" style={{ animationDelay: '300ms' }}>
            <div className="relative rounded-xl border border-border bg-card shadow-elevated overflow-hidden">
              {/* Window header */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-secondary/30">
                <div className="flex gap-1.5">
                  <div className="h-3 w-3 rounded-full bg-destructive/80" />
                  <div className="h-3 w-3 rounded-full bg-warning/80" />
                  <div className="h-3 w-3 rounded-full bg-success/80" />
                </div>
                <div className="flex-1 text-center">
                  <span className="text-sm text-muted-foreground">CodioLive Session</span>
                </div>
              </div>

              {/* Mock editor content */}
              <div className="p-6 font-mono text-sm bg-editor-bg">
                <div className="flex gap-6">
                  {/* Line numbers */}
                  <div className="text-muted-foreground/50 select-none">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                      <div key={n}>{n}</div>
                    ))}
                  </div>
                  
                  {/* Code */}
                  <div className="flex-1">
                    <div><span className="text-purple-400">function</span> <span className="text-yellow-300">twoSum</span>(<span className="text-orange-300">nums</span>, <span className="text-orange-300">target</span>) {'{'}</div>
                    <div>  <span className="text-purple-400">const</span> map = <span className="text-purple-400">new</span> <span className="text-cyan-300">Map</span>();</div>
                    <div>  <span className="text-purple-400">for</span> (<span className="text-purple-400">let</span> i = <span className="text-green-300">0</span>; i {'<'} nums.length; i++) {'{'}</div>
                    <div>    <span className="text-purple-400">const</span> complement = target - nums[i];</div>
                    <div>    <span className="text-purple-400">if</span> (map.<span className="text-yellow-300">has</span>(complement)) {'{'}</div>
                    <div>      <span className="text-purple-400">return</span> [map.<span className="text-yellow-300">get</span>(complement), i];<span className="animate-pulse text-primary">|</span></div>
                    <div>    {'}'}</div>
                    <div>    map.<span className="text-yellow-300">set</span>(nums[i], i);</div>
                  </div>
                </div>

                {/* Mock cursors */}
                <div className="absolute top-[180px] left-[400px] flex items-center gap-1 animate-pulse">
                  <div className="h-5 w-0.5 bg-accent" />
                  <span className="text-xs bg-accent text-accent-foreground px-1.5 py-0.5 rounded">alex_dev</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-secondary/20">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything you need for
              <span className="text-gradient-primary"> technical interviews</span>
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Built for speed and simplicity. Get candidates coding in seconds, not minutes.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card 
                key={index} 
                className="group hover:border-primary/30 transition-all hover:shadow-lg animate-fade-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <CardContent className="pt-6">
                  <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <div className="max-w-4xl mx-auto relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary/20 via-primary/10 to-accent/20 p-12 text-center border border-primary/20">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-accent/5" />
            
            <div className="relative">
              <div className="flex justify-center mb-6">
                <div className="h-16 w-16 rounded-2xl bg-gradient-primary shadow-glow flex items-center justify-center">
                  <Code2 className="h-8 w-8 text-primary-foreground" />
                </div>
              </div>
              
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to streamline your interviews?
              </h2>
              <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
                Join hundreds of interviewers and bootcamps using CodioLive for smooth, productive coding sessions.
              </p>
              
              <Button 
                variant="hero" 
                size="xl"
                onClick={() => navigate(user ? '/lobby' : '/signup')}
              >
                Get Started Now
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-4">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Code2 className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-semibold">CodioLive</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2025 CodioLive. Built for seamless technical interviews.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
