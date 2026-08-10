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
import { AiAssistantService } from './api-client/services/AiAssistantService';

// Import generated types as 'Api*' to avoid conflicts
import type { User as ApiUser } from './api-client/models/User';
import type { Session as ApiSession } from './api-client/models/Session';
import type { PublicSession as ApiPublicSession } from './api-client/models/PublicSession';
import type { Participant as ApiParticipant } from './api-client/models/Participant';
import type { Problem as ApiProblem } from './api-client/models/Problem';
import type { ChatMessage as ApiChatMessage } from './api-client/models/ChatMessage';
// Note: ExecutionResult and TestResult types are defined locally since
// code execution now happens in the browser via WASM, not the backend.

import type { SupportedLanguage as ApiSupportedLanguage } from './api-client/models/SupportedLanguage';
import type { CursorPosition as ApiCursorPosition } from './api-client/models/CursorPosition';
import type { ExecutionResult as ApiExecutionResult } from './api-client/models/ExecutionResult';

type ApiErrorLike = {
  status?: number;
  body?: unknown;
};

const asApiError = (error: unknown): ApiErrorLike => {
  if (typeof error !== 'object' || error === null) return {};
  const candidate = error as Record<string, unknown>;
  return {
    status: typeof candidate.status === 'number' ? candidate.status : undefined,
    body: candidate.body,
  };
};

const getApiDetail = (error: unknown): string | undefined => {
  const body = asApiError(error).body;
  if (typeof body !== 'object' || body === null) return undefined;
  const detail = (body as Record<string, unknown>).detail;
  return typeof detail === 'string' ? detail : undefined;
};

// Configure API Client
// Configuration moved to main.tsx to ensure it runs before any requests


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
  codeRevision: number;
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
  authorType?: 'user' | 'assistant';
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

const parseUtcDate = (value: string | undefined, field: string): Date => {
  if (!value || !/(?:Z|[+-]\d{2}:\d{2})$/.test(value)) {
    throw new Error(`Invalid ${field}: expected an ISO-8601 timestamp with UTC offset`);
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) throw new Error(`Invalid ${field}`);
  return parsed;
};

// --- Type Mappers ---

function mapUser(apiUser: ApiUser): User {
  return {
    id: apiUser.id || '',
    username: apiUser.username || '',
    email: apiUser.email || '',
    avatar: apiUser.avatar,
    role: (apiUser.role as User['role']) || 'participant',
    createdAt: parseUtcDate(apiUser.createdAt, 'user.createdAt'),
  };
}

function mapParticipant(apiParticipant: ApiParticipant, index: number): Participant {
  return {
    // PublicParticipant intentionally omits user IDs. Keep a local render key
    // without fabricating an authorization identity.
    id: apiParticipant.id || `public-${index}`,
    username: apiParticipant.username || '',
    avatar: apiParticipant.avatar,
    role: (apiParticipant.role as Participant['role']) || 'participant',
    cursorPosition: apiParticipant.cursorPosition ? {
      line: apiParticipant.cursorPosition.line || 0,
      column: apiParticipant.cursorPosition.column || 0
    } : undefined,
    isTyping: apiParticipant.isTyping,
    color: apiParticipant.color || '#888', // Default color if missing
    joinedAt: parseUtcDate(apiParticipant.joinedAt, 'participant.joinedAt'),
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
    codeRevision: typeof apiSession.codeRevision === 'number' ? apiSession.codeRevision : (() => { throw new Error('Session response is missing codeRevision'); })(),
    status: (apiSession.status as Session['status']) || 'waiting',
    createdAt: parseUtcDate(apiSession.createdAt, 'session.createdAt'),
    problem: apiSession.problem ? mapProblem(apiSession.problem) : undefined,
  };
}

function mapPublicSession(apiSession: ApiPublicSession): Session {
  return {
    id: apiSession.id,
    pin: '',
    hostId: '',
    title: apiSession.title,
    description: apiSession.description || '',
    language: apiSession.language as SupportedLanguage,
    participants: (apiSession.participants || []).map((participant, index) => ({
      id: `public-${index}`,
      username: participant.username,
      avatar: participant.avatar,
      role: participant.role as Participant['role'],
      cursorPosition: participant.cursorPosition ? {
        line: participant.cursorPosition.line,
        column: participant.cursorPosition.column,
      } : undefined,
      isTyping: participant.isTyping,
      color: participant.color || '#888',
      joinedAt: parseUtcDate(participant.joinedAt, 'participant.joinedAt'),
    })),
    code: apiSession.code || '',
    codeRevision: apiSession.codeRevision,
    status: apiSession.status as Session['status'],
    createdAt: parseUtcDate(apiSession.createdAt, 'session.createdAt'),
    problem: apiSession.problem ? mapProblem(apiSession.problem) : undefined,
  };
}

function mapChatMessage(apiMsg: ApiChatMessage): ChatMessage {
  return {
    id: apiMsg.id || '',
    participantId: apiMsg.participantId || '',
    username: apiMsg.username || '',
    authorType: (apiMsg.authorType as ChatMessage['authorType']) || 'user',
    message: apiMsg.message || '',
    timestamp: parseUtcDate(apiMsg.timestamp, 'message.timestamp'),
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
      } catch (error: unknown) {
        const apiError = asApiError(error);
        const detail = getApiDetail(error);
        if (detail) {
          throw new Error(detail);
        }
        // Handle case where body is missing (e.g. proxy 404 or 504)
        if (apiError.status === 404) {
          throw new Error('Server not reachable or user not found (404)');
        }
        if (apiError.status === 504 || apiError.status === 502) {
          throw new Error('Backend server is not running');
        }
        throw error;
      }
    },

    async signup(username: string, email: string, password: string): Promise<User> {
      try {
        const user = await AuthService.postAuthSignup({ username, email, password });
        return mapUser(user);
      } catch (error: unknown) {
        const detail = getApiDetail(error);
        if (detail) {
          throw new Error(detail);
        }
        throw error;
      }
    },

    async logout(): Promise<void> {
      await AuthService.postAuthLogout();
    },

    async getCurrentUser(): Promise<User | null> {
      try {
        const user = await AuthService.getAuthMe();
        return mapUser(user);
      } catch (error: unknown) {
        const status = asApiError(error).status;
        if (status === 401) {
          return null;
        }
        throw error;
      }
    },

  },

  sessions: {
    async create(title: string, language: SupportedLanguage = 'javascript'): Promise<Session> {
      const session = await SessionsService.postSessions({ title, language: language as ApiSupportedLanguage });
      return mapSession(session);
    },

    async start(sessionId: string): Promise<void> {
      await SessionsService.startSessionSessionsIdStartPost({ id: sessionId });
    },

    async join(sessionId: string, pin: string): Promise<Session> {
      const session = await SessionsService.postSessionsJoin(sessionId, { pin });
      return mapSession(session);
    },

    async joinByPin(pin: string): Promise<Session> {
      const session = await SessionsService.postSessionsJoinByPin({ pin });
      return mapSession(session);
    },

    async guestJoin(sessionId: string, username: string, pin: string): Promise<{ user: User; session: Session }> {
      const attemptKey = `guest-attempt:${sessionId}`;
      let attempt: { attemptId: string; attemptSecret: string } | undefined;
      try { attempt = JSON.parse(window.localStorage.getItem(attemptKey) || 'null'); } catch { /* ignore malformed local state */ }
      if (!attempt?.attemptId || !attempt?.attemptSecret) {
        const random = new Uint8Array(32);
        crypto.getRandomValues(random);
        const encoded = btoa(String.fromCharCode(...random)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
        attempt = { attemptId: `${crypto.randomUUID()}_${Date.now()}`, attemptSecret: encoded };
        window.localStorage.setItem(attemptKey, JSON.stringify(attempt));
      }
      const data = await SessionsService.guestJoinSessionSessionsIdGuestJoinPost({
        id: sessionId,
        requestBody: { username, pin, attemptId: attempt.attemptId, attemptSecret: attempt.attemptSecret },
      });
      return { user: mapUser(data.user), session: mapSession(data.session) };
    },

    async getPublic(sessionId: string): Promise<Session | null> {
      try {
        return mapPublicSession(await SessionsService.getSessions1(sessionId));
      } catch (error: unknown) {
        if (asApiError(error).status === 404) return null;
        throw error;
      }
    },

    async get(sessionId: string): Promise<Session | null> {
      try {
        // Updated to use getSessions1 as per generated client if necessary, or check if getSessions(id) exists
        // Looking at generated file: public static getSessions1(id: string): ...
        const session = await SessionsService.getSessionsPrivate(sessionId);
        return mapSession(session);
      } catch (error: unknown) {
        if (asApiError(error).status === 404) {
          return null;
        }
        throw error;
      }
    },

    async updateCode(sessionId: string, code: string, baseRevision?: number): Promise<number> {
      const result = await SessionsService.putSessionsCode(sessionId, baseRevision === undefined ? { code } as never : { code, baseRevision });
      return result?.codeRevision ?? 0;
    },

    async updateLanguage(sessionId: string, language: SupportedLanguage, baseRevision?: number): Promise<number> {
      const result = await SessionsService.putSessionsLanguage(sessionId, baseRevision === undefined ? { language: language as ApiSupportedLanguage } as never : { language: language as ApiSupportedLanguage, baseRevision });
      return result?.codeRevision ?? 0;
    },

    async updateCursor(sessionId: string, position: CursorPosition): Promise<void> {
      await SessionsService.putSessionsCursor(sessionId, { position: position as ApiCursorPosition });
    },

    async leave(sessionId: string): Promise<void> {
      await SessionsService.postSessionsLeave(sessionId);
    },

    async end(sessionId: string): Promise<void> {
      await SessionsService.postSessionsEnd(sessionId);
    },

    async getActive(): Promise<Session[]> {
      const sessions = await SessionsService.getSessions();
      return sessions.map(mapPublicSession);
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

  ai: {
    async getGuidance(sessionId: string, message: string, problemContext?: Problem, requestId = crypto.randomUUID().replace(/-/g, '')): Promise<ChatMessage> {
      const response = await AiAssistantService.getAiAssistanceAiAssistPost({ requestBody: {
          sessionId,
          message,
          requestId,
          problemContext: problemContext ? {
            title: problemContext.title,
            description: problemContext.description,
            examples: problemContext.examples,
            constraints: problemContext.constraints,
            difficulty: problemContext.difficulty,
          } : undefined,
        } });
      return mapChatMessage(response as unknown as ApiChatMessage);
    },
  },

  execution: {
    async run(code: string, language: SupportedLanguage): Promise<ExecutionResult> {
      await ExecutionService.postExecutionRun({ code, language: language as ApiSupportedLanguage });
      return { stdout: '', stderr: 'Collaborative execution requires a fully isolated runtime and is disabled.', exitCode: 1, executionTime: 0 };
    },

    async test(code: string, language: SupportedLanguage, problem: Problem): Promise<ExecutionResult> {
      await ExecutionService.postExecutionTest({ code, language: language as ApiSupportedLanguage, problem: problem as unknown as ApiProblem });
      return { stdout: '', stderr: 'Collaborative execution requires a fully isolated runtime and is disabled.', exitCode: 1, executionTime: 0 };
    },
  },



  spectator: {
    async getSessions(): Promise<Session[]> {
      const sessions = await SessionsService.getPublicSessionsSessionsPublicGet();
      return sessions.map(mapSession);
    },

    async watch(sessionId: string): Promise<Session | null> {
      try {
        const session = await SessionsService.getSessions1(sessionId);
        return mapPublicSession(session);
      } catch (error: unknown) {
        if (asApiError(error).status === 404) return null;
        throw error;
      }
    },

    async getMessages(sessionId: string): Promise<ChatMessage[]> {
      const rows = await SessionsService.getPublicMessagesSessionsIdPublicMessagesGet({ id: sessionId, limit: 50 });
      return rows.map((row: { username: string; message: string; timestamp: string; authorType: 'user' | 'assistant' }) => ({
        // Public DTOs intentionally omit database IDs.  Derive a stable
        // render/merge key from the immutable transcript projection instead
        // of a polling-page index that shifts as the bounded window advances.
        id: `${row.timestamp}|${row.authorType}|${row.username}|${row.message}`, participantId: '', authorType: row.authorType, username: row.username,
        message: row.message, timestamp: parseUtcDate(row.timestamp, 'public message timestamp'),
      }));
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
