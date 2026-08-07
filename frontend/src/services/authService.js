import api from './api';

export const authService = {
  /**
   * 用户登录
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{access: string, refresh: string}>}
   */
  async login(username, password) {
    const response = await api.post('/token/', { username, password });
    const { access, refresh } = response.data;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    return response.data;
  },

  /**
   * 用户注册
   * @param {object} data - { username, email, password, password2 }
   * @returns {Promise<{access: string, refresh: string, user: object}>}
   */
  async register(data) {
    const response = await api.post('/auth/register/', data);
    const { access, refresh } = response.data;
    if (access && refresh) {
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
    }
    return response.data;
  },

  /**
   * 退出登录
   */
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  /**
   * 获取当前用户信息
   * @returns {Promise<object>}
   */
  async getCurrentUser() {
    const response = await api.get('/auth/me/');
    return response.data;
  },

  /**
   * 检查登录状态
   * @returns {Promise<{is_authenticated: boolean, user: object|null}>}
   */
  async checkAuth() {
    try {
      const response = await api.get('/auth/check/');
      return response.data;
    } catch {
      return { is_authenticated: false, user: null };
    }
  },

  /**
   * 更新用户资料
   * @param {object} data
   * @returns {Promise<object>}
   */
  async updateProfile(data) {
    const response = await api.patch('/auth/me/', data);
    return response.data;
  },

  /**
   * 删除账号
   * @returns {Promise<object>}
   */
  async deleteAccount() {
    const response = await api.delete('/auth/delete/');
    this.logout();
    return response.data;
  },

  /**
   * 判断是否已登录
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },
};

export default authService;
