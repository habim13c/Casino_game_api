import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) { setLoading(false); return; }
      const { data } = await axios.get(`${API}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      setUser(data);
    } catch {
      localStorage.removeItem('token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  const login = async (email, password) => {
    const { data } = await axios.post(`${API}/api/auth/login`, { email, password }, { withCredentials: true });
    if (data.token) localStorage.setItem('token', data.token);
    setUser(data);
    return data;
  };

  const register = async (email, password, name) => {
    const { data } = await axios.post(`${API}/api/auth/register`, { email, password, name }, { withCredentials: true });
    if (data.token) localStorage.setItem('token', data.token);
    setUser(data);
    return data;
  };

  const logout = async () => {
    try { await axios.post(`${API}/api/auth/logout`, {}, { withCredentials: true }); } catch {}
    localStorage.removeItem('token');
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem('token');
      const { data } = await axios.get(`${API}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      setUser(data);
    } catch {}
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function apiHeaders() {
  const token = localStorage.getItem('token');
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
}

export { API };
