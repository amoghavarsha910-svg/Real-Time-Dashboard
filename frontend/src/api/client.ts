import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/authStore';

const apiClient = axios.create({
  baseURL: '/api',
  withCredentials: true, // send httpOnly refresh-token cookie automatically
});

// ---------------------------------------------------------------------------
// Request interceptor — attach access token from memory store
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — silent token refresh on 401
// ---------------------------------------------------------------------------
let _isRefreshing = false;
let _pendingQueue: Array<{
  resolve: (value: string) => void;
  reject: (reason: unknown) => void;
}> = [];

function _flushQueue(token: string | null, error: unknown) {
  _pendingQueue.forEach(({ resolve, reject }) => {
    if (token) resolve(token);
    else reject(error);
  });
  _pendingQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (_isRefreshing) {
      // Queue this request until the refresh resolves
      return new Promise((resolve, reject) => {
        _pendingQueue.push({
          resolve: (token) => {
            originalRequest.headers.set('Authorization', `Bearer ${token}`);
            resolve(apiClient(originalRequest));
          },
          reject,
        });
      });
    }

    originalRequest._retry = true;
    _isRefreshing = true;

    try {
      const { data } = await axios.post<{ access_token: string }>(
        '/api/auth/refresh',
        {},
        { withCredentials: true },
      );
      const newToken = data.access_token;
      useAuthStore.getState().setToken(newToken);
      _flushQueue(newToken, null);
      originalRequest.headers.set('Authorization', `Bearer ${newToken}`);
      return apiClient(originalRequest);
    } catch (refreshError) {
      _flushQueue(null, refreshError);
      useAuthStore.getState().clearAuth();
      return Promise.reject(refreshError);
    } finally {
      _isRefreshing = false;
    }
  },
);

export default apiClient;
