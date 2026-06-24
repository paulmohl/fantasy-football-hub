import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/LoginPage'
import ConnectPage from '@/pages/ConnectPage'
import TeamPage from '@/pages/TeamPage'
import DraftPage from '@/pages/DraftPage'
import TradePage from '@/pages/TradePage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
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

export default function App() {
  return (
    <BrowserRouter>
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
