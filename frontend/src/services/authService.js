import api from './api';

/**
 * 认证服务：HttpOnly Cookie + CSRF 认证方案。
 * 前端不再存储任何 token —— 访问/刷新凭据均存放在 HttpOnly Cookie 中，
 * 由浏览器自动携带，服务端自动轮换。
 */

// 内存中的登录标记（仅用于便捷判断，真正的认证状态以 Cookie/服务端为准）
let _authenticated = false;

/**
 * 设置内存登录标记（供内部及测试使用）。
 * @param {boolean} value
 */
export function setAuthenticated(value) {
  _authenticated = !!value;
}

export const authService = {
  /**
   * 用户登录
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{success: boolean, message: string, user: object}>}
   */
  async login(username, password) {
    const response = await api.post('/auth/login/', { username, password });
    setAuthenticated(true);
    return response.data;
  },

  /**
   * 用户注册（注册成功后自动登录，服务端写入 Cookie）
   * @param {object} data - { username, email, password, password2 }
   * @returns {Promise<{success: boolean, message: string, user: object}>}
   */
  async register(data) {
    const response = await api.post('/auth/register/', data);
    setAuthenticated(true);
    return response.data;
  },

  /**
   * 退出登录：调用服务端清除 HttpOnly Cookie
   * @returns {Promise<object>}
   */
  async logout() {
    try {
      const response = await api.post('/auth/logout/');
      return response.data;
    } finally {
      setAuthenticated(false);
    }
  },

  /**
   * 获取当前登录用户信息
   * @returns {Promise<{id, username, email, date_joined, profile: {phone, avatar, bio}}>}
   */
  async getCurrentUser() {
    try {
      const response = await api.get('/auth/me/');
      setAuthenticated(true);
      return response.data;
    } catch (err) {
      setAuthenticated(false);
      throw err;
    }
  },

  /**
   * 检查登录状态
   * @returns {Promise<{is_authenticated: boolean, user: object|null}>}
   */
  async checkAuth() {
    try {
      const response = await api.get('/auth/check/');
      setAuthenticated(true);
      return response.data;
    } catch {
      setAuthenticated(false);
      return { is_authenticated: false, user: null };
    }
  },

  /**
   * 更新用户资料
   * @param {object} data - { email?, profile?: { phone?, bio?, avatar? } }
   * @returns {Promise<object>}
   */
  async updateProfile(data) {
    const response = await api.patch('/auth/me/', data);
    return response.data;
  },

  /**
   * 删除账号（服务端删除用户并清除 Cookie）
   * @returns {Promise<object>}
   */
  async deleteAccount() {
    const response = await api.delete('/auth/delete/');
    setAuthenticated(false);
    return response.data;
  },

  /**
   * 判断是否已登录（内存标记，避免 localStorage 存储任何 token）
   * @returns {boolean}
   */
  isAuthenticated() {
    return _authenticated;
  },
};

export default authService;
