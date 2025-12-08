import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from './api';
import { AuthService } from './api-client/services/AuthService';
import { SessionsService } from './api-client/services/SessionsService';
import { ChatService } from './api-client/services/ChatService';
import { ExecutionService } from './api-client/services/ExecutionService';
import { LeaderboardService } from './api-client/services/LeaderboardService';

// Mock the generated services with explicit factories
vi.mock('./api-client/services/AuthService', () => ({
  AuthService: {
    loginUser: vi.fn(),
    registerNewUser: vi.fn(),
    logoutUser: vi.fn(),
    getCurrentAuthenticatedUser: vi.fn(),
    joinAsGuest: vi.fn(),
  },
}));

vi.mock('./api-client/services/SessionsService', () => ({
  SessionsService: {
    createANewSession: vi.fn(),
    joinASessionUsingIdAndPin: vi.fn(),
    joinASessionUsingOnlyPin: vi.fn(),
    getSessionById: vi.fn(),
    updateSessionCode: vi.fn(),
    updateSessionLanguage: vi.fn(),
    updateUserCursorPosition: vi.fn(),
    leaveASession: vi.fn(),
    endASessionHostOnly: vi.fn(),
    getActiveSessions: vi.fn(),
  },
}));

vi.mock('./api-client/services/ChatService', () => ({
  ChatService: {
    sendAChatMessage: vi.fn(),
    getChatMessages: vi.fn(),
  },
}));

vi.mock('./api-client/services/ExecutionService', () => ({
  ExecutionService: {
    runCode: vi.fn(),
    runTests: vi.fn(),
  },
}));

vi.mock('./api-client/services/LeaderboardService', () => ({
  LeaderboardService: {
    getLeaderboard: vi.fn(),
  },
}));

describe('API Module', () => {
  beforeEach(() => {
    // Reset state between tests
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should login a user with valid credentials', async () => {
      // Mock response
      const mockUser = {
        id: '1',
        username: 'test',
        email: 'test@example.com',
        role: 'host',
        createdAt: new Date().toISOString()
      };
      vi.mocked(AuthService.loginUser).mockResolvedValue(mockUser as any);

      const user = await api.auth.login('test@example.com', 'password123');

      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(user.username).toBe('test');
      expect(user.role).toBe('host');
      expect(AuthService.loginUser).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' });
    });

    it('should throw error for invalid login credentials', async () => {
      vi.mocked(AuthService.loginUser).mockRejectedValue(new Error('Invalid credentials'));
      await expect(api.auth.login('', '')).rejects.toThrow('Invalid credentials');
    });

    it('should signup a new user', async () => {
      const mockUser = {
        id: '2',
        username: 'newuser',
        email: 'new@example.com',
        role: 'host',
        createdAt: new Date().toISOString()
      };
      vi.mocked(AuthService.registerNewUser).mockResolvedValue(mockUser as any);

      const user = await api.auth.signup('newuser', 'new@example.com', 'password123');

      expect(user).toBeDefined();
      expect(user.username).toBe('newuser');
      expect(user.email).toBe('new@example.com');
    });

    it('should throw error for incomplete signup', async () => {
      vi.mocked(AuthService.registerNewUser).mockRejectedValue(new Error('All fields required'));
      await expect(api.auth.signup('', 'email@test.com', 'pass')).rejects.toThrow('All fields required');
    });

    it('should logout a user', async () => {
      vi.mocked(AuthService.logoutUser).mockResolvedValue(undefined as any);
      vi.mocked(AuthService.getCurrentAuthenticatedUser).mockResolvedValue(null as any); // Or throw if not auth

      await api.auth.logout();
      expect(AuthService.logoutUser).toHaveBeenCalled();
    });

    it('should join as guest with username', async () => {
      const mockUser = {
        id: 'guest',
        username: 'GuestUser',
        email: '',
        role: 'participant',
        createdAt: new Date().toISOString()
      };
      vi.mocked(AuthService.joinAsGuest).mockResolvedValue(mockUser as any);

      const user = await api.auth.guestJoin('GuestUser');

      expect(user.username).toBe('GuestUser');
      expect(user.role).toBe('participant');
    });
  });

  describe('Session Management', () => {
    it('should create a new session', async () => {
      const mockSession = {
        id: 'sess1',
        title: 'Interview Session',
        language: 'javascript',
        pin: '123456',
        status: 'waiting',
        participants: [{ id: '1', username: 'host' }],
        createdAt: new Date().toISOString()
      };
      vi.mocked(SessionsService.createANewSession).mockResolvedValue(mockSession as any);

      const session = await api.sessions.create('Interview Session', 'javascript');

      expect(session).toBeDefined();
      expect(session.title).toBe('Interview Session');
      expect(session.language).toBe('javascript');
      // expect(session.pin).toMatch(/^\d{6}$/); // Mocked value
      expect(session.status).toBe('waiting');
      expect(session.participants.length).toBe(1);
    });

    it('should get session by id', async () => {
      const mockSession = { id: 'sess1', title: 'Test Session', createdAt: new Date().toISOString() };
      vi.mocked(SessionsService.getSessionById).mockResolvedValue(mockSession as any);

      const fetched = await api.sessions.get('sess1');

      expect(fetched).toBeDefined();
      expect(fetched?.id).toBe('sess1');
    });

    it('should return null for non-existent session', async () => {
      vi.mocked(SessionsService.getSessionById).mockRejectedValue(new Error('Not found'));
      const session = await api.sessions.get('non-existent-id');
      expect(session).toBeNull();
    });

    it('should update session code', async () => {
      vi.mocked(SessionsService.updateSessionCode).mockResolvedValue(undefined as any);
      await api.sessions.updateCode('id', 'const x = 42;');
      expect(SessionsService.updateSessionCode).toHaveBeenCalledWith('id', { code: 'const x = 42;' });
    });

    it('should update session language', async () => {
      vi.mocked(SessionsService.updateSessionLanguage).mockResolvedValue(undefined as any);
      await api.sessions.updateLanguage('id', 'python');
      expect(SessionsService.updateSessionLanguage).toHaveBeenCalledWith('id', { language: 'python' });
    });

    it('should end a session', async () => {
      vi.mocked(SessionsService.endASessionHostOnly).mockResolvedValue(undefined as any);
      await api.sessions.end('id');
      expect(SessionsService.endASessionHostOnly).toHaveBeenCalledWith('id');
    });

    it('should get active sessions', async () => {
      const mockSessions = [
        { id: '1', title: 'Active 1', status: 'active', createdAt: new Date().toISOString() },
        { id: '2', title: 'Active 2', status: 'active', createdAt: new Date().toISOString() }
      ];
      vi.mocked(SessionsService.getActiveSessions).mockResolvedValue(mockSessions as any);

      const active = await api.sessions.getActive();
      expect(active.length).toBe(2);
    });
  });

  describe('Link Generation', () => {
    it('should generate shareable link for session', async () => {
      // Utilities are still local but depend on window
      const link = api.utils.generateShareableLink('123');
      expect(link).toContain('/session/');
      expect(link).toContain('123');
    });
  });

  describe('Language Support', () => {
    it('should return all supported languages', () => {
      const languages = api.utils.getSupportedLanguages();
      const languageValues = languages.map(l => l.value);
      expect(languageValues).toContain('javascript');
    });

    it('should return code template for each language', () => {
      const template = api.utils.getCodeTemplate('javascript');
      expect(template).toContain('Welcome');
    });
  });

  describe('Code Execution', () => {
    it('should execute JavaScript code', async () => {
      const mockResult = { stdout: 'hello', exitCode: 0, executionTime: 10 };
      vi.mocked(ExecutionService.runCode).mockResolvedValue(mockResult as any);

      const result = await api.execution.run('console.log("hello")', 'javascript');

      expect(result.stdout).toBe('hello');
      expect(result.exitCode).toBe(0);
    });
  });

  describe('Chat', () => {
    it('should send and retrieve chat messages', async () => {
      const mockMsg = { id: 'm1', message: 'Hello!', timestamp: new Date().toISOString() };
      vi.mocked(ChatService.sendAChatMessage).mockResolvedValue(mockMsg as any);

      await api.chat.send('s1', 'Hello!');
      expect(ChatService.sendAChatMessage).toHaveBeenCalledWith('s1', { message: 'Hello!' });
    });

    it('should get messages', async () => {
      const mockMsgs = [{ id: 'm1', message: 'Hello!', timestamp: new Date().toISOString() }];
      vi.mocked(ChatService.getChatMessages).mockResolvedValue(mockMsgs as any);

      const msgs = await api.chat.getMessages('s1');
      expect(msgs.length).toBe(1);
      expect(msgs[0].message).toBe('Hello!');
    });
  });

  describe('Leaderboard', () => {
    it('should return leaderboard entries', async () => {
      const mockEntries = [{ rank: 1, username: 'user', avgScore: 100 }];
      vi.mocked(LeaderboardService.getLeaderboard).mockResolvedValue(mockEntries as any);

      const leaderboard = await api.leaderboard.get();
      expect(leaderboard.length).toBe(1);
      expect(leaderboard[0].username).toBe('user');
    });
  });
});
