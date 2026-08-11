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
  },
}));

vi.mock('./api-client/services/SessionsService', () => ({
  SessionsService: {
    postSessions: vi.fn(),
    postSessionsJoin: vi.fn(),
    postSessionsJoinByPin: vi.fn(),
    getSessions1: vi.fn(), // getSessionById mapped to getSessions1
    getSessionsPrivate: vi.fn(),
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
      vi.mocked(AuthService.postAuthLogin).mockResolvedValue(mockUser as unknown as Awaited<ReturnType<typeof AuthService.postAuthLogin>>);

      const user = await api.auth.login('test@example.com', 'password123');

      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(user.username).toBe('test');
      expect(user.role).toBe('host');
      expect(AuthService.postAuthLogin).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' });
    });

    it('login with invalid credentials throws specific error', async () => {
      const errorBody = { detail: 'Invalid email or password' };
      const apiError = Object.assign(new Error('Not Found'), { body: errorBody });

      vi.mocked(AuthService.postAuthLogin).mockRejectedValue(apiError);

      await expect(api.auth.login('wrong@example.com', 'password')).rejects.toThrow('Invalid email or password');
    });

    it('should signup a new user', async () => {
      const mockUser = {
        id: '2',
        username: 'newuser',
        email: 'new@example.com',
        role: 'host',
        createdAt: new Date().toISOString()
      };
      vi.mocked(AuthService.postAuthSignup).mockResolvedValue(mockUser as unknown as Awaited<ReturnType<typeof AuthService.postAuthSignup>>);

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
      vi.mocked(AuthService.postAuthLogout).mockResolvedValue(undefined);
      // Removed dependent mock checking for getCurrentUser as logout doesn't inherently call it in the implementation unless specified

      await api.auth.logout();
      expect(AuthService.postAuthLogout).toHaveBeenCalled();
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
        codeRevision: 0,
        participants: [{ id: '1', username: 'host', joinedAt: new Date().toISOString() }],
        createdAt: new Date().toISOString()
      };
      vi.mocked(SessionsService.postSessions).mockResolvedValue(mockSession as unknown as Awaited<ReturnType<typeof SessionsService.postSessions>>);

      const session = await api.sessions.create('Interview Session', 'javascript');

      expect(session).toBeDefined();
      expect(session.title).toBe('Interview Session');
      expect(session.language).toBe('javascript');
      expect(session.status).toBe('waiting');
      expect(session.participants.length).toBe(1);
    });

    it('should get session by id', async () => {
      const mockSession = { id: 'sess1', title: 'Test Session', codeRevision: 0, createdAt: new Date().toISOString() };
      vi.mocked(SessionsService.getSessionsPrivate).mockResolvedValue(mockSession as unknown as Awaited<ReturnType<typeof SessionsService.getSessionsPrivate>>);

      const fetched = await api.sessions.get('sess1');

      expect(fetched).toBeDefined();
      expect(fetched?.id).toBe('sess1');
    });

    it('should return null for non-existent session', async () => {
      vi.mocked(SessionsService.getSessionsPrivate).mockRejectedValue(Object.assign(new Error('Not found'), { status: 404 }));
      const session = await api.sessions.get('non-existent-id');
      expect(session).toBeNull();
    });

    it('should update session code', async () => {
      vi.mocked(SessionsService.putSessionsCode).mockResolvedValue(undefined);
      await api.sessions.updateCode('id', 'const x = 42;');
      expect(SessionsService.putSessionsCode).toHaveBeenCalledWith('id', { code: 'const x = 42;' });
    });

    it('should update session language', async () => {
      vi.mocked(SessionsService.putSessionsLanguage).mockResolvedValue(undefined);
      await api.sessions.updateLanguage('id', 'python');
      expect(SessionsService.putSessionsLanguage).toHaveBeenCalledWith('id', { language: 'python' });
    });

    it('should end a session', async () => {
      vi.mocked(SessionsService.postSessionsEnd).mockResolvedValue(undefined);
      await api.sessions.end('id');
      expect(SessionsService.postSessionsEnd).toHaveBeenCalledWith('id');
    });

    it('should get active sessions', async () => {
      const mockSessions = [
        { id: '1', title: 'Active 1', status: 'active', createdAt: new Date().toISOString() },
        { id: '2', title: 'Active 2', status: 'active', createdAt: new Date().toISOString() }
      ];
      vi.mocked(SessionsService.getSessions).mockResolvedValue(mockSessions as unknown as Awaited<ReturnType<typeof SessionsService.getSessions>>);

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
  it('should report that collaborative execution is disabled', async () => {
      const mockResult = { stdout: 'hello', exitCode: 0, executionTime: 10 };
      vi.mocked(ExecutionService.postExecutionRun).mockResolvedValue(mockResult as unknown as Awaited<ReturnType<typeof ExecutionService.postExecutionRun>>);

      const result = await api.execution.run('console.log("hello")', 'javascript');

    expect(result.stdout).toBe('');
    expect(result.stderr).toContain('fully isolated runtime');
    expect(result.exitCode).toBe(1);
    });
  });

  describe('Chat', () => {
    it('should send and retrieve chat messages', async () => {
      const mockMsg = { id: 'm1', message: 'Hello!', timestamp: new Date().toISOString() };
      vi.mocked(ChatService.postSessionsMessages).mockResolvedValue(mockMsg as unknown as Awaited<ReturnType<typeof ChatService.postSessionsMessages>>);

      await api.chat.send('s1', 'Hello!');
      expect(ChatService.postSessionsMessages).toHaveBeenCalledWith('s1', { message: 'Hello!' });
    });

    it('should get messages', async () => {
      const mockMsgs = [{ id: 'm1', message: 'Hello!', timestamp: new Date().toISOString() }];
      vi.mocked(ChatService.getSessionsMessages).mockResolvedValue(mockMsgs as unknown as Awaited<ReturnType<typeof ChatService.getSessionsMessages>>);

      const msgs = await api.chat.getMessages('s1');
      expect(msgs.length).toBe(1);
      expect(msgs[0].message).toBe('Hello!');
    });
  });


});
