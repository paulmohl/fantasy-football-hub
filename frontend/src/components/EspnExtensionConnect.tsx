import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import {
  EspnExtensionError,
  getProbeDetail,
  isInstalled,
  requestCookies,
  type EspnCookies,
  type EspnExtensionErrorCode,
} from '@/lib/espnExtension'

const EXTENSION_STORE_URL = import.meta.env.VITE_ESPN_EXTENSION_URL as string | undefined

type Phase = 'checking' | 'not_installed' | 'ready' | 'waiting' | 'pick' | 'manual' | 'connecting'

interface FanLeague {
  league_id: string
  name: string
  season: number
}

const EXTENSION_MESSAGES: Record<EspnExtensionErrorCode, string> = {
  not_installed: 'The ESPN extension is not installed yet.',
  denied: 'You declined access. Try again when you are ready.',
  not_signed_in: 'Sign in to ESPN in the tab we just opened, then try again.',
  busy: 'An approval request is already waiting — check the extension popup.',
  unreachable: 'Could not reach the extension. Reload this page and try again.',
}

function detailOf(err: unknown, fallback: string): string {
  return (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? fallback
}

interface Props {
  onConnected: () => void
  onAdvanced: () => void
}

export default function EspnExtensionConnect({ onConnected, onAdvanced }: Props) {
  const [phase, setPhase] = useState<Phase>('checking')
  const [cookies, setCookies] = useState<EspnCookies | null>(null)
  const [leagues, setLeagues] = useState<FanLeague[]>([])
  const [leagueId, setLeagueId] = useState('')
  const [error, setError] = useState('')
  const [probeDetail, setProbeDetail] = useState('')

  async function detect() {
    setPhase('checking')
    let installed = false
    try {
      installed = await isInstalled()
    } catch {
      installed = false
    }
    setProbeDetail(getProbeDetail())
    setPhase(installed ? 'ready' : 'not_installed')
  }

  useEffect(() => {
    void detect()
  }, [])

  async function handleConnect() {
    setError('')
    setPhase('waiting')
    let granted: EspnCookies
    try {
      granted = await requestCookies()
    } catch (err) {
      if (err instanceof EspnExtensionError && err.code === 'not_installed') {
        setPhase('not_installed')
        return
      }
      setError(err instanceof EspnExtensionError ? EXTENSION_MESSAGES[err.code] : EXTENSION_MESSAGES.unreachable)
      setPhase('ready')
      return
    }
    setCookies(granted)
    try {
      const { data } = await api.post('/espn/leagues', granted)
      const found = (data?.leagues ?? []) as FanLeague[]
      setLeagues(found)
      setPhase(found.length > 0 ? 'pick' : 'manual')
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401) {
        setError(detailOf(err, 'ESPN rejected the cookies. Sign in to ESPN and try again.'))
        setPhase('ready')
        return
      }
      setPhase('manual')
    }
  }

  async function connectLeague(id: string) {
    if (!cookies || !id.trim()) return
    setError('')
    setPhase('connecting')
    try {
      await api.post('/espn/connect', { ...cookies, league_id: id.trim() })
      onConnected()
    } catch (err) {
      setError(detailOf(err, 'ESPN connection failed. Please try again.'))
      setPhase(leagues.length > 0 ? 'pick' : 'manual')
    }
  }

  const buttonClass =
    'w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors'

  return (
    <div className="space-y-3">
      <div className="bg-raised border border-border rounded-lg p-4 space-y-2">
        <p className="text-sm font-semibold text-text">Link your ESPN account</p>
        <p className="text-sm text-muted">
          A small browser extension asks for your permission once, then lets Fantasy Hub read your
          ESPN leagues. Your ESPN password is never shared.
        </p>
      </div>

      {phase === 'checking' && <p className="text-sm text-muted text-center">Looking for the extension…</p>}

      {phase === 'not_installed' && (
        <div className="space-y-2">
          {EXTENSION_STORE_URL ? (
            <a href={EXTENSION_STORE_URL} target="_blank" rel="noopener noreferrer" className={`${buttonClass} block text-center`}>
              Install the extension →
            </a>
          ) : (
            <p className="text-sm text-text">Install the extension, then come back here.</p>
          )}
          <button onClick={() => void detect()} className="text-sm text-accent underline w-full text-center">
            Check again
          </button>
          {probeDetail && <p className="text-xs text-muted break-all text-center">Detection: {probeDetail}</p>}
        </div>
      )}

      {(phase === 'ready' || phase === 'waiting') && (
        <div className="space-y-2">
          {error && <p className="text-sm text-danger">{error}</p>}
          <button onClick={() => void handleConnect()} disabled={phase === 'waiting'} className={buttonClass}>
            {phase === 'waiting' ? 'Waiting for approval…' : 'Connect ESPN →'}
          </button>
        </div>
      )}

      {phase === 'pick' && (
        <div className="space-y-2">
          <p className="text-sm text-text">Which league?</p>
          {error && <p className="text-sm text-danger">{error}</p>}
          {leagues.map((l) => (
            <button
              key={l.league_id}
              onClick={() => void connectLeague(l.league_id)}
              className="w-full text-left bg-raised border border-border rounded-lg px-4 py-3 min-h-[44px] text-text hover:border-accent transition-colors"
            >
              {l.name}
            </button>
          ))}
        </div>
      )}

      {(phase === 'manual' || (phase === 'connecting' && leagues.length === 0)) && (
        <div className="space-y-2">
          <p className="text-sm text-muted">
            We could not list your leagues automatically. Enter the League ID from your ESPN league URL.
          </p>
          <label htmlFor="espn-league-id" className="block text-xs text-muted ml-0.5">League ID</label>
          <input
            id="espn-league-id"
            value={leagueId}
            onChange={(e) => setLeagueId(e.target.value)}
            placeholder="e.g. 336584"
            className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
          />
          {error && <p className="text-sm text-danger">{error}</p>}
          <button
            onClick={() => void connectLeague(leagueId)}
            disabled={phase === 'connecting' || !leagueId.trim()}
            className={buttonClass}
          >
            {phase === 'connecting' ? 'Connecting…' : 'Connect league →'}
          </button>
        </div>
      )}

      {phase === 'connecting' && leagues.length > 0 && (
        <p className="text-sm text-muted text-center">Connecting…</p>
      )}

      <button onClick={onAdvanced} className="text-xs text-muted underline w-full text-center">
        Advanced: enter cookies manually
      </button>
    </div>
  )
}
