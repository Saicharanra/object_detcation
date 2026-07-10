import React, { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '../services/supabase'
import api from '../services/api'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState({
    id: '00000000-0000-0000-0000-000000000000',
    email: 'guest@example.com',
    full_name: 'Guest User'
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(false)
  }, [])

  const signup = async (email, password, fullName) => {
    return { user }
  }

  const login = async (email, password) => {
    return { user }
  }

  const logout = async () => {
    // No-op for guest mode
  }

  const resetPassword = async (email) => {
    // No-op for guest mode
  }

  return (
    <AuthContext.Provider value={{ user, loading, signup, login, logout, resetPassword, isAuthenticated: true }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
