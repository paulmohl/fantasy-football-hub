import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { InjuryBadge } from './InjuryBadge'
import { ConfidenceBadge } from './ConfidenceBadge'
import { WeatherChip } from './WeatherChip'
import { TrendChart } from './TrendChart'
import { PlayerComparePanel } from './PlayerComparePanel'

export interface PlayerSlotData {
  player_id: string
  full_name: string | null
  position: string | null
  injury_status: string | null
  projected_points: number
  confidence: number
  matchup_grade?: string | null
  opponent_rank_vs_position?: number | null
  recent_usage_trend?: string | null
  weather?: {
    wind_mph: number
    precipitation_mm: number
    weather_code: number
    snowfall_mm: number
    has_chip: boolean
  } | null
  team?: string | null
  is_out?: boolean
  replacement_suggestion?: string | null
}

function buildNLExplanation(player: PlayerSlotData): string {
  const name = player.full_name ?? 'This player'
  const pos = player.position ?? 'player'
  const conf = player.confidence
  const inj = player.injury_status
  const grade = player.matchup_grade
  const trend = player.recent_usage_trend

  let s1: string
  if (inj === 'Out' || inj === 'IR') {
    s1 = `${name} is listed as ${inj} and should not be started this week.`
  } else if (conf >= 70) {
    s1 = `${name} is a strong start this week with ${conf}% confidence, ranking among the top ${pos.toUpperCase()}s for this matchup.`
  } else if (conf >= 55) {
    s1 = `${name} is a moderate start with ${conf}% confidence — a reasonable floor with upside if the game script cooperates.`
  } else {
    s1 = `${name} is a risky start this week at only ${conf}% confidence; stronger bench options should be considered.`
  }

  let s2: string
  if (inj === 'Questionable' || inj === 'Doubtful') {
    s2 = `The ${inj?.toLowerCase()} injury designation adds uncertainty — monitor the practice report through Saturday.`
  } else if (grade === 'A' || grade === 'B') {
    s2 = `The matchup grades out as ${grade} — the opponent ranks poorly at defending the ${pos} position this season.`
  } else if (grade === 'D' || grade === 'F') {
    s2 = `The matchup grades out as ${grade} — the opponent is strong at defending ${pos}s and the projection reflects that.`
  } else {
    s2 = `The matchup is neutral (grade ${grade ?? '—'}) with no clear advantage or disadvantage based on current opponent data.`
  }

  let s3: string
  if (trend === 'up') {
    s3 = `Usage trend is pointing up over the last three weeks, supporting the projected floor.`
  } else if (trend === 'down') {
    s3 = `Usage trend has declined recently — ownership may be dropping them in waiver wire activity, so monitor snap counts.`
  } else if (player.weather?.has_chip) {
    s3 = `Weather conditions may suppress the projection; check the weather chip above for details.`
  } else {
    s3 = `Usage trend is stable with no significant changes in snap share over the recent stretch.`
  }

  return `${s1} ${s2} ${s3}`
}

const GRADE_COLOR: Record<string, string> = {
  A: 'text-success bg-success/10',
  B: 'text-success bg-success/5',
  C: 'text-text bg-raised',
  D: 'text-warning bg-warning/10',
  F: 'text-danger bg-danger/10',
}

const TREND_LABEL: Record<string, string> = {
  up: '↑ trending up',
  down: '↓ trending down',
  stable: '→ stable',
}

interface PlayerDetailDrawerProps {
  player: PlayerSlotData | null
  onClose: () => void
  seasonType?: string
  activeLeagueId?: string | null
  comparePool?: PlayerSlotData[]
}

export function PlayerDetailDrawer({
  player,
  onClose,
  seasonType,
  activeLeagueId,
  comparePool = [],
}: PlayerDetailDrawerProps) {
  const [isComparing, setIsComparing] = useState(false)
  const [playerB, setPlayerB] = useState<PlayerSlotData | null>(null)

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['player-stats', player?.player_id, activeLeagueId],
    queryFn: () =>
      api
        .get(`/team/stats/${player!.player_id}`, { params: { league_id: activeLeagueId } })
        .then((r) => r.data as { weekly_pts: { week: number; pts: number }[]; season_type: string }),
    enabled: !!player?.player_id && !!activeLeagueId,
    staleTime: 5 * 60 * 1000,
  })

  const trendData = statsData?.weekly_pts ?? []

  return (
    <Dialog.Root
      open={!!player}
      onOpenChange={(open) => {
        if (!open) {
          onClose()
          setIsComparing(false)
          setPlayerB(null)
        }
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
        <Dialog.Content
          className={cn(
            'fixed bg-surface border-border overflow-y-auto z-50 p-6',
            'inset-x-0 bottom-0 h-[85vh] border-t rounded-t-2xl',
            'sm:inset-x-auto sm:inset-y-0 sm:right-0 sm:h-full sm:w-full sm:max-w-[400px] sm:border-l sm:border-t-0 sm:rounded-none',
          )}
          aria-describedby="player-detail-description"
        >
          <Dialog.Title className="text-base font-semibold text-text" id="player-detail-title">
            {isComparing ? 'Compare Players' : (player?.full_name ?? 'Player Details')}
          </Dialog.Title>

          <p id="player-detail-description" className="sr-only">
            Player details and start/sit analysis
          </p>

          <Dialog.Close asChild>
            <button
              className="absolute top-4 right-4 text-muted hover:text-text transition-colors"
              aria-label="Close player details"
            >
              <X size={20} />
            </button>
          </Dialog.Close>

          {player && !isComparing && (
            <div className="mt-4 space-y-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-muted">{player.position}</span>
                    {player.team && <span className="text-xs text-muted">· {player.team}</span>}
                    <InjuryBadge status={player.injury_status} playerName={player.full_name ?? undefined} />
                  </div>
                </div>
                <button
                  className="text-xs font-semibold text-accent hover:underline"
                  onClick={() => setIsComparing(true)}
                >
                  Compare
                </button>
              </div>

              <div className="flex gap-2 overflow-x-auto pb-1">
                <div className="bg-raised rounded-lg px-3 py-2 shrink-0">
                  <p className="text-xs text-muted">Proj Pts</p>
                  <p className="text-sm font-semibold text-accent font-mono">
                    {player.projected_points.toFixed(1)}
                  </p>
                </div>
                <div className="bg-raised rounded-lg px-3 py-2 shrink-0">
                  <p className="text-xs text-muted">Confidence</p>
                  <ConfidenceBadge confidence={player.confidence} />
                </div>
                {player.matchup_grade && (
                  <div className="bg-raised rounded-lg px-3 py-2 shrink-0">
                    <p className="text-xs text-muted">Matchup</p>
                    <span
                      className={cn(
                        'text-sm font-semibold rounded px-1',
                        GRADE_COLOR[player.matchup_grade] ?? 'text-text bg-raised',
                      )}
                    >
                      {player.matchup_grade}
                    </span>
                  </div>
                )}
                {player.opponent_rank_vs_position != null && (
                  <div className="bg-raised rounded-lg px-3 py-2 shrink-0">
                    <p className="text-xs text-muted">Opp vs {player.position}</p>
                    <p className="text-sm font-semibold text-text">
                      #{player.opponent_rank_vs_position}
                    </p>
                  </div>
                )}
                {player.recent_usage_trend && (
                  <div className="bg-raised rounded-lg px-3 py-2 shrink-0">
                    <p className="text-xs text-muted">Usage</p>
                    <p className="text-sm font-semibold text-text">
                      {TREND_LABEL[player.recent_usage_trend] ?? player.recent_usage_trend}
                    </p>
                  </div>
                )}
              </div>

              {player.weather?.has_chip && (
                <WeatherChip
                  wind_mph={player.weather.wind_mph}
                  precipitation_mm={player.weather.precipitation_mm ?? 0}
                  weather_code={player.weather.weather_code ?? 0}
                  is_indoor={false}
                  size="full"
                />
              )}

              {seasonType !== 'off' && player.injury_status && player.injury_status !== 'Active' && (
                <div>
                  <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">Injury Status</p>
                  <div className="flex items-center gap-2">
                    <InjuryBadge status={player.injury_status} />
                    {player.is_out && player.replacement_suggestion && (
                      <span className="text-xs text-muted italic">Suggested: check bench</span>
                    )}
                  </div>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-semibold text-muted uppercase tracking-wide">This Season</p>
                </div>
                <TrendChart data={trendData} isLoading={statsLoading} />
                {statsData?.season_type === 'off' && (
                  <p className="text-xs text-muted mt-1 italic">
                    Trend data unavailable during off-season. Historical weekly stats show in-season.
                  </p>
                )}
              </div>

              <div>
                <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Analysis</p>
                <p className="text-sm text-text leading-relaxed">
                  {buildNLExplanation(player)}
                </p>
              </div>
            </div>
          )}

          {player && isComparing && (
            <PlayerComparePanel
              playerA={player}
              playerB={playerB}
              activeLeagueId={activeLeagueId ?? null}
              comparePool={comparePool.filter((p) => p.player_id !== player.player_id)}
              onSelectPlayerB={setPlayerB}
              onBack={() => {
                setIsComparing(false)
                setPlayerB(null)
              }}
            />
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
