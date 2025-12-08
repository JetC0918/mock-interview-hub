/**
 * Centralized API module for CodioLive
 * All backend calls are mocked here for easy replacement with real API later
 */

import { v4 as uuidv4 } from 'uuid';

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  role: 'host' | 'participant' | 'spectator';
  createdAt: Date;
}

export interface Session {
  id: string;
  pin: string;
  hostId: string;
  title: string;
  description: string;
  language: SupportedLanguage;
  participants: Participant[];
  code: string;
  status: 'waiting' | 'active' | 'ended';
  createdAt: Date;
  problem?: Problem;
}

export interface Participant {
  id: string;
  username: string;
  avatar?: string;
  role: 'host' | 'participant' | 'spectator';
  cursorPosition?: CursorPosition;
  isTyping?: boolean;
  color: string;
  joinedAt: Date;
}

export interface CursorPosition {
  line: number;
  column: number;
}

export interface Problem {
  id: string;
  title: string;
  description: string;
  examples: { input: string; output: string; explanation?: string }[];
  constraints: string[];
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface ChatMessage {
  id: string;
  participantId: string;
  username: string;
  message: string;
  timestamp: Date;
}

export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  executionTime: number;
  testResults?: TestResult[];
}

export interface TestResult {
  passed: boolean;
  input: string;
  expected: string;
  actual: string;
}

export interface LeaderboardEntry {
  rank: number;
  userId: string;
  username: string;
  avatar?: string;
  sessionsCompleted: number;
  avgScore: number;
  totalTime: string;
}

export type SupportedLanguage = 'javascript' | 'typescript' | 'python' | 'java' | 'cpp' | 'go';

// Mock data storage
let currentUser: User | null = null;
const sessions: Map<string, Session> = new Map();
const chatMessages: Map<string, ChatMessage[]> = new Map();

// Simulated network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock cursor colors
const cursorColors = [
  'hsl(174 72% 50%)', // cyan
  'hsl(265 70% 60%)', // purple
  'hsl(38 92% 50%)',  // orange
  'hsl(330 80% 60%)', // pink
  'hsl(142 72% 45%)', // green
];

// Sample problems
const sampleProblems: Problem[] = [
  {
    id: '1',
    title: 'Two Sum',
    description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.',
    examples: [
      { input: 'nums = [2,7,11,15], target = 9', output: '[0,1]', explanation: 'Because nums[0] + nums[1] == 9, we return [0, 1].' },
      { input: 'nums = [3,2,4], target = 6', output: '[1,2]' },
    ],
    constraints: ['2 <= nums.length <= 10^4', '-10^9 <= nums[i] <= 10^9', 'Only one valid answer exists.'],
    difficulty: 'easy',
  },
  {
    id: '2',
    title: 'Reverse Linked List',
    description: 'Given the head of a singly linked list, reverse the list, and return the reversed list.',
    examples: [
      { input: 'head = [1,2,3,4,5]', output: '[5,4,3,2,1]' },
      { input: 'head = [1,2]', output: '[2,1]' },
    ],
    constraints: ['The number of nodes in the list is the range [0, 5000]', '-5000 <= Node.val <= 5000'],
    difficulty: 'easy',
  },
  {
    id: '3',
    title: 'Valid Parentheses',
    description: 'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.\n\nAn input string is valid if:\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket of the same type.',
    examples: [
      { input: 's = "()"', output: 'true' },
      { input: 's = "()[]{}"', output: 'true' },
      { input: 's = "(]"', output: 'false' },
    ],
    constraints: ['1 <= s.length <= 10^4', 's consists of parentheses only \'()[]{}\''],
    difficulty: 'easy',
  },
];

// Default code templates
const codeTemplates: Record<SupportedLanguage, string> = {
  javascript: `// Welcome to CodioLive!
// Write your solution below

function solution(input) {
  // Your code here
  return input;
}

// Test your solution
console.log(solution([2, 7, 11, 15]));
`,
  typescript: `// Welcome to CodioLive!
// Write your solution below

function solution(input: number[]): number[] {
  // Your code here
  return input;
}

// Test your solution
console.log(solution([2, 7, 11, 15]));
`,
  python: `# Welcome to CodioLive!
# Write your solution below

def solution(input):
    # Your code here
    return input

# Test your solution
print(solution([2, 7, 11, 15]))
`,
  java: `// Welcome to CodioLive!
// Write your solution below

public class Solution {
    public static void main(String[] args) {
        int[] result = solution(new int[]{2, 7, 11, 15});
        System.out.println(java.util.Arrays.toString(result));
    }
    
    public static int[] solution(int[] input) {
        // Your code here
        return input;
    }
}
`,
  cpp: `// Welcome to CodioLive!
// Write your solution below
#include <iostream>
#include <vector>

std::vector<int> solution(std::vector<int> input) {
    // Your code here
    return input;
}

int main() {
    std::vector<int> result = solution({2, 7, 11, 15});
    for (int n : result) std::cout << n << " ";
    return 0;
}
`,
  go: `// Welcome to CodioLive!
// Write your solution below
package main

import "fmt"

func solution(input []int) []int {
    // Your code here
    return input
}

func main() {
    result := solution([]int{2, 7, 11, 15})
    fmt.Println(result)
}
`,
};

// Generate random PIN
const generatePin = (): string => {
  return Math.floor(100000 + Math.random() * 900000).toString();
};

// API Functions

export const api = {
  // Auth
  auth: {
    async login(email: string, password: string): Promise<User> {
      await delay(800);
      if (!email || !password) throw new Error('Invalid credentials');
      
      currentUser = {
        id: uuidv4(),
        username: email.split('@')[0],
        email,
        role: 'host',
        createdAt: new Date(),
      };
      return currentUser;
    },

    async signup(username: string, email: string, password: string): Promise<User> {
      await delay(800);
      if (!username || !email || !password) throw new Error('All fields required');
      
      currentUser = {
        id: uuidv4(),
        username,
        email,
        role: 'host',
        createdAt: new Date(),
      };
      return currentUser;
    },

    async logout(): Promise<void> {
      await delay(300);
      currentUser = null;
    },

    async getCurrentUser(): Promise<User | null> {
      await delay(200);
      return currentUser;
    },

    async guestJoin(username: string): Promise<User> {
      await delay(300);
      currentUser = {
        id: uuidv4(),
        username,
        email: '',
        role: 'participant',
        createdAt: new Date(),
      };
      return currentUser;
    },
  },

  // Sessions
  sessions: {
    async create(title: string, language: SupportedLanguage = 'javascript'): Promise<Session> {
      await delay(500);
      if (!currentUser) throw new Error('Must be logged in to create session');

      const session: Session = {
        id: uuidv4(),
        pin: generatePin(),
        hostId: currentUser.id,
        title,
        description: '',
        language,
        participants: [{
          id: currentUser.id,
          username: currentUser.username,
          role: 'host',
          color: cursorColors[0],
          joinedAt: new Date(),
        }],
        code: codeTemplates[language],
        status: 'waiting',
        createdAt: new Date(),
        problem: sampleProblems[Math.floor(Math.random() * sampleProblems.length)],
      };

      sessions.set(session.id, session);
      chatMessages.set(session.id, []);
      return session;
    },

    async join(sessionId: string, pin: string): Promise<Session> {
      await delay(500);
      const session = sessions.get(sessionId);
      if (!session) throw new Error('Session not found');
      if (session.pin !== pin) throw new Error('Invalid PIN');
      if (!currentUser) throw new Error('Must be logged in');

      const existingParticipant = session.participants.find(p => p.id === currentUser!.id);
      if (!existingParticipant) {
        session.participants.push({
          id: currentUser.id,
          username: currentUser.username,
          role: currentUser.role,
          color: cursorColors[session.participants.length % cursorColors.length],
          joinedAt: new Date(),
        });
      }

      return session;
    },

    async joinByPin(pin: string): Promise<Session> {
      await delay(500);
      const session = Array.from(sessions.values()).find(s => s.pin === pin);
      if (!session) throw new Error('Session not found');
      if (!currentUser) throw new Error('Must be logged in');

      const existingParticipant = session.participants.find(p => p.id === currentUser!.id);
      if (!existingParticipant) {
        session.participants.push({
          id: currentUser.id,
          username: currentUser.username,
          role: currentUser.role,
          color: cursorColors[session.participants.length % cursorColors.length],
          joinedAt: new Date(),
        });
      }

      return session;
    },

    async get(sessionId: string): Promise<Session | null> {
      await delay(200);
      return sessions.get(sessionId) || null;
    },

    async updateCode(sessionId: string, code: string): Promise<void> {
      await delay(50);
      const session = sessions.get(sessionId);
      if (session) {
        session.code = code;
      }
    },

    async updateLanguage(sessionId: string, language: SupportedLanguage): Promise<void> {
      await delay(100);
      const session = sessions.get(sessionId);
      if (session) {
        session.language = language;
        session.code = codeTemplates[language];
      }
    },

    async updateCursor(sessionId: string, userId: string, position: CursorPosition): Promise<void> {
      const session = sessions.get(sessionId);
      if (session) {
        const participant = session.participants.find(p => p.id === userId);
        if (participant) {
          participant.cursorPosition = position;
        }
      }
    },

    async leave(sessionId: string): Promise<void> {
      await delay(200);
      const session = sessions.get(sessionId);
      if (session && currentUser) {
        session.participants = session.participants.filter(p => p.id !== currentUser!.id);
      }
    },

    async end(sessionId: string): Promise<void> {
      await delay(300);
      const session = sessions.get(sessionId);
      if (session) {
        session.status = 'ended';
      }
    },

    async getActive(): Promise<Session[]> {
      await delay(300);
      return Array.from(sessions.values()).filter(s => s.status !== 'ended');
    },
  },

  // Chat
  chat: {
    async send(sessionId: string, message: string): Promise<ChatMessage> {
      await delay(100);
      if (!currentUser) throw new Error('Must be logged in');

      const chatMessage: ChatMessage = {
        id: uuidv4(),
        participantId: currentUser.id,
        username: currentUser.username,
        message,
        timestamp: new Date(),
      };

      const messages = chatMessages.get(sessionId) || [];
      messages.push(chatMessage);
      chatMessages.set(sessionId, messages);

      return chatMessage;
    },

    async getMessages(sessionId: string): Promise<ChatMessage[]> {
      await delay(100);
      return chatMessages.get(sessionId) || [];
    },
  },

  // Code Execution (sandboxed - simulated)
  execution: {
    async run(code: string, language: SupportedLanguage): Promise<ExecutionResult> {
      await delay(1000);

      // Only JavaScript and Python have real execution in browser
      if (language === 'javascript' || language === 'typescript') {
        try {
          const logs: string[] = [];
          const originalLog = console.log;
          console.log = (...args) => {
            logs.push(args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' '));
          };

          // Create sandboxed execution
          const sandboxedCode = `
            (function() {
              ${code}
            })();
          `;
          
          const startTime = performance.now();
          eval(sandboxedCode);
          const executionTime = performance.now() - startTime;

          console.log = originalLog;

          return {
            stdout: logs.join('\n'),
            stderr: '',
            exitCode: 0,
            executionTime,
          };
        } catch (error: any) {
          return {
            stdout: '',
            stderr: error.message,
            exitCode: 1,
            executionTime: 0,
          };
        }
      }

      // Mock execution for other languages
      return {
        stdout: `[Mock] Executed ${language} code successfully.\nOutput: [2, 7, 11, 15]`,
        stderr: '',
        exitCode: 0,
        executionTime: 234,
      };
    },

    async runTests(code: string, language: SupportedLanguage, problem: Problem): Promise<ExecutionResult> {
      await delay(1500);

      // Mock test results
      const testResults: TestResult[] = problem.examples.map((example, i) => ({
        passed: i < 2,
        input: example.input,
        expected: example.output,
        actual: i < 2 ? example.output : '[0, 0]',
      }));

      return {
        stdout: `Running ${testResults.length} test cases...`,
        stderr: '',
        exitCode: testResults.some(t => !t.passed) ? 1 : 0,
        executionTime: 456,
        testResults,
      };
    },
  },

  // Leaderboard
  leaderboard: {
    async get(): Promise<LeaderboardEntry[]> {
      await delay(400);
      return [
        { rank: 1, userId: '1', username: 'alex_dev', sessionsCompleted: 47, avgScore: 98, totalTime: '12h 34m' },
        { rank: 2, userId: '2', username: 'sarah_codes', sessionsCompleted: 42, avgScore: 95, totalTime: '14h 22m' },
        { rank: 3, userId: '3', username: 'mike_python', sessionsCompleted: 38, avgScore: 92, totalTime: '11h 45m' },
        { rank: 4, userId: '4', username: 'emma_js', sessionsCompleted: 35, avgScore: 89, totalTime: '15h 10m' },
        { rank: 5, userId: '5', username: 'david_rust', sessionsCompleted: 31, avgScore: 87, totalTime: '10h 55m' },
        { rank: 6, userId: '6', username: 'lisa_go', sessionsCompleted: 28, avgScore: 85, totalTime: '9h 30m' },
        { rank: 7, userId: '7', username: 'tom_java', sessionsCompleted: 25, avgScore: 82, totalTime: '13h 15m' },
        { rank: 8, userId: '8', username: 'anna_cpp', sessionsCompleted: 22, avgScore: 80, totalTime: '8h 45m' },
      ];
    },
  },

  // Spectator
  spectator: {
    async getSessions(): Promise<Session[]> {
      await delay(400);
      return Array.from(sessions.values()).filter(s => s.status === 'active');
    },

    async watch(sessionId: string): Promise<Session | null> {
      await delay(200);
      return sessions.get(sessionId) || null;
    },
  },

  // Utilities
  utils: {
    getCodeTemplate(language: SupportedLanguage): string {
      return codeTemplates[language];
    },

    getSupportedLanguages(): { value: SupportedLanguage; label: string }[] {
      return [
        { value: 'javascript', label: 'JavaScript' },
        { value: 'typescript', label: 'TypeScript' },
        { value: 'python', label: 'Python' },
        { value: 'java', label: 'Java' },
        { value: 'cpp', label: 'C++' },
        { value: 'go', label: 'Go' },
      ];
    },

    generateShareableLink(sessionId: string): string {
      return `${window.location.origin}/session/${sessionId}`;
    },
  },
};

export default api;
