import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { api, User, Session } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  authError: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  guestJoinSession: (sessionId: string, username: string, pin: string) => Promise<Session>;
  retryAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const authGeneration = useRef(0);

  const checkAuth = async () => {
    const generation = ++authGeneration.current;
    setIsLoading(true);
    setAuthError(null);
    try {
      const nextUser = await api.auth.getCurrentUser();
      if (generation === authGeneration.current) setUser(nextUser);
    } catch (error) {
      if (generation === authGeneration.current) {
        setAuthError(error instanceof Error ? error.message : 'Authentication service unavailable');
      }
    } finally {
      if (generation === authGeneration.current) setIsLoading(false);
    }
  };

  useEffect(() => { void checkAuth(); }, []);

  const login = async (email: string, password: string) => {
    ++authGeneration.current;
    const user = await api.auth.login(email, password);
    setUser(user);
  };

  const signup = async (username: string, email: string, password: string) => {
    ++authGeneration.current;
    const user = await api.auth.signup(username, email, password);
    setUser(user);
  };

  const logout = async () => {
    ++authGeneration.current;
    await api.auth.logout();
    setUser(null);
  };

  const guestJoinSession = async (sessionId: string, username: string, pin: string) => {
    ++authGeneration.current;
    const result = await api.sessions.guestJoin(sessionId, username, pin);
    setUser(result.user);
    return result.session;
  };

  return (
    <AuthContext.Provider value={{
      user, isLoading, authError, login, signup, logout,
      guestJoinSession, retryAuth: checkAuth,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
