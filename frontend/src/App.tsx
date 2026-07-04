import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useToast } from '@/components/ui/Toast'
import { api } from '@/lib/api'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/LoginPage'
import ConnectPage from '@/pages/ConnectPage'
import TeamPage from '@/pages/TeamPage'
import DraftPage from '@/pages/DraftPage'
import TradePage from '@/pages/TradePage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const setHasLeagues = useAuthStore((s) => s.setHasLeagues)
  const setUnhealthyPlatforms = useAuthStore((s) => s.setUnhealthyPlatforms)
  const { toast } = useToast()

  useEffect(() => {
    if (!token) return
    fetch('/api/v1/users/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return
        setHasLeagues(data.has_leagues)
        const unhealthy = (data.credential_health ?? [])
          .filter((c: { platform: string; is_healthy: boolean }) => !c.is_healthy)
          .map((c: { platform: string }) => c.platform)
        setUnhealthyPlatforms(unhealthy)
      })
      .catch(() => {})

    // Notification fetch — in-app notification for scheduled drafts (DR-01)
    api
      .get('/notifications')
      .then((res) => {
        const notifications: Array<{ type: string; message: string }> = res.data
        notifications.forEach((n) => {
          toast(n.message, 'info')
        })
      })
      .catch(() => {})
  }, [token])

  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireLeague({ children }: { children: React.ReactNode }) {
  const hasLeagues = useAuthStore((s) => s.hasLeagues)
  if (!hasLeagues) return <Navigate to="/connect" replace />
  return <>{children}</>
}

function AuthCallback() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  useEffect(() => {
    const token = params.get('token')
    const userId = params.get('user_id')
    if (token && userId) {
      setAuth(token, userId)
      navigate('/connect', { replace: true })
    } else {
      navigate('/login', { replace: true })
    }
  }, [])

  return null
}

function RateLimitListener() {
  const { toast } = useToast()
  useEffect(() => {
    const handler = (e: CustomEvent<{ platform: string }>) => {
      toast(`${e.detail.platform} data rate-limited — showing cached results`, 'info')
    }
    window.addEventListener('rate-limited', handler as EventListener)
    return () => window.removeEventListener('rate-limited', handler as EventListener)
  }, [toast])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <RateLimitListener />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/team" replace />} />
          <Route path="connect" element={<ConnectPage />} />
          <Route path="team" element={<RequireLeague><TeamPage /></RequireLeague>} />
          <Route path="draft" element={<RequireLeague><DraftPage /></RequireLeague>} />
          <Route path="trades" element={<RequireLeague><TradePage /></RequireLeague>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
