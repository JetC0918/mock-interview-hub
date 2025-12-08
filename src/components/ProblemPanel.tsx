import React from 'react';
import { Problem } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface ProblemPanelProps {
  problem: Problem;
}

const difficultyColors: Record<string, string> = {
  easy: 'bg-success/20 text-success',
  medium: 'bg-warning/20 text-warning',
  hard: 'bg-destructive/20 text-destructive',
};

const ProblemPanel: React.FC<ProblemPanelProps> = ({ problem }) => {
  return (
    <div className="h-full bg-card rounded-lg border border-border flex flex-col">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold">Problem</h3>
        <Badge className={difficultyColors[problem.difficulty]}>
          {problem.difficulty}
        </Badge>
      </div>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold mb-3">{problem.title}</h2>
            <p className="text-muted-foreground whitespace-pre-wrap leading-relaxed">
              {problem.description}
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Examples</h4>
            <div className="space-y-3">
              {problem.examples.map((example, index) => (
                <div
                  key={index}
                  className="bg-secondary/50 rounded-lg p-4 space-y-2 font-mono text-sm"
                >
                  <div>
                    <span className="text-muted-foreground">Input: </span>
                    <span className="text-foreground">{example.input}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Output: </span>
                    <span className="text-primary">{example.output}</span>
                  </div>
                  {example.explanation && (
                    <div className="pt-2 border-t border-border">
                      <span className="text-muted-foreground">
                        {example.explanation}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Constraints</h4>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {problem.constraints.map((constraint, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-primary">•</span>
                  <code className="font-mono">{constraint}</code>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};

export default ProblemPanel;
