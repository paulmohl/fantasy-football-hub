/**
 * RosterPanel — shows current user's drafted players by round.
 *
 * DR-06: User sees their roster building in real-time as picks are confirmed.
 * Reads from useDraftStore.myRoster (filtered to my_team_id in addPick).
 */
import { useDraftStore } from '@/store/draft'
import { PositionBadge } from './PositionBadge'

export function RosterPanel() {
  const myRoster = useDraftStore((s) => s.myRoster)
  const availablePlayers = useDraftStore((s) => s.availablePlayers)
  const config = useDraftStore((s) => s.config)

  // Build player lookup for names
  const playerMap = Object.fromEntries(availablePlayers.map((p) => [p.player_id, p]))

  // Group roster by round
  const byRound: Record<number, typeof myRoster> = {}
  for (const pick of myRoster) {
    if (!byRound[pick.round]) byRound[pick.round] = []
    byRound[pick.round].push(pick)
  }
  const rounds = Object.keys(byRound).map(Number).sort((a, b) => a - b)

  const totalRounds = config?.num_rounds ?? 15
  const drafted = myRoster.length

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-2 py-1 border-b border-border bg-surface flex-shrink-0 flex items-center justify-between">
        <span className="font-mono text-[10px] text-text-muted uppercase tracking-wider">My Roster</span>
        <span className="font-mono text-[10px] text-text-muted">{drafted}/{totalRounds}</span>
      </div>

      {/* Roster rows */}
      <div className="flex-1 overflow-y-auto">
        {myRoster.length === 0 ? (
          <div className="px-2 py-4 text-center font-mono text-[10px] text-text-muted">
            <p>No picks yet</p>
            <p className="mt-1 text-[9px]">Your selections appear here</p>
          </div>
        ) : (
          rounds.map((round) => (
            <div key={round}>
              {/* Round header */}
              <div className="px-2 py-0.5 font-mono text-[9px] text-text-muted border-b border-border bg-surface/50 uppercase tracking-wider">
                Rd {round}
              </div>
              {byRound[round].map((pick) => {
                const player = playerMap[pick.player_id]
                return (
                  <div
                    key={pick.pick_num}
                    className={`flex items-center gap-1 px-2 py-1 border-b border-border hover:bg-surface-hover
                      ${pick.is_auto_pick ? 'opacity-60' : ''}`}
                    data-testid={`roster-pick-${pick.pick_num}`}
                  >
                    <PositionBadge position={player?.position ?? '?'} />
                    <div className="flex flex-col min-w-0 flex-1">
                      <span className="font-mono text-[11px] text-text truncate leading-tight">
                        {player?.name ?? pick.player_id}
                      </span>
                      {player && (
                        <span className="font-mono text-[9px] text-text-muted leading-none">
                          {player.nfl_team}{player.bye_week ? ` · BYE ${player.bye_week}` : ''}
                        </span>
                      )}
                    </div>
                    {pick.is_auto_pick && (
                      <span className="font-mono text-[9px] text-text-muted flex-shrink-0">AUTO</span>
                    )}
                  </div>
                )
              })}
            </div>
          ))
        )}

        {/* Empty rounds remaining */}
        {drafted < totalRounds && (
          <div className="px-2 py-2 text-center font-mono text-[10px] text-text-muted/50">
            {totalRounds - drafted} picks remaining
          </div>
        )}
      </div>
    </div>
  )
}
