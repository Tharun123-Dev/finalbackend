import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_LAP_API_BASE
  ? `${import.meta.env.VITE_LAP_API_BASE}/api`
  : (import.meta.env.VITE_API_BASE ? `${import.meta.env.VITE_API_BASE}/api` : '/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;


