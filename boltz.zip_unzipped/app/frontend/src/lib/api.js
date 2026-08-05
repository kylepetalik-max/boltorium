import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
export const API_BASE = `${BACKEND_URL}/api`;

export const MAPBOX_TOKEN = 'pk.eyJ1Ijoia2l2bzAzIiwiYSI6ImNtbmtxNHkzYzExaGoycm9nNDFqbWs1NjcifQ.xpdk0Clp_J3GeyO1GFE3fQ';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rmr_session_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e?.response?.status === 401 && !window.location.pathname.includes('/auth/callback') && window.location.pathname !== '/') {
      // session invalid — clear and go to landing
      localStorage.removeItem('rmr_session_token');
    }
    return Promise.reject(e);
  }
);

export default api;
