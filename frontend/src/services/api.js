import axios from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

api.interceptors.request.use(
  async (config) => {
    // Fetch the token from Supabase session if initialized
    if (supabase) {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.access_token) {
          config.headers.Authorization = `Bearer ${session.access_token}`
        }
      } catch (err) {
        console.error("Error retrieving Supabase session in interceptor:", err)
      }
    } else {
      // Fallback bearer token for mock development modes
      const cachedToken = localStorage.getItem('mock_token')
      if (cachedToken) {
        config.headers.Authorization = `Bearer ${cachedToken}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default api
