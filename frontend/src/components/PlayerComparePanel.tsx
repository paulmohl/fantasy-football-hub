import { useQuery } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { ConfidenceBadge } from './ConfidenceBadge'
import { InjuryBadge } from './InjuryBadge'
import type { PlayerSlotData } from './PlayerDetailDrawer'

interface TradeComparisonResult {
  recommendation: 'start_a' | 'start_b' | 'neutral'
  point_delta: number
  confidence: number
  three_biggest_factors: { label: string; detail: string }[]
}

interface PlayerComparePanelProps {
  playerA: PlayerSlotData
  playerB: PlayerSlotData | null
  activeLeagueId: string | null
  comparePool: PlayerSlotData[]
  onSelectPlayerB: (player: PlayerSlotData) => void
  onBack: () => void
}

export function PlayerComparePanel({
  playerA,
  playerB,
  activeLeagueId,
  comparePool,
  onSelectPlayerB,
  onBack,
}: PlayerComparePanelProps) {
  const { data: tradeData, isLoading } = useQuery<TradeComparisonResult>({
    queryKey: ['trade', playerA.player_id, playerB?.player_id, activeLeagueId],
    queryFn: () =>
      api
        .get('/team/trade', {
          params: {
            player_a: playerA.player_id,
            player_b: playerB!.player_id,
            league_id: activeLeagueId,
          },
        })
        .then((r) => r.data),
    enabled: !!playerB && !!activeLeagueId,
    staleTime: 5 * 60 * 1000,
  })

  const winnerIsA = tradeData?.recommendation === 'start_a'
  const winnerIsB = tradeData?.recommendation === 'start_b'

  return (
    <div className="mt-4 space-y-4">
      <button
        onClick={onBack}
        className="text-xs font-semibold text-accent hover:underline"
      >
        &larr; Back to {playerA.full_name?.split(' ')[0]}
      </button>

      <div
        className={cn(
          'bg-raised border rounded-xl p-4 space-y-3',
          winnerIsA ? 'border-success/30 bg-success/5' : 'border-border',
        )}
      >
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-text">{playerA.full_name}</p>
          <InjuryBadge status={playerA.injury_status} />
        </div>
        <div className="flex gap-4">
          <div>
            <p className="text-xs text-muted">Proj Pts</p>
            <p className="font-mono text-sm font-semibold text-accent">
              {playerA.projected_points.toFixed(1)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Confidence</p>
            <ConfidenceBadge confidence={playerA.confidence} />
          </div>
        </div>
        {winnerIsA && (
          <p className="text-xs font-semibold text-success">Recommended start</p>
        )}
      </div>

      {!playerB ? (
        <div className="space-y-2">
          <p className="text-xs text-muted font-semibold uppercase tracking-wide">
            Select a player to compare
          </p>
          {comparePool.length === 0 ? (
            <p className="text-xs text-muted italic">
              No other players available in current lineup view.
            </p>
          ) : (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {comparePool.map((p) => (
                <button
                  key={p.player_id}
                  onClick={() => onSelectPlayerB(p)}
                  className="w-full text-left px-3 py-2 rounded-lg bg-raised hover:bg-border transition-colors"
                >
                  <span className="text-sm text-text">{p.full_name}</span>
                  <span className="text-xs text-muted ml-2">{p.position}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <>
          <div
            className={cn(
              'bg-raised border rounded-xl p-4 space-y-3',
              winnerIsB ? 'border-success/30 bg-success/5' : 'border-border',
            )}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-text">{playerB.full_name}</p>
              <div className="flex items-center gap-2">
                <InjuryBadge status={playerB.injury_status} />
                <button
                  onClick={() => onSelectPlayerB(null as unknown as PlayerSlotData)}
                  className="text-xs text-muted hover:text-text"
                >
                  Change
                </button>
              </div>
            </div>
            <div className="flex gap-4">
              <div>
                <p className="text-xs text-muted">Proj Pts</p>
                <p className="font-mono text-sm font-semibold text-accent">
                  {playerB.projected_points.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted">Confidence</p>
                <ConfidenceBadge confidence={playerB.confidence} />
              </div>
            </div>
            {winnerIsB && (
              <p className="text-xs font-semibold text-success">Recommended start</p>
            )}
          </div>

          {isLoading && (
            <div className="h-24 animate-pulse bg-raised rounded-xl" />
          )}

          {tradeData && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <p className="text-xs text-muted">Value delta</p>
                <p className="text-sm font-mono font-semibold text-text">
                  {tradeData.point_delta > 0 ? '+' : ''}
                  {tradeData.point_delta.toFixed(0)} pts
                </p>
                <p className="text-xs text-muted">
                  ({tradeData.confidence}% confidence)
                </p>
              </div>

              {tradeData.three_biggest_factors.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted uppercase tracking-wide">
                    Key factors
                  </p>
                  {tradeData.three_biggest_factors.map((f, i) => (
                    <div key={i} className="bg-raised rounded-lg px-3 py-2">
                      <p className="text-xs font-semibold text-text">{f.label}</p>
                      <p className="text-xs text-muted">{f.detail}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
