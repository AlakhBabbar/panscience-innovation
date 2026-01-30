import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import LoginSignup from './pages/LoginSignup'
import Home from './pages/Home'
import './App.css'

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const location = useLocation()

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setIsAuthenticated(!!token)
    setIsChecking(false)
  }, [location])

  if (isChecking) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

// Public Route wrapper (redirects to home if already authenticated)
function PublicRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setIsAuthenticated(!!token)
    setIsChecking(false)
  }, [])

  if (isChecking) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  return isAuthenticated ? <Navigate to="/home" replace /> : children
}

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved !== null ? JSON.parse(saved) : true
  })

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
  }, [darkMode])

  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <LoginSignup darkMode={darkMode} setDarkMode={setDarkMode} />
            </PublicRoute>
          } 
        />
        <Route 
          path="/home" 
          element={
            <ProtectedRoute>
              <Home darkMode={darkMode} setDarkMode={setDarkMode} />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/" 
          element={<RootRedirect />} 
        />
      </Routes>
    </BrowserRouter>
  )
}

function RootRedirect() {
  const [destination, setDestination] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setDestination(token ? '/home' : '/login')
  }, [])

  if (!destination) {
    return (
      <div className="flex h-screen items-center justify-center bg-neutral-950">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  return <Navigate to={destination} replace />
}

export default App
