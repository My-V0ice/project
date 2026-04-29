import axios from 'axios'
import { getAccessToken, setAccessToken } from '../utils/authToken'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    setAccessToken(token)
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
