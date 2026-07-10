import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import Profile from './pages/Profile'
import Login from './pages/Login'
import Signup from './pages/Signup'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

// Route guard for authenticated pages
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-darkBg transition-colors">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-brand-500"></div>
        <span className="text-xs text-slate-500 mt-4 font-semibold">Verifying session...</span>
      </div>
    )
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />
}

// Layout wrapper including the navigation bar
const MainLayout = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-darkBg text-slate-900 dark:text-slate-100 transition-colors duration-300">
      <Navbar />
      <main className="min-h-[calc(100vh-4rem)]">
        <Routes>
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
            {/* Protected Routes */}
            <Route path="/*" element={<MainLayout />} />
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}
