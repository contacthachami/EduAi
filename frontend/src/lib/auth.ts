import { create } from "zustand";
import axios from "axios";

export const api = axios.create({ baseURL: "/", timeout: 60_000 });

// Inject auth token on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("eduai_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface User {
  id: string;
  name: string;
  email: string;
  plan: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => Promise<void>;
}

export const useAuth = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  loading: true,

  login: async (email, password) => {
    const res = await api.post("/api/auth/login", { email, password });
    const { token, user } = res.data;
    localStorage.setItem("eduai_token", token);
    set({ token, user, loading: false });
  },

  register: async (name, email, password) => {
    const res = await api.post("/api/auth/register", { name, email, password });
    const { token, user } = res.data;
    localStorage.setItem("eduai_token", token);
    set({ token, user, loading: false });
  },

  logout: () => {
    localStorage.removeItem("eduai_token");
    set({ token: null, user: null, loading: false });
  },

  loadFromStorage: async () => {
    const token = localStorage.getItem("eduai_token");
    if (!token) {
      set({ loading: false });
      return;
    }
    try {
      const res = await api.get("/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      set({ token, user: res.data, loading: false });
    } catch {
      localStorage.removeItem("eduai_token");
      set({ token: null, user: null, loading: false });
    }
  },
}));
