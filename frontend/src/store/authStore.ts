import { create } from 'zustand';
import axios from 'axios';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'SystemAdmin' | 'OrgAdmin' | 'Coordinator' | 'Member' | 'Auditor';
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<{ message: string; token?: string }>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api/v1';

// Custom clean Axios instance to avoid circular dependency with api.ts configuration
const authClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const useAuthStore = create<AuthState>((set, get) => {
  // Pull existing session settings from local storage
  const savedToken = localStorage.getItem('aip_token');
  const savedUser = localStorage.getItem('aip_user');
  
  let initialUser: User | null = null;
  if (savedUser) {
    try {
      initialUser = JSON.parse(savedUser);
    } catch {
      localStorage.removeItem('aip_user');
    }
  }

  return {
    user: initialUser,
    token: savedToken,
    isAuthenticated: !!savedToken,
    isLoading: false,
    error: null,

    login: async (email, password) => {
      set({ isLoading: true, error: null });
      try {
        const response = await authClient.post('/auth/login', { email, password });
        const { access_token, user } = response.data;
        
        localStorage.setItem('aip_token', access_token);
        localStorage.setItem('aip_user', JSON.stringify(user));
        
        set({
          token: access_token,
          user,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch (err: any) {
        const errMsg = err.response?.data?.detail || 'Login failed. Please verify your credentials.';
        set({ error: errMsg, isLoading: false });
        throw new Error(errMsg);
      }
    },

    logout: () => {
      localStorage.removeItem('aip_token');
      localStorage.removeItem('aip_user');
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        error: null,
      });
    },

    forgotPassword: async (email) => {
      set({ isLoading: true, error: null });
      try {
        const response = await authClient.post('/auth/forgot-password', { email });
        set({ isLoading: false });
        return response.data;
      } catch (err: any) {
        const errMsg = err.response?.data?.detail || 'Failed to initiate password reset request.';
        set({ error: errMsg, isLoading: false });
        throw new Error(errMsg);
      }
    },

    resetPassword: async (token, newPassword) => {
      set({ isLoading: true, error: null });
      try {
        await authClient.post('/auth/reset-password', {
          token,
          new_password: newPassword,
          confirm_password: newPassword,
        });
        set({ isLoading: false });
      } catch (err: any) {
        const errMsg = err.response?.data?.detail || 'Failed to reset password.';
        set({ error: errMsg, isLoading: false });
        throw new Error(errMsg);
      }
    },

    fetchCurrentUser: async () => {
      const { token } = get();
      if (!token) return;
      
      set({ isLoading: true, error: null });
      try {
        const response = await authClient.get('/auth/me', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const user = response.data;
        localStorage.setItem('aip_user', JSON.stringify(user));
        set({ user, isAuthenticated: true, isLoading: false });
      } catch (err: any) {
        localStorage.removeItem('aip_token');
        localStorage.removeItem('aip_user');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    },

    clearError: () => set({ error: null }),
  };
});
