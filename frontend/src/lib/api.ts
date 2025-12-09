/**
 * Centralized API module for CodioLive
 * Uses generated OpenAPI client to communicate with the backend
 * Includes adapters to map API types to frontend internal types
 */

import { OpenAPI } from './api-client/core/OpenAPI';
import { AuthService } from './api-client/services/AuthService';
import { SessionsService } from './api-client/services/SessionsService';
import { ChatService } from './api-client/services/ChatService';

// Browser-based code execution (WASM)
import { executeCode, runTests } from './codeExecutor';


// Import generated types as 'Api*' to avoid conflicts
import type { User as ApiUser } from './api-client/models/User';
import type { Session as ApiSession } from './api-client/models/Session';
import type { Participant as ApiParticipant } from './api-client/models/Participant';
import type { Problem as ApiProblem } from './api-client/models/Problem';
import type { ChatMessage as ApiChatMessage } from './api-client/models/ChatMessage';
// Note: ExecutionResult and TestResult types are defined locally since
// code execution now happens in the browser via WASM, not the backend.

import type { SupportedLanguage as ApiSupportedLanguage } from './api-client/models/SupportedLanguage';
import type { CursorPosition as ApiCursorPosition } from './api-client/models/CursorPosition';

// Configure API Client
// Use relative /api path - works with both Vite dev proxy and nginx production proxy
OpenAPI.BASE = '/api';
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

// Note: mapExecutionResult removed - execution now happens in browser via WASM




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
      try {
        const user = await AuthService.postAuthLogin({ email, password });
        return mapUser(user);
      } catch (error: any) {
        console.error('Login error:', error);
        if (error.body) console.error('Error body:', error.body);

        if (error.body && error.body.detail) {
          throw new Error(error.body.detail);
        }
        // Handle case where body is missing (e.g. proxy 404 or 504)
        if (error.status === 404) {
          throw new Error('Server not reachable or user not found (404)');
        }
        if (error.status === 504 || error.status === 502) {
          throw new Error('Backend server is not running');
        }
        throw error;
      }
    },

    async signup(username: string, email: string, password: string): Promise<User> {
      try {
        const user = await AuthService.postAuthSignup({ username, email, password });
        return mapUser(user);
      } catch (error: any) {
        if (error.body && error.body.detail) {
          throw new Error(error.body.detail);
        }
        throw error;
      }
    },

    async logout(): Promise<void> {
      return AuthService.postAuthLogout();
    },

    async getCurrentUser(): Promise<User | null> {
      try {
        const user = await AuthService.getAuthMe();
        return mapUser(user);
      } catch (error) {
        return null; // Not authenticated
      }
    },

    async guestJoin(username: string): Promise<User> {
      const user = await AuthService.postAuthGuest({ username });
      return mapUser(user);
    },
  },

  sessions: {
    async create(title: string, language: SupportedLanguage = 'javascript'): Promise<Session> {
      const session = await SessionsService.postSessions({
        title,
        language: language as ApiSupportedLanguage
      });
      return mapSession(session);
    },

    async join(sessionId: string, pin: string): Promise<Session> {
      const session = await SessionsService.postSessionsJoin(sessionId, { pin });
      return mapSession(session);
    },

    async joinByPin(pin: string): Promise<Session> {
      const session = await SessionsService.postSessionsJoinByPin({ pin });
      return mapSession(session);
    },

    async get(sessionId: string): Promise<Session | null> {
      try {
        // Updated to use getSessions1 as per generated client if necessary, or check if getSessions(id) exists
        // Looking at generated file: public static getSessions1(id: string): ...
        const session = await SessionsService.getSessions1(sessionId);
        return mapSession(session);
      } catch (error) {
        return null;
      }
    },

    async updateCode(sessionId: string, code: string): Promise<void> {
      await SessionsService.putSessionsCode(sessionId, { code });
    },

    async updateLanguage(sessionId: string, language: SupportedLanguage): Promise<void> {
      await SessionsService.putSessionsLanguage(sessionId, { language: language as ApiSupportedLanguage });
    },

    async updateCursor(sessionId: string, userId: string, position: CursorPosition): Promise<void> {
      await SessionsService.putSessionsCursor(sessionId, {
        userId,
        position: position as ApiCursorPosition
      });
    },

    async leave(sessionId: string): Promise<void> {
      await SessionsService.postSessionsLeave(sessionId);
    },

    async end(sessionId: string): Promise<void> {
      await SessionsService.postSessionsEnd(sessionId);
    },

    async getActive(): Promise<Session[]> {
      const sessions = await SessionsService.getSessions();
      return sessions.map(mapSession);
    },
  },

  chat: {
    async send(sessionId: string, message: string): Promise<ChatMessage> {
      const msg = await ChatService.postSessionsMessages(sessionId, { message });
      return mapChatMessage(msg);
    },

    async getMessages(sessionId: string): Promise<ChatMessage[]> {
      const msgs = await ChatService.getSessionsMessages(sessionId);
      return msgs.map(mapChatMessage);
    },
  },

  execution: {
    async run(code: string, language: SupportedLanguage): Promise<ExecutionResult> {
      // Execute code locally in the browser using WASM for security
      return executeCode(code, language);
    },

    async test(code: string, language: SupportedLanguage, problem: Problem): Promise<ExecutionResult> {
      // Run tests locally in the browser using WASM for security
      return runTests(code, language, problem);
    },
  },



  spectator: {
    async getSessions(): Promise<Session[]> {
      const sessions = await SessionsService.getSessions();
      return sessions.map(mapSession);
    },

    async watch(sessionId: string): Promise<Session | null> {
      try {
        const session = await SessionsService.getSessions1(sessionId);
        return mapSession(session);
      } catch (error) {
        return null;
      }
    },
  },

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
