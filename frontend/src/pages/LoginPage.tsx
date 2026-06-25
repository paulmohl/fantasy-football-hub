import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mail } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/auth'

type AuthMode = 'signin' | 'register' | 'post-register' | 'forgot-password'

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const [mode, setMode] = useState<AuthMode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [resetEmail, setResetEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resetSent, setResetSent] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (mode === 'register') {
        await api.post('/auth/register', { email, password })
        setMode('post-register')
      } else {
        const { data } = await api.post('/auth/login', { email, password })
        setAuth(data.access_token, data.user_id)
        navigate('/connect', { replace: true })
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSendReset(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/forgot-password', { email: resetEmail })
    } catch {
      // Always show success — server returns 200 regardless (no enumeration)
    } finally {
      setResetSent(true)
      setLoading(false)
    }
  }

  if (mode === 'post-register') {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center space-y-4">
          <Mail className="mx-auto text-muted" size={48} strokeWidth={1.5} />
          <h1 className="text-2xl font-semibold text-text">Check your email</h1>
          <p className="text-sm text-muted">
            We sent a verification link to <span className="text-text">{email}</span>.
            Click the link to activate your account.
          </p>
          <button
            onClick={() => api.post('/auth/resend-verification', { email }).catch(() => {})}
            className="text-accent text-sm hover:underline"
          >
            Resend verification email
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center">
          <span className="text-base font-semibold text-text">FantasyHub</span>
        </div>

        {/* Google OAuth button (above form per UI-SPEC) */}
        <button
          type="button"
          onClick={() => { window.location.href = '/api/v1/auth/google' }}
          className="bg-surface border border-border rounded-lg px-4 py-3 w-full flex items-center gap-3 min-h-[44px] hover:border-accent transition-colors"
          aria-label="Continue with Google"
        >
          <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden="true">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          <span className="text-sm font-semibold text-text">Continue with Google</span>
        </button>

        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs text-muted">or</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Email/password form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm text-text mb-1">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
              aria-describedby={error ? 'auth-error' : undefined}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm text-text mb-1">Password</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
            />
            {mode === 'signin' && !resetSent && (
              <div className="text-right mt-1">
                <button
                  type="button"
                  onClick={() => setMode('forgot-password')}
                  className="text-accent text-sm hover:underline"
                >
                  Forgot password?
                </button>
              </div>
            )}
          </div>

          {/* Inline forgot password panel */}
          {mode === 'forgot-password' && (
            <form onSubmit={handleSendReset} className="space-y-3 bg-raised border border-border rounded-lg p-4">
              <label htmlFor="reset-email" className="block text-sm text-text">
                Enter your email to reset password
              </label>
              <input
                id="reset-email"
                type="email"
                required
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-bg border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent min-h-[44px]"
              />
              {resetSent ? (
                <p className="text-sm text-muted">Reset link sent — check your inbox.</p>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors"
                >
                  {loading ? 'Please wait…' : 'Send Reset Link'}
                </button>
              )}
              <button
                type="button"
                onClick={() => { setMode('signin'); setResetSent(false) }}
                className="text-muted text-sm hover:text-text"
              >
                Cancel
              </button>
            </form>
          )}

          {error && (
            <p id="auth-error" role="alert" className="text-danger text-sm bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || mode === 'forgot-password'}
            className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors"
          >
            {loading ? 'Please wait…' : mode === 'register' ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        {/* Toggle between sign in and register */}
        <p className="text-center text-sm text-muted">
          {mode === 'signin' || mode === 'forgot-password' ? (
            <>Don&apos;t have an account?{' '}
              <button
                onClick={() => { setMode('register'); setError(null) }}
                className="text-accent hover:underline"
              >
                Create one
              </button>
            </>
          ) : (
            <>Already have an account?{' '}
              <button
                onClick={() => { setMode('signin'); setError(null) }}
                className="text-accent hover:underline"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  )
}
