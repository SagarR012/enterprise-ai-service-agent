import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { auth } from '../services/api';
import type { UserInfo } from '../types';

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  switchUser: (userId: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const u = await auth.me();
      setUser(u);
    } catch {
      setUser(null);
      setToken(null);
      localStorage.removeItem('token');
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token, fetchUser]);

  const login = async (email: string, password: string) => {
    const res = await auth.login({ email, password });
    localStorage.setItem('token', res.access_token);
    setToken(res.access_token);
    setUser({ id: res.user_id, name: res.name, email, role: res.role, workspace_id: res.workspace_id });
  };

  const switchUser = async (userId: string) => {
    const res = await auth.switchUser(userId);
    localStorage.setItem('token', res.access_token);
    setToken(res.access_token);
    setUser({ id: res.user_id, name: res.name, email: '', role: res.role, workspace_id: res.workspace_id });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const refresh = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, switchUser, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
