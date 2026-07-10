import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import { supabase } from '../services/supabase'
import api from '../services/api'
import { User, Mail, Calendar, Shield, Save, KeyRound, CheckCircle, BarChart3 } from 'lucide-react'

export default function Profile() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState({ type: '', text: '' })
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false)
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false)

  // Fetch full user profile details from backend /profile
  const { data: profileData, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await api.get('/profile')
      // Update local state when query loads
      if (res.data?.full_name) {
        setFullName(res.data.full_name)
      }
      return res.data
    }
  })

  // Update profile details handler
  const handleUpdateProfile = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    setIsUpdatingProfile(true)

    try {
      if (supabase) {
        const { error } = await supabase.auth.updateUser({
          data: { full_name: fullName }
        })
        if (error) throw error
      }
      
      // Update mock locally as fallback
      const cached = localStorage.getItem('mock_user')
      if (cached) {
        const parsed = JSON.parse(cached)
        parsed.full_name = fullName
        localStorage.setItem('mock_user', JSON.stringify(parsed))
      }

      setMessage({ type: 'success', text: 'Profile details updated successfully!' })
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Failed to update profile.' })
    } finally {
      setIsUpdatingProfile(false)
    }
  }

  // Update password handler
  const handleUpdatePassword = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })

    if (password !== confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match' })
      return
    }

    if (password.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters' })
      return
    }

    setIsUpdatingPassword(true)
    try {
      if (supabase) {
        const { error } = await supabase.auth.updateUser({
          password: password
        })
        if (error) throw error
      }
      setMessage({ type: 'success', text: 'Password changed successfully!' })
      setPassword('')
      setConfirmPassword('')
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Failed to change password.' })
    } finally {
      setIsUpdatingPassword(false)
    }
  }

  const creationDate = profileData?.created_at 
    ? new Date(profileData.created_at).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })
    : 'Loading...'

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Profile Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Manage your account details and password options.</p>
      </div>

      {message.text && (
        <div className={`flex items-center space-x-2 p-4 rounded-xl text-xs font-semibold ${
          message.type === 'success' 
            ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400' 
            : 'bg-rose-50 text-rose-800 dark:bg-rose-950/20 dark:text-rose-455'
        }`}>
          <CheckCircle className="w-4.5 h-4.5 shrink-0" />
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* User Card Summary */}
        <div className="md:col-span-1 glass-card p-6 flex flex-col items-center justify-center text-center space-y-4 h-fit">
          <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-brand-500 to-indigo-500 flex items-center justify-center text-white text-3xl font-bold shadow-lg shadow-brand-500/25">
            {fullName ? fullName.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-905 dark:text-slate-100">{fullName || 'Active User'}</h3>
            <p className="text-xs text-slate-500 font-semibold">{user?.email}</p>
          </div>
          <div className="w-full border-t border-slate-150 dark:border-darkBorder/40 pt-4 flex flex-col space-y-2 text-left">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Account Metadata</span>
            <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400">
              <Calendar className="w-4 h-4" />
              <span>Joined: {creationDate}</span>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400">
              <Shield className="w-4 h-4" />
              <span>Status: Authenticated</span>
            </div>
          </div>
        </div>

        {/* Action Panel Forms */}
        <div className="md:col-span-2 space-y-8">
          {/* Edit Profile Form */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="font-bold text-sm text-slate-805 dark:text-slate-200 flex items-center space-x-2">
              <User className="w-4.5 h-4.5 text-brand-650" />
              <span>Display Information</span>
            </h3>
            
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your Name"
                  className="input-field text-sm"
                  disabled={isLoading || isUpdatingProfile}
                />
              </div>

              <div className="space-y-1.5 opacity-70">
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Email Address (Read-only)</label>
                <div className="input-field bg-slate-100 dark:bg-slate-900 border-slate-200 text-slate-500 flex items-center space-x-2 text-sm">
                  <Mail className="w-4.5 h-4.5" />
                  <span>{user?.email}</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={isUpdatingProfile || isLoading}
                className="btn-primary flex items-center space-x-2 py-2.5 px-4 text-xs font-bold self-end"
              >
                <Save className="w-4 h-4" />
                <span>{isUpdatingProfile ? 'Saving...' : 'Save Profile'}</span>
              </button>
            </form>
          </div>

          {/* Change Password Form */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="font-bold text-sm text-slate-805 dark:text-slate-200 flex items-center space-x-2">
              <KeyRound className="w-4.5 h-4.5 text-brand-650" />
              <span>Security & Password</span>
            </h3>
            
            <form onSubmit={handleUpdatePassword} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">New Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="input-field text-sm"
                    disabled={isUpdatingPassword}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Confirm New Password</label>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="input-field text-sm"
                    disabled={isUpdatingPassword}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isUpdatingPassword || !password}
                className="btn-primary flex items-center space-x-2 py-2.5 px-4 text-xs font-bold"
              >
                <KeyRound className="w-4 h-4" />
                <span>{isUpdatingPassword ? 'Updating...' : 'Change Password'}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
