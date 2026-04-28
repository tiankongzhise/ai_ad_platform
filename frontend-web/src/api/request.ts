/**
 * Axios 实例封装
 * 统一处理请求拦截、响应拦截、错误处理
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { message } from 'antd';

// 创建 Axios 实例
const axiosInstance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // 处理 401 未授权
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return axiosInstance(originalRequest);
        } catch (refreshError) {
          // 刷新失败，跳转登录
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }

    // 处理其他错误
    if (error.response?.status === 403) {
      message.error('无权限访问');
    } else if (error.response?.status === 404) {
      message.error('资源不存在');
    } else if (error.response?.status >= 500) {
      message.error('服务器错误，请稍后重试');
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
