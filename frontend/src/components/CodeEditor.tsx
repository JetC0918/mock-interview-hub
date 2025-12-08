import React, { useRef, useEffect, useState } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { SupportedLanguage, Participant } from '@/lib/api';

interface CodeEditorProps {
  code: string;
  language: SupportedLanguage;
  onChange: (value: string) => void;
  participants: Participant[];
  currentUserId: string;
  readOnly?: boolean;
}

const languageMap: Record<SupportedLanguage, string> = {
  javascript: 'javascript',
  typescript: 'typescript',
  python: 'python',
  java: 'java',
  cpp: 'cpp',
  go: 'go',
};

const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  language,
  onChange,
  participants,
  currentUserId,
  readOnly = false,
}) => {
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    setIsLoaded(true);

    // Define custom theme
    monaco.editor.defineTheme('codiolive', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
        { token: 'keyword', foreground: '569CD6' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: 'B5CEA8' },
        { token: 'function', foreground: 'DCDCAA' },
        { token: 'variable', foreground: '9CDCFE' },
        { token: 'type', foreground: '4EC9B0' },
      ],
      colors: {
        'editor.background': '#0a0e14',
        'editor.foreground': '#f8f8f2',
        'editor.lineHighlightBackground': '#111827',
        'editor.selectionBackground': '#22d3ee33',
        'editorCursor.foreground': '#22d3ee',
        'editorLineNumber.foreground': '#4b5563',
        'editorLineNumber.activeForeground': '#9ca3af',
        'editorGutter.background': '#0d1117',
        'editor.selectionHighlightBackground': '#22d3ee22',
      },
    });

    monaco.editor.setTheme('codiolive');

    editor.updateOptions({
      fontSize: 14,
      fontFamily: "'JetBrains Mono', monospace",
      fontLigatures: true,
      lineHeight: 22,
      padding: { top: 16, bottom: 16 },
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      renderLineHighlight: 'line',
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      smoothScrolling: true,
      bracketPairColorization: { enabled: true },
      wordWrap: 'on',
    });
  };

  // Update remote cursors
  useEffect(() => {
    if (!editorRef.current || !isLoaded) return;

    const monaco = (window as any).monaco;
    if (!monaco) return;

    const newDecorations = participants
      .filter((p) => p.id !== currentUserId && p.cursorPosition)
      .map((participant) => ({
        range: new monaco.Range(
          participant.cursorPosition!.line,
          participant.cursorPosition!.column,
          participant.cursorPosition!.line,
          participant.cursorPosition!.column + 1
        ),
        options: {
          className: `remote-cursor-${participants.indexOf(participant) + 1}`,
          beforeContentClassName: 'remote-cursor-marker',
          hoverMessage: { value: participant.username },
          stickiness: 1,
        },
      }));

    decorationsRef.current = editorRef.current.deltaDecorations(
      decorationsRef.current,
      newDecorations
    );
  }, [participants, currentUserId, isLoaded]);

  return (
    <div className="h-full w-full rounded-lg overflow-hidden border border-border bg-editor-bg">
      <style>{`
        .remote-cursor-1 { background-color: hsl(174 72% 50% / 0.3); }
        .remote-cursor-2 { background-color: hsl(265 70% 60% / 0.3); }
        .remote-cursor-3 { background-color: hsl(38 92% 50% / 0.3); }
        .remote-cursor-4 { background-color: hsl(330 80% 60% / 0.3); }
        .remote-cursor-5 { background-color: hsl(142 72% 45% / 0.3); }
        .remote-cursor-marker {
          border-left: 2px solid;
          animation: blink 1s ease-in-out infinite;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
      <Editor
        height="100%"
        language={languageMap[language]}
        value={code}
        onChange={(value) => onChange(value || '')}
        onMount={handleEditorDidMount}
        loading={
          <div className="flex h-full items-center justify-center bg-editor-bg">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        }
        options={{
          readOnly,
        }}
      />
    </div>
  );
};

export default CodeEditor;
