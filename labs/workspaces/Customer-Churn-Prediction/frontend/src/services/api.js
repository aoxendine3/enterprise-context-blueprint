import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 600000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('churn_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const token = localStorage.getItem('churn_token')
    const isLoginRequest = err.config?.url?.includes('/api/auth/login')
    if (err.response?.status === 401 && token && !isLoginRequest) {
      localStorage.removeItem('churn_token')
      localStorage.removeItem('churn_user')
      localStorage.removeItem('churn_active_page')
      window.location.assign('/')
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (data) => api.post('/api/auth/login', data),
  logout: () => api.post('/api/auth/logout'),
}

export const dashboardApi = { get: () => api.get('/api/dashboard') }

export const uploadApi = {
  // Do NOT manually set multipart Content-Type. Axios/browser will add the correct boundary.
  upload: (formData, onUploadProgress) =>
    api.post('/api/upload', formData, {
      headers: { 'Content-Type': undefined },
      timeout: 600000,
      onUploadProgress,
    }),
  validate: (formData) =>
    api.post('/api/upload/validate', formData, {
      headers: { 'Content-Type': undefined },
      timeout: 600000,
    }),
  downloadSample: () => `${BASE_URL}/api/upload/sample`,
}

export const predictApi = {
  predict: (data) => api.post('/api/predict', data),
  history: () => api.get('/api/predict/history'),
}

export const riskApi = { get: (params) => api.get('/api/risk-analysis', { params }) }
export const performanceApi = { get: () => api.get('/api/model-performance') }
export const retentionApi = { get: () => api.get('/api/retention') }
export const reportsApi = { download: (type) => api.get(`/api/reports/${type}`, { responseType: 'blob' }) }

export const settingsApi = {
  get: () => api.get('/api/settings'),
  update: (data) => api.put('/api/settings', data),
  changePassword: (data) => api.post('/api/settings/password', data),
  revealApiKey: () => api.get('/api/settings/api-key'),
  regenerateApiKey: () => api.post('/api/settings/api-key/regenerate'),
  getAttestationKey: () => api.get('/api/settings/attestation-key'),
}

export const safetyApi = {
  getPending: () => api.get('/api/safety/pending-reviews'),
  resolve: (id, data) => api.post(`/api/safety/pending-reviews/${id}/resolve`, data),
}

