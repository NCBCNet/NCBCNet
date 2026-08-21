import axios from 'axios';

/**
 * 从 document.cookie 中读取指定名称的 Cookie 值。
 * @param {string} name Cookie 名称
 * @returns {string|null}
 */
export function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
});

// 请求拦截器：Cookie 认证 + CSRF
// 认证凭据存放在 HttpOnly Cookie（nc_access / nc_refresh）中，浏览器自动携带，
// 前端不再读写任何 token。所有不安全请求（POST/PUT/PATCH/DELETE）都需要
// 从可读的 csrftoken Cookie 中取值并回填 X-CSRFToken 请求头。
api.interceptors.request.use(
  (config) => {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// 不应触发“刷新后重试”的端点（登录 / 刷新本身）
const SKIP_REFRESH_PATHS = ['/auth/login/', '/auth/refresh/'];

// 清理旧 JWT 方案遗留的 localStorage 状态（新方案不使用 token）
function clearLegacyAuthState() {
  try {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  } catch {
    // 忽略清理失败
  }
}

// 共享的在途刷新 Promise：并发 401 只触发一次刷新
let refreshPromise = null;

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = api
      .post('/auth/refresh/')
      .then((response) => response.data)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

// 响应拦截器：401 时自动刷新 Cookie 并重试一次；刷新失败则清理状态并跳转登录
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!originalRequest || error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    const url = originalRequest.url || '';

    // 登录 / 刷新接口自身的 401 直接抛出，交由调用方处理（如登录失败提示）
    if (SKIP_REFRESH_PATHS.some((path) => url.startsWith(path))) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      // 共享在途刷新：多个并发 401 只调用一次 /auth/refresh/
      await refreshAccessToken();
      // 刷新成功后重试原始请求一次（请求拦截器会重新读取最新的 csrftoken Cookie）
      return api(originalRequest);
    } catch (refreshError) {
      // 认证相关接口（me/check/csrf 等）的 401 表示“未登录/会话已过期”，
      // 由调用方（如 authStore）自行处理为匿名状态，不强制跳转登录页，
      // 避免匿名访客浏览公开页面时被重定向。
      if (url.startsWith('/auth/')) {
        return Promise.reject(refreshError);
      }
      // 其余受保护接口刷新失败：清理状态并跳转登录
      clearLegacyAuthState();
      window.location.assign('/usermanage/login');
      return Promise.reject(refreshError);
    }
  },
);

export default api;
