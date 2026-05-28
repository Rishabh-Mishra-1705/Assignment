import axios from 'axios';

// Set VITE_API_URL in .env.local or Vercel env vars
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

// ── Uploads ────────────────────────────────────────────────────────────────────
export const uploadSAP = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return api.post('/upload/sap/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};

export const uploadUtility = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return api.post('/upload/utility/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};

export const uploadTravel = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return api.post('/upload/travel/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
};

export const fetchUploadHistory = () => api.get('/uploads/');

// ── Records ────────────────────────────────────────────────────────────────────
export const fetchRecords = (params = {}) => api.get('/records/', { params });
export const fetchRecord = (id) => api.get(`/records/${id}/`);
export const updateRecord = (id, data) => api.patch(`/records/${id}/`, data);
export const approveRecord = (id, note = '') => api.post(`/records/${id}/approve/`, { note });
export const rejectRecord = (id, reason) => api.post(`/records/${id}/reject/`, { reason });
export const lockRecord = (id) => api.post(`/records/${id}/lock/`);
export const bulkApprove = (ids) => api.post('/records/bulk-approve/', { ids });

// ── Dashboard ──────────────────────────────────────────────────────────────────
export const fetchDashboardStats = () => api.get('/dashboard/stats/');

export default api;