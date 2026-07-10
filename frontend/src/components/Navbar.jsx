import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Sun, Moon, Menu, X, LogOut, LayoutDashboard, History, User, Eye } from 'lucide-react'

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem('theme') === 'dark' || 
      (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
  })

  useEffect(() => {
    const root = window.document.documentElement
    if (isDark) {
      root.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const navLinks = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'History', path: '/history', icon: History },
    { name: 'Profile', path: '/profile', icon: User },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <nav className="sticky top-0 z-50 bg-white/80 dark:bg-darkBg/80 backdrop-blur-md border-b border-slate-200/50 dark:border-darkBorder/50 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-md shadow-brand-500/25">
              <Eye className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-brand-600 to-indigo-500 bg-clip-text text-transparent dark:from-brand-400 dark:to-indigo-300">
              YOLO-World
            </span>
          </Link>

          {/* Desktop Navigation */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center space-x-1">
              {navLinks.map((link) => {
                const Icon = link.icon
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                      isActive(link.path)
                        ? 'bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-400 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{link.name}</span>
                  </Link>
                )
              })}
            </div>
          )}

          {/* Right Controls */}
          <div className="flex items-center space-x-3">
            {/* Theme Toggle */}
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2.5 rounded-xl border border-slate-200/50 hover:bg-slate-50 text-slate-500 dark:border-darkBorder/50 dark:hover:bg-slate-850 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4.5 h-4.5" /> : <Moon className="w-4.5 h-4.5" />}
            </button>

            {isAuthenticated && (
              <>
                {/* Profile Display */}
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-semibold text-slate-850 dark:text-slate-200">
                    {user?.full_name || 'User'}
                  </span>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 max-w-[150px] truncate">
                    {user?.email}
                  </span>
                </div>

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="hidden md:flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-sm font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/20 transition-colors"
                >
                  <LogOut className="w-4.5 h-4.5" />
                  <span>Logout</span>
                </button>
              </>
            )}

            {/* Mobile Menu Toggle */}
            {isAuthenticated && (
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="md:hidden p-2 rounded-xl text-slate-650 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800/40 transition-colors"
              >
                {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {isAuthenticated && isOpen && (
        <div className="md:hidden border-t border-slate-200/50 dark:border-darkBorder/50 bg-white dark:bg-darkBg transition-colors duration-300">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navLinks.map((link) => {
              const Icon = link.icon
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium ${
                    isActive(link.path)
                      ? 'bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-400'
                      : 'text-slate-650 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{link.name}</span>
                </Link>
              )
            })}
            <button
              onClick={() => {
                setIsOpen(false)
                handleLogout()
              }}
              className="flex w-full items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/20"
            >
              <LogOut className="w-5 h-5" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  )
}
