import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import authService from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 应用挂载时先确保 CSRF Cookie 已下发（所有不安全请求都需要它）
  const ensureCsrf = useCallback(async () => {
    try {
      await api.get('/auth/csrf/');
    } catch {
      // 获取 CSRF 失败不阻断；登录/注册等写操作前仍会携带当前可用的 csrftoken
    }
  }, []);

  // 加载当前登录用户（未登录时接口返回 401，捕获后置为匿名状态）
  const loadUser = useCallback(async () => {
    try {
      const data = await authService.getCurrentUser();
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const init = async () => {
      await ensureCsrf();
      if (cancelled) return;
      await loadUser();
    };
    init();
    return () => {
      cancelled = true;
    };
  }, [ensureCsrf, loadUser]);

  const checkAuth = useCallback(async () => {
    try {
      const data = await authService.checkAuth();
      setUser(data.is_authenticated ? data.user : null);
      return data;
    } catch {
      setUser(null);
      return { is_authenticated: false, user: null };
    }
  }, []);

  const login = async (username, password) => {
    await authService.login(username, password);
    await loadUser();
  };

  const register = async (data) => {
    const result = await authService.register(data);
    await loadUser();
    return result;
  };

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      // 登出接口失败不阻塞前端状态清理
    } finally {
      setUser(null);
    }
  }, []);

  const updateProfile = async (data) => {
    const result = await authService.updateProfile(data);
    setUser(result);
    return result;
  };

  const deleteAccount = async () => {
    await authService.deleteAccount();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
        deleteAccount,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
