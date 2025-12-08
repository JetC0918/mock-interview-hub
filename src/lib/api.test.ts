import { describe, it, expect, beforeEach, vi } from 'vitest';
import { api } from './api';

describe('API Module', () => {
  beforeEach(() => {
    // Reset state between tests
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should login a user with valid credentials', async () => {
      const user = await api.auth.login('test@example.com', 'password123');
      
      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(user.username).toBe('test');
      expect(user.role).toBe('host');
    });

    it('should throw error for invalid login credentials', async () => {
      await expect(api.auth.login('', '')).rejects.toThrow('Invalid credentials');
    });

    it('should signup a new user', async () => {
      const user = await api.auth.signup('newuser', 'new@example.com', 'password123');
      
      expect(user).toBeDefined();
      expect(user.username).toBe('newuser');
      expect(user.email).toBe('new@example.com');
    });

    it('should throw error for incomplete signup', async () => {
      await expect(api.auth.signup('', 'email@test.com', 'pass')).rejects.toThrow('All fields required');
    });

    it('should logout a user', async () => {
      await api.auth.login('test@example.com', 'password');
      await api.auth.logout();
      const user = await api.auth.getCurrentUser();
      
      expect(user).toBeNull();
    });

    it('should join as guest with username', async () => {
      const user = await api.auth.guestJoin('GuestUser');
      
      expect(user.username).toBe('GuestUser');
      expect(user.role).toBe('participant');
    });
  });

  describe('Session Management', () => {
    beforeEach(async () => {
      await api.auth.login('host@example.com', 'password');
    });

    it('should create a new session', async () => {
      const session = await api.sessions.create('Interview Session', 'javascript');
      
      expect(session).toBeDefined();
      expect(session.title).toBe('Interview Session');
      expect(session.language).toBe('javascript');
      expect(session.pin).toMatch(/^\d{6}$/);
      expect(session.status).toBe('waiting');
      expect(session.participants.length).toBe(1);
    });

    it('should create sessions with different languages', async () => {
      const jsSession = await api.sessions.create('JS Interview', 'javascript');
      const pySession = await api.sessions.create('Python Interview', 'python');
      
      expect(jsSession.language).toBe('javascript');
      expect(pySession.language).toBe('python');
      expect(jsSession.code).toContain('function');
      expect(pySession.code).toContain('def');
    });

    it('should get session by id', async () => {
      const created = await api.sessions.create('Test Session', 'javascript');
      const fetched = await api.sessions.get(created.id);
      
      expect(fetched).toBeDefined();
      expect(fetched?.id).toBe(created.id);
    });

    it('should return null for non-existent session', async () => {
      const session = await api.sessions.get('non-existent-id');
      expect(session).toBeNull();
    });

    it('should update session code', async () => {
      const session = await api.sessions.create('Test', 'javascript');
      await api.sessions.updateCode(session.id, 'const x = 42;');
      const updated = await api.sessions.get(session.id);
      
      expect(updated?.code).toBe('const x = 42;');
    });

    it('should update session language', async () => {
      const session = await api.sessions.create('Test', 'javascript');
      await api.sessions.updateLanguage(session.id, 'python');
      const updated = await api.sessions.get(session.id);
      
      expect(updated?.language).toBe('python');
      expect(updated?.code).toContain('def');
    });

    it('should end a session', async () => {
      const session = await api.sessions.create('Test', 'javascript');
      await api.sessions.end(session.id);
      const ended = await api.sessions.get(session.id);
      
      expect(ended?.status).toBe('ended');
    });

    it('should get active sessions', async () => {
      await api.sessions.create('Active 1', 'javascript');
      await api.sessions.create('Active 2', 'python');
      const active = await api.sessions.getActive();
      
      expect(active.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Link Generation', () => {
    it('should generate shareable link for session', async () => {
      await api.auth.login('host@example.com', 'password');
      const session = await api.sessions.create('Test', 'javascript');
      const link = api.utils.generateShareableLink(session.id);
      
      expect(link).toContain('/session/');
      expect(link).toContain(session.id);
    });
  });

  describe('Language Support', () => {
    it('should return all supported languages', () => {
      const languages = api.utils.getSupportedLanguages();
      
      expect(languages).toContain('javascript');
      expect(languages).toContain('typescript');
      expect(languages).toContain('python');
      expect(languages).toContain('java');
      expect(languages).toContain('cpp');
      expect(languages).toContain('go');
    });

    it('should return code template for each language', () => {
      const languages = api.utils.getSupportedLanguages();
      
      languages.forEach(langObj => {
        const template = api.utils.getCodeTemplate(langObj.value);
        expect(template).toBeDefined();
        expect(template.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Code Execution', () => {
    it('should execute JavaScript code', async () => {
      const result = await api.execution.run('console.log("hello")', 'javascript');
      
      expect(result.stdout).toBe('hello');
      expect(result.exitCode).toBe(0);
    });

    it('should catch JavaScript errors', async () => {
      const result = await api.execution.run('throw new Error("test error")', 'javascript');
      
      expect(result.stderr).toContain('test error');
      expect(result.exitCode).toBe(1);
    });

    it('should return mock output for non-JS languages', async () => {
      const result = await api.execution.run('print("hello")', 'python');
      
      expect(result.stdout).toContain('Mock');
      expect(result.exitCode).toBe(0);
    });
  });

  describe('Chat', () => {
    it('should send and retrieve chat messages', async () => {
      await api.auth.login('user@example.com', 'password');
      const session = await api.sessions.create('Chat Test', 'javascript');
      
      await api.chat.send(session.id, 'Hello!');
      await api.chat.send(session.id, 'How are you?');
      
      const messages = await api.chat.getMessages(session.id);
      
      expect(messages.length).toBe(2);
      expect(messages[0].message).toBe('Hello!');
      expect(messages[1].message).toBe('How are you?');
    });
  });

  describe('Leaderboard', () => {
    it('should return leaderboard entries', async () => {
      const leaderboard = await api.leaderboard.get();
      
      expect(Array.isArray(leaderboard)).toBe(true);
      expect(leaderboard.length).toBeGreaterThan(0);
      expect(leaderboard[0]).toHaveProperty('rank');
      expect(leaderboard[0]).toHaveProperty('username');
      expect(leaderboard[0]).toHaveProperty('avgScore');
    });
  });
});
