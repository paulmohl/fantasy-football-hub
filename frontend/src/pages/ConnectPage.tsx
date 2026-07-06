import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import { ChatBubble } from '@/components/ui/ChatBubble'
import { TypingIndicator } from '@/components/ui/TypingIndicator'
import { OptionPill } from '@/components/ui/OptionPill'
import { LeagueCard } from '@/components/ui/LeagueCard'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { ConnectionCard } from '@/components/ui/ConnectionCard'
import { PlatformIcon } from '@/components/ui/PlatformIcon'
import { cn } from '@/lib/utils'
import { EspnCookieNative, isNative } from '@/plugins/espn-cookie'

type Step = 'platform' | 'username' | 'leagues' | 'importing' | 'done' | 'espn_type' | 'espn_private' | 'espn_public' | 'yahoo_connected'

interface BubbleEntry {
  id: string
  type: 'app' | 'user' | 'typing' | 'loading'
  content: React.ReactNode
}

interface SleeperLeague {
  league_id: string
  name: string
  season: string
  total_rosters: number
  settings?: { type?: string; num_keepers?: number }
}

interface ConnectedLeague {
  id: string
  name: string
  season: string
  host_platform: string
  draft_type: string | null
  keeper_flag: boolean
  dynasty_flag: boolean
  last_synced_at: string | null
  connected_at: string
}

function uid() {
  return Math.random().toString(36).slice(2)
}

// ──────────────────────────────────────────
// My Connections view (hasLeagues=true)
// ──────────────────────────────────────────
function MyConnections({ onAddLeague }: { onAddLeague: () => void }) {
  const setHasLeagues = useAuthStore((s) => s.setHasLeagues)
  const [leagues, setLeagues] = useState<ConnectedLeague[]>([])

  const { isLoading } = useQuery({
    queryKey: ['leagues/mine'],
    queryFn: async () => {
      const { data } = await api.get('/leagues/mine')
      setLeagues(data)
      return data as ConnectedLeague[]
    },
  })

  function handleDisconnected(id: string) {
    const next = leagues.filter((l) => l.id !== id)
    setLeagues(next)
    if (next.length === 0) setHasLeagues(false)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-10 pb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-text">My Connections</h1>
        <button
          onClick={onAddLeague}
          className="text-sm text-accent hover:underline"
        >
          Connect another →
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 space-y-3 pb-6">
        {isLoading && (
          <>
            <div className="animate-pulse bg-raised rounded-xl h-24" />
            <div className="animate-pulse bg-raised rounded-xl h-24" />
          </>
        )}

        {!isLoading && leagues.length === 0 && (
          <div className="flex flex-col items-center justify-center pt-20 space-y-3 text-center">
            <h2 className="text-lg font-semibold text-text">No leagues connected</h2>
            <p className="text-sm text-muted">Connect a league to get started.</p>
            <button
              onClick={onAddLeague}
              className="bg-accent hover:bg-accent/90 text-white font-semibold rounded-lg px-6 py-3 min-h-[44px] transition-colors"
            >
              Connect a league
            </button>
          </div>
        )}

        {!isLoading && leagues.map((league) => (
          <ConnectionCard
            key={league.id}
            league={league}
            onDisconnected={handleDisconnected}
          />
        ))}
      </div>
    </div>
  )
}

// ──────────────────────────────────────────
// Conversational onboarding (hasLeagues=false)
// ──────────────────────────────────────────
function OnboardingFlow({ onComplete, initialStep = 'platform' }: { onComplete: () => void; initialStep?: Step }) {
  const [step, setStep] = useState<Step>(initialStep)
  const [bubbles, setBubbles] = useState<BubbleEntry[]>([
    {
      id: uid(),
      type: 'app',
      content: initialStep === 'yahoo_connected'
        ? 'Yahoo connected! Your leagues will be imported. Head to My Team to see your lineup.'
        : 'Hey! Welcome to FantasyHub. Which platform is your league on?',
    },
  ])
  const [username, setUsername] = useState('')
  const [sleeperLeagues, setSleeperLeagues] = useState<SleeperLeague[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [lookingUp, setLookingUp] = useState(false)
  const [importing, setImporting] = useState(false)
  const [espnSwid, setEspnSwid] = useState('')
  const [espnS2, setEspnS2] = useState('')
  const [espnLeagueId, setEspnLeagueId] = useState('')
  const [espnError, setEspnError] = useState('')
  const [espnSubmitting, setEspnSubmitting] = useState(false)
  const [espnManual, setEspnManual] = useState(false)
  const [espnNativeLoading, setEspnNativeLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Handle bookmarklet redirect: /connect?espn_swid=...&espn_s2=...&espn_lid=...
  useEffect(() => {
    const swid = searchParams.get('espn_swid')
    const s2 = searchParams.get('espn_s2')
    const lid = searchParams.get('espn_lid')
    if (swid && s2) {
      setEspnSwid(swid)
      setEspnS2(s2)
      if (lid) setEspnLeagueId(lid)
      setPlatform('ESPN')
      setStep('espn_private')
      append({ type: 'user', content: 'ESPN' })
      append({ type: 'user', content: 'Private league' })
      append({
        type: 'app',
        content: (
          <p>
            Got your ESPN credentials automatically.{' '}
            {lid ? 'League ID detected too — ' : 'Just enter your League ID and '}
            hit Connect.
          </p>
        ),
      })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [bubbles])

  function append(entry: Omit<BubbleEntry, 'id'>) {
    setBubbles((prev) => [...prev, { ...entry, id: uid() }])
  }

  function removeTyping() {
    setBubbles((prev) => prev.filter((b) => b.type !== 'typing'))
  }

  function handlePlatformSelect(platform: string) {
    append({ type: 'user', content: platform })
    if (platform === 'Sleeper') {
      setStep('username')
      setTimeout(() => {
        append({
          type: 'app',
          content: (
            <div>
              <p>Got it. What&apos;s your Sleeper username? I&apos;ll find your leagues — no password needed.</p>
            </div>
          ),
        })
      }, 400)
    } else if (platform === 'Yahoo') {
      append({
        type: 'app',
        content: <p>Redirecting you to Yahoo to authorize access…</p>,
      })
      setTimeout(() => {
        window.location.href = '/api/v1/auth/yahoo'
      }, 600)
    } else if (platform === 'ESPN') {
      setStep('espn_type')
      setTimeout(() => {
        append({
          type: 'app',
          content: <p>Is your ESPN league private (requires cookies) or public?</p>,
        })
      }, 400)
    }
  }

  async function handleEspnPrivateSubmit() {
    if (!espnSwid.trim() || !espnS2.trim() || !espnLeagueId.trim()) return
    setEspnError('')
    setEspnSubmitting(true)
    try {
      await api.post('/espn/connect', {
        swid: espnSwid.trim(),
        espn_s2: espnS2.trim(),
        league_id: espnLeagueId.trim(),
      })
      setStep('done')
      append({ type: 'app', content: <p>ESPN private league connected! Head to My Team.</p> })
      onComplete()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'ESPN connection failed. Check your cookies and try again.'
      setEspnError(detail)
    } finally {
      setEspnSubmitting(false)
    }
  }

  async function handleEspnNativeConnect() {
    setEspnNativeLoading(true)
    setEspnError('')
    try {
      const result = await EspnCookieNative.extractCookies()
      setEspnSwid(result.swid)
      setEspnS2(result.espnS2)
      if (result.leagueId) setEspnLeagueId(result.leagueId)
      append({
        type: 'app',
        content: (
          <p>
            Got your ESPN credentials.{' '}
            {result.leagueId ? 'League ID detected too — ' : 'Enter your League ID and '}
            hit Connect.
          </p>
        ),
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (!msg.includes('cancelled')) setEspnError('Could not sign in to ESPN. Please try again.')
    } finally {
      setEspnNativeLoading(false)
    }
  }

  async function handleEspnPublicSubmit() {
    if (!espnLeagueId.trim()) return
    setEspnError('')
    setEspnSubmitting(true)
    try {
      await api.post('/espn/public', { league_id: espnLeagueId.trim() })
      setStep('done')
      append({ type: 'app', content: <p>ESPN public league connected! Head to My Team.</p> })
      onComplete()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'Could not find that ESPN league. Verify the league ID.'
      setEspnError(detail)
    } finally {
      setEspnSubmitting(false)
    }
  }

  async function handleLookup() {
    if (!username.trim()) return
    append({ type: 'user', content: username.trim() })
    setLookingUp(true)
    append({ type: 'typing', content: null })
    try {
      const { data } = await api.get(`/sleeper/lookup?username=${encodeURIComponent(username.trim())}`)
      removeTyping()
      setSleeperLeagues(data.leagues)
      setStep('leagues')
      append({
        type: 'app',
        content: (
          <p>Found {data.leagues.length} league{data.leagues.length !== 1 ? 's' : ''}. Pick the ones you want to import.</p>
        ),
      })
    } catch (err: unknown) {
      removeTyping()
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? "That username doesn't exist on Sleeper. Double-check the spelling and try again."
      append({ type: 'app', content: <p className="text-danger">{detail}</p> })
    } finally {
      setLookingUp(false)
    }
  }

  function toggleLeague(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function handleImport() {
    const selectedLeagues = sleeperLeagues.filter((l) => selected.has(l.league_id))
    const names = selectedLeagues.map((l) => l.name).join(', ')
    append({ type: 'user', content: `Import ${names}` })
    setStep('importing')
    setImporting(true)
    setTimeout(() => {
      append({
        type: 'app',
        content: (
          <div className="space-y-3">
            <p>Done! Importing your roster now — this takes about 10 seconds.</p>
            <ProgressBar estimatedSeconds={10} />
          </div>
        ),
      })
    }, 400)
    try {
      await api.post('/sleeper/import', { league_ids: [...selected] })
      setStep('done')
      append({
        type: 'app',
        content: (
          <div className="space-y-3">
            <p>You&apos;re all set. Head to My Team to see your lineup.</p>
          </div>
        ),
      })
      onComplete()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? 'Something went wrong importing that league.'
      append({ type: 'app', content: <p className="text-danger">{detail}</p> })
      setStep('leagues')
    } finally {
      setImporting(false)
    }
  }

  const selectedCount = selected.size

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="px-4 pt-10 pb-2 flex items-center justify-between shrink-0">
        <h1 className="text-xl font-semibold text-text">Connect a League</h1>
      </div>

      {/* Chat scroll area */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-3">
        <div className="max-w-[600px] w-full mx-auto space-y-3">
          {bubbles.map((b) => {
            if (b.type === 'typing') {
              return (
                <div key={b.id} className="bg-surface border border-border rounded-[20px] self-start animate-fade-in">
                  <TypingIndicator />
                </div>
              )
            }
            return (
              <ChatBubble key={b.id} variant={b.type as 'app' | 'user'}>
                {b.content}
              </ChatBubble>
            )
          })}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Fixed input row */}
      <div className="shrink-0 border-t border-border bg-surface px-4 py-4">
        <div className="max-w-[600px] w-full mx-auto">

          {/* Step: platform selection */}
          {step === 'platform' && (
            <div className="flex flex-wrap gap-2">
              <OptionPill onClick={() => handlePlatformSelect('Sleeper')}>
                <span className="flex items-center gap-1.5"><PlatformIcon platform="sleeper" size={20} />Sleeper</span>
              </OptionPill>
              <OptionPill onClick={() => handlePlatformSelect('Yahoo')}>
                <span className="flex items-center gap-1.5"><PlatformIcon platform="yahoo" size={20} />Yahoo</span>
              </OptionPill>
              <OptionPill onClick={() => handlePlatformSelect('ESPN')}>
                <span className="flex items-center gap-1.5"><PlatformIcon platform="espn" size={20} />ESPN</span>
              </OptionPill>
            </div>
          )}

          {/* Step: ESPN sub-type selection */}
          {step === 'espn_type' && (
            <div className="flex flex-wrap gap-2">
              <OptionPill onClick={() => { append({ type: 'user', content: 'Private league' }); setStep('espn_private') }}>
                Private league (cookie paste)
              </OptionPill>
              <OptionPill onClick={() => { append({ type: 'user', content: 'Public league' }); setStep('espn_public') }}>
                Public league (league ID only)
              </OptionPill>
            </div>
          )}

          {/* Step: ESPN private — bookmarklet-first flow */}
          {step === 'espn_private' && (() => {
            const bookmarklet = `javascript:(function(){var d=document.cookie,swid=(d.match(/(?:^|;\\s*)SWID=([^;]+)/)||[])[1],s2=(d.match(/(?:^|;\\s*)espn_s2=([^;]+)/)||[])[1],lid=(location.search.match(/[?&]leagueId=(\\d+)/)||[])[1]||'';if(swid&&s2){location.href='${window.location.origin}/connect?espn_swid='+encodeURIComponent(swid)+'&espn_s2='+encodeURIComponent(s2)+'&espn_lid='+encodeURIComponent(lid);}else{alert('Couldn\\'t find your ESPN login. Make sure you are signed in to espn.com and try again.');}})();`
            const alreadyFilled = espnSwid && espnS2
            return (
              <div className="space-y-3">
                {!alreadyFilled && !espnManual ? (
                  <>
                    {isNative() ? (
                      /* Native app: single "Sign in to ESPN" button */
                      <div className="space-y-3">
                        <div className="bg-raised border border-border rounded-lg p-4 space-y-2">
                          <p className="text-sm font-semibold text-text">Sign in to ESPN</p>
                          <p className="text-sm text-muted">
                            We'll open ESPN inside the app. Sign in and we'll automatically
                            detect your league credentials.
                          </p>
                        </div>
                        {espnError && <p className="text-sm text-danger">{espnError}</p>}
                        <button
                          onClick={handleEspnNativeConnect}
                          disabled={espnNativeLoading}
                          className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors"
                        >
                          {espnNativeLoading ? 'Opening ESPN…' : 'Sign in to ESPN →'}
                        </button>
                        <button
                          onClick={() => setEspnManual(true)}
                          className="text-xs text-muted underline w-full text-center"
                        >
                          Enter cookies manually
                        </button>
                      </div>
                    ) : (
                    /* Web: bookmarklet card */
                    <div className="bg-raised border border-border rounded-lg p-4 space-y-3">
                      <p className="text-sm font-semibold text-text">Connect in 3 steps — no technical knowledge needed</p>
                      <div className="space-y-3 text-sm text-muted">
                        <div className="flex gap-3 items-start">
                          <span className="bg-accent text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shrink-0 mt-0.5">1</span>
                          <div>
                            <p className="text-text font-medium">Drag this button to your bookmarks bar</p>
                            <p className="text-xs mt-0.5 mb-2">If your bookmarks bar isn't visible: <strong className="text-text">View → Show Bookmarks Bar</strong></p>
                            <a
                              href={bookmarklet}
                              onClick={(e) => e.preventDefault()}
                              draggable
                              className="inline-flex items-center gap-1.5 bg-surface border-2 border-accent text-accent text-xs font-semibold rounded-lg px-3 py-2 cursor-grab active:cursor-grabbing select-none"
                              title="Drag me to your bookmarks bar"
                            >
                              ⭐ ESPN Connect
                            </a>
                            <p className="text-xs mt-1.5 text-muted">Drag the button above into your browser's bookmarks bar.</p>
                          </div>
                        </div>
                        <div className="flex gap-3 items-start">
                          <span className="bg-accent text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shrink-0 mt-0.5">2</span>
                          <div>
                            <p className="text-text font-medium">Go to your ESPN fantasy league page</p>
                            <a
                              href="https://fantasy.espn.com/football/league"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-accent text-xs underline"
                            >
                              Open ESPN Fantasy →
                            </a>
                            <p className="text-xs mt-0.5">Make sure you're signed in to your ESPN account.</p>
                          </div>
                        </div>
                        <div className="flex gap-3 items-start">
                          <span className="bg-accent text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shrink-0 mt-0.5">3</span>
                          <div>
                            <p className="text-text font-medium">Click the "ESPN Connect" bookmark</p>
                            <p className="text-xs mt-0.5">You'll be brought back here automatically with everything filled in.</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => setEspnManual(true)}
                      className="text-xs text-muted underline w-full text-center"
                    >
                      I'm a developer — enter cookies manually
                    </button>
                    </div>
                    /* end web bookmarklet */
                    )}
                  </>
                ) : (
                  /* Form — shown after bookmarklet redirect or manual toggle */
                  <div className="space-y-2">
                    {alreadyFilled && (
                      <div className="flex items-center gap-2 bg-success/10 border border-success/30 rounded-lg px-3 py-2">
                        <span className="text-success text-sm">✓</span>
                        <p className="text-xs text-success">ESPN credentials extracted automatically.</p>
                      </div>
                    )}
                    <div>
                      <label className="block text-xs text-muted mb-1 ml-0.5">SWID cookie</label>
                      <input
                        type="text"
                        value={espnSwid}
                        onChange={(e) => setEspnSwid(e.target.value)}
                        placeholder="{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}"
                        className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px] font-mono"
                        aria-label="ESPN SWID cookie"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-muted mb-1 ml-0.5">espn_s2 cookie</label>
                      <input
                        type="text"
                        value={espnS2}
                        onChange={(e) => setEspnS2(e.target.value)}
                        placeholder="AExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…"
                        className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px] font-mono"
                        aria-label="ESPN espn_s2 cookie"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-muted mb-1 ml-0.5">League ID</label>
                      <input
                        type="text"
                        value={espnLeagueId}
                        onChange={(e) => setEspnLeagueId(e.target.value)}
                        placeholder="e.g. 336584  (from the ESPN URL: /league?leagueId=...)"
                        className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
                        aria-label="ESPN League ID"
                      />
                    </div>
                    {espnError && <p className="text-sm text-danger">{espnError}</p>}
                    <button
                      onClick={handleEspnPrivateSubmit}
                      disabled={espnSubmitting || !espnSwid.trim() || !espnS2.trim() || !espnLeagueId.trim()}
                      className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors"
                    >
                      {espnSubmitting ? 'Connecting…' : 'Connect ESPN League →'}
                    </button>
                  </div>
                )}
              </div>
            )
          })()}

          {/* Step: ESPN public form */}
          {step === 'espn_public' && (
            <div className="space-y-2">
              <input
                type="text"
                value={espnLeagueId}
                onChange={(e) => setEspnLeagueId(e.target.value)}
                placeholder="ESPN League ID"
                className="w-full bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
                aria-label="ESPN League ID"
              />
              {espnError && <p className="text-sm text-danger">{espnError}</p>}
              <button
                onClick={handleEspnPublicSubmit}
                disabled={espnSubmitting || !espnLeagueId.trim()}
                className="w-full bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors"
              >
                {espnSubmitting ? 'Connecting…' : 'Connect Public League →'}
              </button>
            </div>
          )}

          {/* Step: Yahoo connected success */}
          {step === 'yahoo_connected' && (
            <OptionPill onClick={onComplete} selected>
              View My Team →
            </OptionPill>
          )}

          {/* Step: username input */}
          {step === 'username' && (
            <div className="flex gap-2">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !lookingUp && handleLookup()}
                placeholder="your_sleeper_username"
                autoFocus
                className="flex-1 bg-raised border border-border rounded-lg px-3 py-3 text-sm text-text placeholder:text-muted focus:outline-none focus:border-accent transition-colors min-h-[44px]"
                aria-label="Sleeper username"
              />
              <button
                onClick={handleLookup}
                disabled={lookingUp || !username.trim()}
                className="bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors whitespace-nowrap"
              >
                {lookingUp ? 'Looking up…' : 'Find my leagues →'}
              </button>
            </div>
          )}

          {/* Step: league selection */}
          {step === 'leagues' && (
            <div className="space-y-2">
              <div className="max-h-48 overflow-y-auto space-y-2">
                {sleeperLeagues.map((league) => (
                  <LeagueCard
                    key={league.league_id}
                    league={league}
                    selected={selected.has(league.league_id)}
                    onToggle={toggleLeague}
                  />
                ))}
              </div>
              <button
                onClick={handleImport}
                disabled={selectedCount === 0}
                className={cn(
                  'w-full bg-accent hover:bg-accent/90 text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors',
                  selectedCount === 0 && 'opacity-50 cursor-not-allowed',
                )}
              >
                {selectedCount === 0
                  ? 'Select at least one'
                  : `Import ${selectedCount} League${selectedCount !== 1 ? 's' : ''} →`}
              </button>
            </div>
          )}

          {/* Step: importing */}
          {step === 'importing' && (
            <div className="text-center text-sm text-muted py-2">
              {importing ? 'Importing…' : 'Import complete'}
            </div>
          )}

          {/* Step: done */}
          {step === 'done' && (
            <OptionPill onClick={onComplete} selected>
              View My Team →
            </OptionPill>
          )}
        </div>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────
// ConnectPage — dual-mode entry point
// ──────────────────────────────────────────
export default function ConnectPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const hasLeagues = useAuthStore((s) => s.hasLeagues)
  const setHasLeagues = useAuthStore((s) => s.setHasLeagues)
  const [showAddFlow, setShowAddFlow] = useState(false)

  const platformParam = searchParams.get('platform')
  const reconnectParam = searchParams.get('reconnect')

  // /connect?platform=yahoo → returned from Yahoo OAuth callback
  const isYahooConnected = platformParam === 'yahoo'
  // /connect?reconnect=yahoo → from HealthBanner; skip to Yahoo step
  const isReconnect = !!reconnectParam

  function handleImportComplete() {
    setHasLeagues(true)
    setShowAddFlow(false)
    navigate('/team', { replace: true })
  }

  if (isYahooConnected) {
    return <OnboardingFlow onComplete={handleImportComplete} initialStep="yahoo_connected" />
  }

  if (isReconnect) {
    // Skip platform step — open onboarding directly
    return <OnboardingFlow onComplete={handleImportComplete} />
  }

  if (!hasLeagues || showAddFlow) {
    return <OnboardingFlow onComplete={handleImportComplete} />
  }

  return <MyConnections onAddLeague={() => setShowAddFlow(true)} />
}
