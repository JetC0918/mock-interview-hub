import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from './api';
import { AuthService } from './api-client/services/AuthService';
import { SessionsService } from './api-client/services/SessionsService';
import { ChatService } from './api-client/services/ChatService';
import { ExecutionService } from './api-client/services/ExecutionService';


// Mock the generated services with explicit libraries
// We use the names found in the generated files
vi.mock('./api-client/services/AuthService', () => ({
  AuthService: {
    postAuthLogin: vi.fn(),
    postAuthSignup: vi.fn(),
    postAuthLogout: vi.fn(),
    getAuthMe: vi.fn(),
    postAuthGuest: vi.fn(),
  },
}));

vi.mock('./api-client/services/SessionsService', () => ({
  SessionsService: {
    postSessions: vi.fn(),
    postSessionsJoin: vi.fn(),
    postSessionsJoinByPin: vi.fn(),
    getSessions1: vi.fn(), // getSessionById mapped to getSessions1
    putSessionsCode: vi.fn(),
    putSessionsLanguage: vi.fn(),
    putSessionsCursor: vi.fn(),
    postSessionsLeave: vi.fn(),
    postSessionsEnd: vi.fn(),
    getSessions: vi.fn(), // getActiveSessions mapped to getSessions
  },
}));

vi.mock('./api-client/services/ChatService', () => ({
  ChatService: {
    postSessionsMessages: vi.fn(), // sendAChatMessage
    getSessionsMessages: vi.fn(), // getChatMessages
  },
}));

vi.mock('./api-client/services/ExecutionService', () => ({
  ExecutionService: {
    postExecutionRun: vi.fn(), // runCode
    postExecutionTest: vi.fn(), // runTests
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
        createdAt: new Date().toISOString() // API returns string
      };
      vi.mocked(AuthService.postAuthLogin).mockResolvedValue(mockUser as any);

      const user = await api.auth.login('test@example.com', 'password123');

      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(user.username).toBe('test');
      expect(user.role).toBe('host');
      expect(AuthService.postAuthLogin).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' });
    });

    it('login with invalid credentials throws specific error', async () => {
      const errorBody = { detail: 'User not found' };
      const apiError = new Error('Not Found') as any;
      apiError.body = errorBody;

      vi.mocked(AuthService.postAuthLogin).mockRejectedValue(apiError);

      await expect(api.auth.login('wrong@example.com', 'password')).rejects.toThrow('User not found');
    });

    it('should signup a new user', async () => {
      const mockUser = {
        id: '2',
        username: 'newuser',
        email: 'new@example.com',
        role: 'host',
        createdAt: new Date().toISOString()
      };
      vi.mocked(AuthService.postAuthSignup).mockResolvedValue(mockUser as any);

      const user = await api.auth.signup('newuser', 'new@example.com', 'password123');

      expect(user).toBeDefined();
      expect(user.username).toBe('newuser');
      expect(user.email).toBe('new@example.com');
    });

    it('should throw error for incomplete signup', async () => {
      vi.mocked(AuthService.postAuthSignup).mockRejectedValue(new Error('All fields required'));
      await expect(api.auth.signup('', 'email@test.com', 'pass')).rejects.toThrow('All fields required');
    });

    it('should logout a user', async () => {
      vi.mocked(AuthService.postAuthLogout).mockResolvedValue(undefined as any);
      // Removed dependent mock checking for getCurrentUser as logout doesn't inherently call it in the implementation unless specified

      await api.auth.logout();
      expect(AuthService.postAuthLogout).toHaveBeenCalled();
    });

    it('should join as guest with username', async () => {
      const mockUser = {
        id: 'guest',
        username: 'GuestUser',
        email: '',
        role: 'participant',
        createdAt: new Date().toISOString()
      };
      vi.mocked(AuthService.postAuthGuest).mockResolvedValue(mockUser as any);

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
      vi.mocked(SessionsService.postSessions).mockResolvedValue(mockSession as any);

      const session = await api.sessions.create('Interview Session', 'javascript');

      expect(session).toBeDefined();
      expect(session.title).toBe('Interview Session');
      expect(session.language).toBe('javascript');
      expect(session.status).toBe('waiting');
      expect(session.participants.length).toBe(1);
    });

    it('should get session by id', async () => {
      const mockSession = { id: 'sess1', title: 'Test Session', createdAt: new Date().toISOString() };
      vi.mocked(SessionsService.getSessions1).mockResolvedValue(mockSession as any);

      const fetched = await api.sessions.get('sess1');

      expect(fetched).toBeDefined();
      expect(fetched?.id).toBe('sess1');
    });

    it('should return null for non-existent session', async () => {
      vi.mocked(SessionsService.getSessions1).mockRejectedValue(new Error('Not found'));
      const session = await api.sessions.get('non-existent-id');
      expect(session).toBeNull();
    });

    it('should update session code', async () => {
      vi.mocked(SessionsService.putSessionsCode).mockResolvedValue(undefined as any);
      await api.sessions.updateCode('id', 'const x = 42;');
      expect(SessionsService.putSessionsCode).toHaveBeenCalledWith('id', { code: 'const x = 42;' });
    });

    it('should update session language', async () => {
      vi.mocked(SessionsService.putSessionsLanguage).mockResolvedValue(undefined as any);
      await api.sessions.updateLanguage('id', 'python');
      expect(SessionsService.putSessionsLanguage).toHaveBeenCalledWith('id', { language: 'python' });
    });

    it('should end a session', async () => {
      vi.mocked(SessionsService.postSessionsEnd).mockResolvedValue(undefined as any);
      await api.sessions.end('id');
      expect(SessionsService.postSessionsEnd).toHaveBeenCalledWith('id');
    });

    it('should get active sessions', async () => {
      const mockSessions = [
        { id: '1', title: 'Active 1', status: 'active', createdAt: new Date().toISOString() },
        { id: '2', title: 'Active 2', status: 'active', createdAt: new Date().toISOString() }
      ];
      vi.mocked(SessionsService.getSessions).mockResolvedValue(mockSessions as any);

      const active = await api.sessions.getActive();
      expect(active.length).toBe(2);
    });
  });

  describe('Link Generation', () => {
    it('should generate shareable link for session', async () => {
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
      vi.mocked(ExecutionService.postExecutionRun).mockResolvedValue(mockResult as any);

      const result = await api.execution.run('console.log("hello")', 'javascript');

      expect(result.stdout).toBe('hello');
      expect(result.exitCode).toBe(0);
    });
  });

  describe('Chat', () => {
    it('should send and retrieve chat messages', async () => {
      const mockMsg = { id: 'm1', message: 'Hello!', timestamp: new Date().toISOString() };
      vi.mocked(ChatService.postSessionsMessages).mockResolvedValue(mockMsg as any);

      await api.chat.send('s1', 'Hello!');
      expect(ChatService.postSessionsMessages).toHaveBeenCalledWith('s1', { message: 'Hello!' });
    });

    it('should get messages', async () => {
      const mockMsgs = [{ id: 'm1', message: 'Hello!', timestamp: new Date().toISOString() }];
      vi.mocked(ChatService.getSessionsMessages).mockResolvedValue(mockMsgs as any);

      const msgs = await api.chat.getMessages('s1');
      expect(msgs.length).toBe(1);
      expect(msgs[0].message).toBe('Hello!');
    });
  });


});
