/**
 * Centralized API module for CodioLive
 * Uses generated OpenAPI client to communicate with the backend
 * Includes adapters to map API types to frontend internal types
 */

import { OpenAPI } from './api-client/core/OpenAPI';
import { AuthService } from './api-client/services/AuthService';
import { SessionsService } from './api-client/services/SessionsService';
import { ChatService } from './api-client/services/ChatService';
import { ExecutionService } from './api-client/services/ExecutionService';
import { LeaderboardService } from './api-client/services/LeaderboardService';

// Import generated types as 'Api*' to avoid conflicts
import type { User as ApiUser } from './api-client/models/User';
import type { Session as ApiSession } from './api-client/models/Session';
import type { Participant as ApiParticipant } from './api-client/models/Participant';
import type { Problem as ApiProblem } from './api-client/models/Problem';
import type { ChatMessage as ApiChatMessage } from './api-client/models/ChatMessage';
import type { ExecutionResult as ApiExecutionResult } from './api-client/models/ExecutionResult';
import type { TestResult as ApiTestResult } from './api-client/models/TestResult';
import type { LeaderboardEntry as ApiLeaderboardEntry } from './api-client/models/LeaderboardEntry';
import type { SupportedLanguage as ApiSupportedLanguage } from './api-client/models/SupportedLanguage';
import type { CursorPosition as ApiCursorPosition } from './api-client/models/CursorPosition';

// Configure API Client
// Note: Backend runs on port 8000 by default (FastAPI) while frontend is on 8080
OpenAPI.BASE = 'http://localhost:8000';
OpenAPI.WITH_CREDENTIALS = true;

// --- Frontend Internal Types (matching original mock structure) ---

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

// --- Type Mappers ---

function mapUser(apiUser: ApiUser): User {
  return {
    id: apiUser.id || '',
    username: apiUser.username || '',
    email: apiUser.email || '',
    avatar: apiUser.avatar,
    role: (apiUser.role as User['role']) || 'participant',
    createdAt: apiUser.createdAt ? new Date(apiUser.createdAt) : new Date(),
  };
}

function mapParticipant(apiParticipant: ApiParticipant): Participant {
  return {
    id: apiParticipant.id || '',
    username: apiParticipant.username || '',
    avatar: apiParticipant.avatar,
    role: (apiParticipant.role as Participant['role']) || 'participant',
    cursorPosition: apiParticipant.cursorPosition ? {
      line: apiParticipant.cursorPosition.line || 0,
      column: apiParticipant.cursorPosition.column || 0
    } : undefined,
    isTyping: apiParticipant.isTyping,
    color: apiParticipant.color || '#888', // Default color if missing
    joinedAt: apiParticipant.joinedAt ? new Date(apiParticipant.joinedAt) : new Date(),
  };
}

function mapProblem(apiProblem: ApiProblem): Problem {
  return {
    id: apiProblem.id || '',
    title: apiProblem.title || '',
    description: apiProblem.description || '',
    examples: (apiProblem.examples || []).map(ex => ({
      input: ex.input || '',
      output: ex.output || '',
      explanation: ex.explanation
    })),
    constraints: apiProblem.constraints || [],
    difficulty: (apiProblem.difficulty as Problem['difficulty']) || 'easy',
  };
}

function mapSession(apiSession: ApiSession): Session {
  return {
    id: apiSession.id || '',
    pin: apiSession.pin || '',
    hostId: apiSession.hostId || '',
    title: apiSession.title || '',
    description: apiSession.description || '',
    language: (apiSession.language as SupportedLanguage) || 'javascript',
    participants: (apiSession.participants || []).map(mapParticipant),
    code: apiSession.code || '',
    status: (apiSession.status as Session['status']) || 'waiting',
    createdAt: apiSession.createdAt ? new Date(apiSession.createdAt) : new Date(),
    problem: apiSession.problem ? mapProblem(apiSession.problem) : undefined,
  };
}

function mapChatMessage(apiMsg: ApiChatMessage): ChatMessage {
  return {
    id: apiMsg.id || '',
    participantId: apiMsg.participantId || '',
    username: apiMsg.username || '',
    message: apiMsg.message || '',
    timestamp: apiMsg.timestamp ? new Date(apiMsg.timestamp) : new Date(),
  };
}

function mapExecutionResult(apiRes: ApiExecutionResult): ExecutionResult {
  return {
    stdout: apiRes.stdout || '',
    stderr: apiRes.stderr || '',
    exitCode: apiRes.exitCode || 0,
    executionTime: apiRes.executionTime || 0,
    testResults: apiRes.testResults?.map(tr => ({
      passed: tr.passed || false,
      input: tr.input || '',
      expected: tr.expected || '',
      actual: tr.actual || ''
    })),
  };
}

function mapLeaderboardEntry(apiEntry: ApiLeaderboardEntry): LeaderboardEntry {
  return {
    rank: apiEntry.rank || 0,
    userId: apiEntry.userId || '',
    username: apiEntry.username || '',
    avatar: apiEntry.avatar,
    sessionsCompleted: apiEntry.sessionsCompleted || 0,
    avgScore: apiEntry.avgScore || 0,
    totalTime: apiEntry.totalTime || '',
  };
}


// --- Template Helpers (Keep local for now as optimistics) ---
const codeTemplates: Record<SupportedLanguage, string> = {
  javascript: `// Welcome to CodioLive!\n// Write your solution below\n\nfunction solution(input) {\n  // Your code here\n  return input;\n}\n\n// Test your solution\nconsole.log(solution([2, 7, 11, 15]));\n`,
  typescript: `// Welcome to CodioLive!\n// Write your solution below\n\nfunction solution(input: number[]): number[] {\n  // Your code here\n  return input;\n}\n\n// Test your solution\nconsole.log(solution([2, 7, 11, 15]));\n`,
  python: `# Welcome to CodioLive!\n# Write your solution below\n\ndef solution(input):\n    # Your code here\n    return input\n\n# Test your solution\nprint(solution([2, 7, 11, 15]))\n`,
  java: `// Welcome to CodioLive!\n// Write your solution below\n\npublic class Solution {\n    public static void main(String[] args) {\n        int[] result = solution(new int[]{2, 7, 11, 15});\n        System.out.println(java.util.Arrays.toString(result));\n    }\n    \n    public static int[] solution(int[] input) {\n        // Your code here\n        return input;\n    }\n}\n`,
  cpp: `// Welcome to CodioLive!\n// Write your solution below\n#include <iostream>\n#include <vector>\n\nstd::vector<int> solution(std::vector<int> input) {\n    // Your code here\n    return input;\n}\n\nint main() {\n    std::vector<int> result = solution({2, 7, 11, 15});\n    for (int n : result) std::cout << n << " ";\n    return 0;\n}\n`,
  go: `// Welcome to CodioLive!\n// Write your solution below\npackage main\n\nimport "fmt"\n\nfunc solution(input []int) []int {\n    // Your code here\n    return input\n}\n\nfunc main() {\n    result := solution([]int{2, 7, 11, 15})\n    fmt.Println(result)\n}\n`,
};

// --- API Implementation ---

export const api = {
  auth: {
    async login(email: string, password: string): Promise<User> {
      const user = await AuthService.loginUser({ email, password });
      return mapUser(user);
    },

    async signup(username: string, email: string, password: string): Promise<User> {
      const user = await AuthService.registerNewUser({ username, email, password });
      return mapUser(user);
    },

    async logout(): Promise<void> {
      return AuthService.logoutUser();
    },

    async getCurrentUser(): Promise<User | null> {
      try {
        const user = await AuthService.getCurrentAuthenticatedUser();
        return mapUser(user);
      } catch (error) {
        return null;
      }
    },

    async guestJoin(username: string): Promise<User> {
      const user = await AuthService.joinAsGuest({ username });
      return mapUser(user);
    },
  },

  sessions: {
    async create(title: string, language: SupportedLanguage = 'javascript'): Promise<Session> {
      const session = await SessionsService.createANewSession({
        title,
        language: language as ApiSupportedLanguage
      });
      return mapSession(session);
    },

    async join(sessionId: string, pin: string): Promise<Session> {
      const session = await SessionsService.joinASessionUsingIdAndPin(sessionId, { pin });
      return mapSession(session);
    },

    async joinByPin(pin: string): Promise<Session> {
      const session = await SessionsService.joinASessionUsingOnlyPin({ pin });
      return mapSession(session);
    },

    async get(sessionId: string): Promise<Session | null> {
      try {
        const session = await SessionsService.getSessionById(sessionId);
        return mapSession(session);
      } catch (error) {
        return null;
      }
    },

    async updateCode(sessionId: string, code: string): Promise<void> {
      await SessionsService.updateSessionCode(sessionId, { code });
    },

    async updateLanguage(sessionId: string, language: SupportedLanguage): Promise<void> {
      await SessionsService.updateSessionLanguage(sessionId, { language: language as ApiSupportedLanguage });
    },

    async updateCursor(sessionId: string, userId: string, position: CursorPosition): Promise<void> {
      await SessionsService.updateUserCursorPosition(sessionId, {
        userId,
        position: position as ApiCursorPosition
      });
    },

    async leave(sessionId: string): Promise<void> {
      await SessionsService.leaveASession(sessionId);
    },

    async end(sessionId: string): Promise<void> {
      await SessionsService.endASessionHostOnly(sessionId);
    },

    async getActive(): Promise<Session[]> {
      const sessions = await SessionsService.getActiveSessions();
      return sessions.map(mapSession);
    },
  },

  chat: {
    async send(sessionId: string, message: string): Promise<ChatMessage> {
      const msg = await ChatService.sendAChatMessage(sessionId, { message });
      return mapChatMessage(msg);
    },

    async getMessages(sessionId: string): Promise<ChatMessage[]> {
      const msgs = await ChatService.getChatMessages(sessionId);
      return msgs.map(mapChatMessage);
    },
  },

  execution: {
    async run(code: string, language: SupportedLanguage): Promise<ExecutionResult> {
      const res = await ExecutionService.runCode({
        code,
        language: language as ApiSupportedLanguage
      });
      return mapExecutionResult(res);
    },

    async runTests(code: string, language: SupportedLanguage, problem: Problem): Promise<ExecutionResult> {
      // Note: Helper might need recursive mapping if problem is complex, but for now we trust partial compatibility
      // Actually 'problem' in runTests likely needs ID or full object. 
      // The API expects 'Problem' object.
      // We should map strictly if possible.
      // For this tool call, we pass it as any or map it back.
      // Since the generated client expects ApiProblem, and our Problem is slightly different (dates?),
      // In this case actually Problem only has strings/arrays, so it might be compatible.
      // But 'difficulty' enum might need casting.

      const apiProblem: ApiProblem = {
        ...problem,
        difficulty: problem.difficulty as ApiProblem.difficulty // cast enum
      };

      const res = await ExecutionService.runTests({
        code,
        language: language as ApiSupportedLanguage,
        problem: apiProblem
      });
      return mapExecutionResult(res);
    },
  },

  leaderboard: {
    async get(): Promise<LeaderboardEntry[]> {
      const entries = await LeaderboardService.getLeaderboard();
      return entries.map(mapLeaderboardEntry);
    },
  },

  // Spectator (Not in API spec explicitly or mapped to sessions?)
  // Looking at spec, spectator logic might be just joining with role?
  // Or handled via active sessions list.
  // The mock had `spectator.getSessions` and `watch`.
  // `getSessions` -> `sessions.getActive` (already implemented)
  // `watch` -> `sessions.get`?
  spectator: {
    async getSessions(): Promise<Session[]> {
      const sessions = await SessionsService.getActiveSessions();
      return sessions.map(mapSession);
    },

    async watch(sessionId: string): Promise<Session | null> {
      try {
        const session = await SessionsService.getSessionById(sessionId);
        return mapSession(session);
      } catch (error) {
        return null; // Return null if not found
      }
    },
  },

  // Utilities - these were mostly frontend helpers, keep them if useful or adapt
  utils: {
    getCodeTemplate(language: SupportedLanguage): string {
      return codeTemplates[language] || '';
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
