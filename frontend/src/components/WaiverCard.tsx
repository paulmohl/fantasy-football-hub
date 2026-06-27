import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { ChevronDown, Check, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { useLeagueStore } from '@/store/league'
import { InjuryBadge } from './InjuryBadge'

type WaiverMode = 'trend' | 'composite'

const MODE_LABELS: Record<WaiverMode, string> = {
  trend: 'Trend-weighted',
  composite: 'Full composite',
}

export interface WaiverPlayer {
  player_id: string
  full_name: string
  position: string
  team: string | null
  trend_score: number
  composite_score: number
  injury_status: string | null
  fc_value: number
  trending_count: number
}

interface DropSuggestion {
  player_id: string
  full_name: string
  position: string
  ros_value: number
  injury_status: string | null
}

interface FaabBid {
  mid_bid: number
  confidence_range: number
  min_bid: number
  max_bid: number
}

interface WaiverResponse {
  league_id: string
  waiver_type: 'faab' | 'rolling'
  mode: WaiverMode
  season_type: string
  players: WaiverPlayer[]
  drop_suggestions: DropSuggestion[]
  faab_bid: FaabBid | null
}

export function WaiverCard({
  onAddPlayer,
}: {
  onAddPlayer: (
    player: WaiverPlayer,
    waiverType: 'faab' | 'rolling',
    dropCandidates: DropSuggestion[],
    faabBid: FaabBid | null,
  ) => void
}) {
  const { activeLeagueId } = useLeagueStore()
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<WaiverMode>('composite')
  const [visibleCount, setVisibleCount] = useState(10)

  const { data, isLoading, error } = useQuery<WaiverResponse>({
    queryKey: ['team-waiver', activeLeagueId, mode],
    queryFn: () =>
      api
        .get('/team/waiver', { params: { league_id: activeLeagueId, mode } })
        .then((r) => r.data),
    enabled: !!activeLeagueId,
  })

  const isOffSeason = data?.season_type === 'off'

  function getScore(player: WaiverPlayer) {
    return mode === 'trend' ? player.trend_score : player.composite_score
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-text">Waiver Wire</h2>

        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button
              className="bg-raised border border-border rounded-lg px-3 py-1.5 text-xs font-semibold text-text flex items-center gap-1.5 hover:border-accent/50 transition-colors"
              aria-label="Change waiver ranking mode"
            >
              {MODE_LABELS[mode]}
              <ChevronDown size={14} className="text-muted" />
            </button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="bg-surface border border-border rounded-xl shadow-lg min-w-[180px] z-50 py-1"
              sideOffset={4}
              align="end"
            >
              {(Object.keys(MODE_LABELS) as WaiverMode[]).map((m) => (
                <DropdownMenu.Item
                  key={m}
                  disabled={isOffSeason}
                  onSelect={() => setMode(m)}
                  className={cn(
                    'px-3 py-2 flex items-center gap-2 text-xs font-semibold cursor-pointer outline-none hover:bg-raised',
                    isOffSeason ? 'opacity-40 cursor-not-allowed' : '',
                    mode === m && 'text-accent',
                  )}
                  title={isOffSeason ? 'In-season data only' : undefined}
                >
                  {mode === m && <Check size={14} />}
                  {mode !== m && <span className="w-[14px]" />}
                  {MODE_LABELS[m]}
                </DropdownMenu.Item>
              ))}
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>

      {isOffSeason && (
        <div className="bg-surface border border-border rounded-xl p-3 mb-3 text-center">
          <p className="text-sm font-semibold text-text">Waiver wire in-season only</p>
          <p className="text-xs text-muted mt-0.5">Rankings will appear when the NFL season starts.</p>
        </div>
      )}

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse bg-raised rounded-xl" />
          ))}
        </div>
      )}

      {error && !isLoading && (
        <p className="text-sm text-danger">
          Couldn't load waiver rankings.{' '}
          <button
            className="underline"
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ['team-waiver', activeLeagueId, mode] })
            }
          >
            Try again
          </button>
        </p>
      )}

      {!isLoading && !error && data && data.players.length === 0 && !isOffSeason && (
        <div className="text-center py-4">
          <p className="text-sm font-semibold text-text">No waiver targets found</p>
          <p className="text-xs text-muted mt-1">Your league may not have available players this week.</p>
        </div>
      )}

      {!isLoading && data && data.players.length > 0 && (
        <>
          <div className="space-y-2">
            {data.players.slice(0, visibleCount).map((player, idx) => (
              <div
                key={player.player_id}
                className="bg-raised border border-border rounded-xl p-3 flex items-center gap-3"
              >
                <span className="w-8 shrink-0 text-xs font-semibold font-mono text-muted text-right">
                  {idx + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <span className="text-sm font-semibold text-text truncate">{player.full_name}</span>
                    <InjuryBadge status={player.injury_status} playerName={player.full_name} />
                  </div>
                  <p className="text-xs text-muted">
                    {player.position} · {player.team ?? '—'}
                  </p>
                </div>
                <span className="font-mono text-sm font-semibold text-text shrink-0">
                  {getScore(player).toFixed(1)}
                </span>
                <button
                  onClick={() =>
                    onAddPlayer(player, data.waiver_type, data.drop_suggestions, data.faab_bid)
                  }
                  className="bg-accent/10 hover:bg-accent text-accent hover:text-white rounded-lg w-8 h-8 flex items-center justify-center transition-colors shrink-0"
                  aria-label={`Add ${player.full_name} to roster`}
                >
                  <Plus size={18} />
                </button>
              </div>
            ))}
          </div>

          {visibleCount < data.players.length && (
            <button
              className="mt-3 w-full text-accent text-sm hover:underline text-center"
              onClick={() => setVisibleCount((n) => n + 20)}
            >
              Show 20 more
            </button>
          )}
        </>
      )}
    </div>
  )
}
