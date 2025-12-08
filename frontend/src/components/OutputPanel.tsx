import React from 'react';
import { ExecutionResult, TestResult } from '@/lib/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle, XCircle, Clock, Terminal } from 'lucide-react';

interface OutputPanelProps {
  result: ExecutionResult | null;
  isRunning: boolean;
}

const OutputPanel: React.FC<OutputPanelProps> = ({ result, isRunning }) => {
  if (isRunning) {
    return (
      <div className="h-full bg-card rounded-lg border border-border flex flex-col">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="font-semibold flex items-center gap-2">
            <Terminal className="h-4 w-4" />
            Output
          </h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="h-8 w-8 mx-auto mb-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-muted-foreground">Running code...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-full bg-card rounded-lg border border-border flex flex-col">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="font-semibold flex items-center gap-2">
            <Terminal className="h-4 w-4" />
            Output
          </h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Run your code to see output</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-card rounded-lg border border-border flex flex-col">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Terminal className="h-4 w-4" />
          Output
        </h3>
        <div className="flex items-center gap-3 text-sm">
          {result.exitCode === 0 ? (
            <span className="flex items-center gap-1 text-success">
              <CheckCircle className="h-4 w-4" />
              Success
            </span>
          ) : (
            <span className="flex items-center gap-1 text-destructive">
              <XCircle className="h-4 w-4" />
              Error
            </span>
          )}
          <span className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-4 w-4" />
            {result.executionTime.toFixed(0)}ms
          </span>
        </div>
      </div>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {result.stdout && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">stdout</h4>
              <pre className="bg-secondary/50 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap overflow-x-auto">
                {result.stdout}
              </pre>
            </div>
          )}

          {result.stderr && (
            <div>
              <h4 className="text-sm font-medium text-destructive mb-2">stderr</h4>
              <pre className="bg-destructive/10 text-destructive rounded-lg p-4 font-mono text-sm whitespace-pre-wrap overflow-x-auto">
                {result.stderr}
              </pre>
            </div>
          )}

          {result.testResults && result.testResults.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">
                Test Results ({result.testResults.filter((t) => t.passed).length}/
                {result.testResults.length} passed)
              </h4>
              <div className="space-y-2">
                {result.testResults.map((test, index) => (
                  <TestResultCard key={index} test={test} index={index} />
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

const TestResultCard: React.FC<{ test: TestResult; index: number }> = ({
  test,
  index,
}) => {
  return (
    <div
      className={`rounded-lg p-3 ${
        test.passed ? 'bg-success/10' : 'bg-destructive/10'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        {test.passed ? (
          <CheckCircle className="h-4 w-4 text-success" />
        ) : (
          <XCircle className="h-4 w-4 text-destructive" />
        )}
        <span className="font-medium">Test Case {index + 1}</span>
      </div>
      <div className="grid gap-1 text-sm font-mono">
        <div>
          <span className="text-muted-foreground">Input: </span>
          {test.input}
        </div>
        <div>
          <span className="text-muted-foreground">Expected: </span>
          <span className="text-success">{test.expected}</span>
        </div>
        {!test.passed && (
          <div>
            <span className="text-muted-foreground">Actual: </span>
            <span className="text-destructive">{test.actual}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default OutputPanel;
