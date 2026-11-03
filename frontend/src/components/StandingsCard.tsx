import { useQuery } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { useLeagueStore } from '@/store/league'

interface StandingsRow {
  roster_id: number
  team_name: string
  user_id: string
  is_current_user: boolean
  wins: number
  losses: number
  pts_for: number
  waiver_position: number | null
}

interface StandingsResponse {
  league_id: string
  week: number
  standings: StandingsRow[]
}

export function StandingsCard() {
  const { activeLeagueId } = useLeagueStore()

  const { data, isLoading, error } = useQuery<StandingsResponse>({
    queryKey: ['team-standings', activeLeagueId],
    queryFn: () =>
      api.get('/team/standings', { params: { league_id: activeLeagueId } }).then((r) => r.data),
    enabled: !!activeLeagueId,
  })

  return (
    <div className="card">
      <h2 className="card-title mb-3">League Standings</h2>

      {isLoading && (
        <div className="space-y-1">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-8 animate-pulse bg-raised rounded-lg" />
          ))}
        </div>
      )}

      {error && !isLoading && (
        <p className="text-sm text-muted">
          Couldn't load standings.{' '}
          <button
            className="text-accent font-medium underline underline-offset-2"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </p>
      )}

      {!isLoading && !error && (!data || data.standings.length === 0) && (
        <div className="text-center py-4">
          <p className="text-sm font-semibold text-text">Standings unavailable</p>
          <p className="text-xs text-muted mt-1">Standings will appear once league games begin.</p>
        </div>
      )}

      {!isLoading && data && data.standings.length > 0 && (
        <div className="space-y-0.5">
          <div className="flex items-center gap-3 px-2 pb-1 label">
            <span className="w-6 text-center">#</span>
            <span className="flex-1">Team</span>
            <span className="shrink-0">W-L</span>
            <span className="shrink-0 w-16 text-right">PF</span>
          </div>
          {data.standings.map((row, idx) => (
            <div
              key={row.roster_id}
              className={cn(
                'flex items-center gap-3 px-2 py-2.5 rounded-lg',
                row.is_current_user ? 'bg-accent/10 ring-1 ring-accent/25' : 'hover:bg-raised/60',
              )}
            >
              <span className="w-6 shrink-0 text-xs font-semibold font-mono text-muted text-center">
                {idx + 1}
              </span>

              <span
                className={cn(
                  'flex-1 text-sm text-text truncate',
                  row.is_current_user && 'font-semibold',
                )}
              >
                {row.team_name}
              </span>

              <span className="font-mono text-xs text-muted shrink-0">
                {row.wins}-{row.losses}
              </span>

              <span className="font-mono text-xs text-text shrink-0 w-16 text-right">
                {row.pts_for.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      )}

      {data && (
        <p className="text-xs text-muted mt-3 text-right">
          Through week <span className="font-mono">{data.week}</span>
        </p>
      )}
    </div>
  )
}
