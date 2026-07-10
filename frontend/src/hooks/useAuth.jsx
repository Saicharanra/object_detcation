import React, { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '../services/supabase'
import api from '../services/api'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (supabase) {
      // 1. Initial session load
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session?.user) {
          setUser({
            id: session.user.id,
            email: session.user.email,
            full_name: session.user.user_metadata?.full_name || ''
          })
        } else {
          setUser(null)
        }
        setLoading(false)
      })

      // 2. Auth state change listener
      const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
        if (session?.user) {
          setUser({
            id: session.user.id,
            email: session.user.email,
            full_name: session.user.user_metadata?.full_name || ''
          })
        } else {
          setUser(null)
        }
        setLoading(false)
      })

      return () => {
        subscription?.unsubscribe()
      }
    } else {
      // Mock mode initialization
      const mockUser = localStorage.getItem('mock_user')
      if (mockUser) {
        setUser(JSON.parse(mockUser))
      }
      setLoading(false)
    }
  }, [])

  const signup = async (email, password, fullName) => {
    setLoading(true)
    try {
      if (supabase) {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { full_name: fullName }
          }
        })
        if (error) throw error
        
        // Also call backend to register profile (if trigger is delayed or for db logging)
        try {
          await api.post('/auth/signup', { email, password, full_name: fullName })
        } catch (backendError) {
          console.warn("Backend profile sync note:", backendError)
        }

        if (data.session?.user) {
          setUser({
            id: data.session.user.id,
            email: data.session.user.email,
            full_name: fullName
          })
        }
        return data
      } else {
        // Mock signup
        const mockId = 'mock-uid-12345'
        const mockProfile = { id: mockId, email, full_name: fullName }
        localStorage.setItem('mock_user', JSON.stringify(mockProfile))
        localStorage.setItem('mock_token', 'mock-jwt-token')
        setUser(mockProfile)
        
        // Register in local SQLite via mock call
        try {
          await api.post('/auth/signup', { email, password, full_name: fullName })
        } catch (err) {
          console.error(err)
        }
        return { user: mockProfile }
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    setLoading(true)
    try {
      if (supabase) {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password
        })
        if (error) throw error
        
        // Sync login session details
        if (data.user) {
          setUser({
            id: data.user.id,
            email: data.user.email,
            full_name: data.user.user_metadata?.full_name || ''
          })
        }
        return data
      } else {
        // Mock login
        const mockProfile = { id: 'mock-uid-12345', email, full_name: 'Mock User' }
        localStorage.setItem('mock_user', JSON.stringify(mockProfile))
        localStorage.setItem('mock_token', 'mock-jwt-token')
        setUser(mockProfile)
        
        // Send login to backend
        try {
          await api.post('/auth/login', { email, password })
        } catch (err) {
          console.error(err)
        }
        return { user: mockProfile }
      }
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      if (supabase) {
        const { error } = await supabase.auth.signOut()
        if (error) throw error
      } else {
        localStorage.removeItem('mock_user')
        localStorage.removeItem('mock_token')
      }
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const resetPassword = async (email) => {
    if (supabase) {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`
      })
      if (error) throw error
    } else {
      console.log(`Mock reset password email sent to ${email}`)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, signup, login, logout, resetPassword, isAuthenticated: !!user }}>
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
