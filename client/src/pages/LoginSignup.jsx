import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { register, login } from '../services/api'

function LoginSignup({ darkMode, setDarkMode }) {
  const [authMode, setAuthMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const navigate = useNavigate()

  const handleAuth = async (e) => {
    e.preventDefault()
    setAuthError('')

    if (authMode === 'signup') {
      if (!username.trim()) {
        setAuthError('Username is required')
        return
      }
      if (password !== confirmPassword) {
        setAuthError('Passwords do not match')
        return
      }
    }

    try {
      if (authMode === 'signup') {
        await register(email, username, password)
      }

      const token = await login(email, password)
      localStorage.setItem('auth_token', token)
      navigate('/home')
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Authentication failed')
    }
  }

  return (
    <div className={`flex h-screen items-center justify-center ${darkMode ? 'bg-neutral-950 text-white' : 'bg-gray-50 text-gray-900'}`}>
      <div className={`w-full max-w-md rounded-2xl border p-6 ${darkMode ? 'bg-neutral-900 border-neutral-800' : 'bg-white border-gray-300'}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="font-semibold text-lg">PanScience</div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-neutral-800' : 'hover:bg-gray-100'}`}
            title="Toggle theme"
            type="button"
          >
            {darkMode ? <Sun size={20} className="text-white" /> : <Moon size={20} className="text-gray-600" />}
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => setAuthMode('login')}
            className={`flex-1 px-3 py-2 rounded-lg text-sm ${
              authMode === 'login'
                ? (darkMode ? 'bg-white text-black' : 'bg-gray-900 text-white')
                : (darkMode ? 'hover:bg-neutral-800' : 'hover:bg-gray-200')
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setAuthMode('signup')}
            className={`flex-1 px-3 py-2 rounded-lg text-sm ${
              authMode === 'signup'
                ? (darkMode ? 'bg-white text-black' : 'bg-gray-900 text-white')
                : (darkMode ? 'hover:bg-neutral-800' : 'hover:bg-gray-200')
            }`}
          >
            Sign Up
          </button>
        </div>

        {authError && (
          <div className={`mb-3 text-sm ${darkMode ? 'text-red-300' : 'text-red-700'}`} role="alert">
            {authError}
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-3">
          {authMode === 'signup' && (
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              className={`w-full px-3 py-2 rounded-lg border outline-none ${
                darkMode
                  ? 'bg-neutral-900 border-neutral-700 text-white placeholder-gray-500'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              required
            />
          )}
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className={`w-full px-3 py-2 rounded-lg border outline-none ${
              darkMode
                ? 'bg-neutral-900 border-neutral-700 text-white placeholder-gray-500'
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            }`}
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className={`w-full px-3 py-2 rounded-lg border outline-none ${
              darkMode
                ? 'bg-neutral-900 border-neutral-700 text-white placeholder-gray-500'
                : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
            }`}
            required
          />

          {authMode === 'signup' && (
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              className={`w-full px-3 py-2 rounded-lg border outline-none ${
                darkMode
                  ? 'bg-neutral-900 border-neutral-700 text-white placeholder-gray-500'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              required
            />
          )}
          <button
            type="submit"
            className={`w-full px-3 py-2 rounded-lg ${darkMode ? 'bg-white text-black hover:bg-gray-200' : 'bg-gray-900 text-white hover:bg-gray-800'}`}
          >
            {authMode === 'signup' ? 'Create account' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginSignup
