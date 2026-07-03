/**
 * BestAvailable — scrollable sorted player list with tier dividers and position filters.
 *
 * D-12: Best available is defined by server-sorted overall_rank.
 * D-11: Tier boundary between players where gap > 15 ranks (tier field from server).
 * D-03: Supports custom CSV rankings (reflected in overall_rank when server sends ranked data).
 */
import { useMemo, useState, useRef } from 'react'
import { useDraftStore } from '@/store/draft'
import { getDraftSocket } from '@/lib/socket'
import { PositionBadge } from './PositionBadge'

const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DEF'] as const
type PositionFilter = typeof POSITIONS[number]

const GRADE_CLASSES: Record<string, string> = {
  'A+': 'text-emerald-400',
  'A':  'text-green-400',
  'B':  'text-yellow-400',
  'C':  'text-amber-400',
  'D':  'text-orange-400',
  'F':  'text-red-400',
}

export function BestAvailable() {
  const availablePlayers = useDraftStore((s) => s.availablePlayers)
  const queuedPlayerIds = useDraftStore((s) => s.queuedPlayerIds)
  const addToQueue = useDraftStore((s) => s.addToQueue)
  const currentPickNum = useDraftStore((s) => s.currentPickNum)
  const config = useDraftStore((s) => s.config)
  const [posFilter, setPosFilter] = useState<PositionFilter>('ALL')
  // rawSearch: immediate input value (what the input shows)
  // search: debounced value (used for filtering) — 150ms debounce per D-10
  const [rawSearch, setRawSearch] = useState('')
  const [search, setSearch] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // D-09: Determine if it's the current user's turn (on the clock)
  const myTeamId = config?.my_team_id ?? ''
  const draftOrder = config?.draft_order ?? []
  const numTeams = config?.num_teams ?? 12
  const activeTeamSlot = (() => {
    const pickNum = currentPickNum + 1  // next pick (1-based)
    const roundNum = Math.floor((pickNum - 1) / numTeams) + 1
    const posInRound = (pickNum - 1) % numTeams
    return roundNum % 2 === 1 ? posInRound : numTeams - 1 - posInRound
  })()
  const isOnTheClock = myTeamId !== '' && draftOrder[activeTeamSlot] === myTeamId

  // Queued players still available (not yet drafted), top 3
  const queuedAvailable = useMemo(
    () => queuedPlayerIds
      .map((pid) => availablePlayers.find((p) => p.player_id === pid))
      .filter((p): p is typeof availablePlayers[0] => p !== undefined && !p.isDrafted)
      .slice(0, 3),
    [queuedPlayerIds, availablePlayers]
  )

  const filtered = useMemo(() => {
    return availablePlayers.filter((p) => {
      if (posFilter !== 'ALL' && p.position !== posFilter) return false
      if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
  }, [availablePlayers, posFilter, search])

  const handleAddToQueue = (player_id: string) => {
    addToQueue(player_id)
    const socket = getDraftSocket()
    if (socket) {
      socket.emit('queue_add', { player_id })
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Search */}
      <div className="px-2 pt-1 pb-0.5 flex-shrink-0">
        <input
          type="text"
          value={rawSearch}
          onChange={(e) => {
            const v = e.target.value
            setRawSearch(v)
            if (debounceRef.current) clearTimeout(debounceRef.current)
            debounceRef.current = setTimeout(() => setSearch(v), 150)
          }}
          placeholder="Search players..."
          className="w-full font-mono text-xs bg-surface border border-border px-2 py-1 rounded text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
          aria-label="Search available players"
        />
      </div>

      {/* Position filter tabs */}
      <div className="flex gap-0.5 px-2 py-1 flex-shrink-0 overflow-x-auto">
        {POSITIONS.map((pos) => (
          <button
            key={pos}
            onClick={() => setPosFilter(pos)}
            className={`px-1.5 py-0.5 rounded font-mono text-[10px] leading-none flex-shrink-0
              ${posFilter === pos
                ? 'bg-accent text-bg font-semibold'
                : 'text-text-muted hover:text-text'
              }`}
            aria-pressed={posFilter === pos}
          >
            {pos}
          </button>
        ))}
      </div>

      {/* Player list */}
      <div className="flex-1 overflow-y-auto">
        {/* D-09: FROM YOUR QUEUE section — shown only when user is on the clock (W3) */}
        {isOnTheClock && queuedAvailable.length > 0 && (
          <div className="border-b border-accent/20 pb-2 mb-2">
            <div className="px-2 py-1">
              <span className="text-xs font-mono font-semibold text-accent tracking-widest">FROM YOUR QUEUE</span>
            </div>
            {queuedAvailable.map((player) => (
              <div
                key={`queue-top-${player.player_id}`}
                className="flex items-center gap-1 px-2 py-1.5 hover:bg-surface-hover border-b border-border"
                data-testid={`queue-top-player-${player.player_id}`}
              >
                <span className="text-[10px] text-text-muted w-6 text-right flex-shrink-0 tabular-nums">{player.overall_rank}</span>
                <PositionBadge position={player.position} />
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="font-mono text-[11px] text-text truncate">{player.name}</span>
                  <span className="font-mono text-[10px] text-text-muted">{player.nfl_team}</span>
                </div>
                <span className="text-[10px] font-mono text-accent flex-shrink-0">&#10003;</span>
              </div>
            ))}
          </div>
        )}
        {filtered.length === 0 ? (
          <div className="px-2 py-4 text-center font-mono text-xs text-text-muted">
            No players available
          </div>
        ) : (
          filtered.map((player, idx) => {
            const prevPlayer = filtered[idx - 1]
            const isTierStart = idx > 0 && player.tier !== undefined && prevPlayer?.tier !== undefined && player.tier !== prevPlayer.tier
            const isQueued = queuedPlayerIds.includes(player.player_id)

            return (
              <div key={player.player_id}>
                {isTierStart && (
                  <div className="py-1 px-2 text-[10px] font-mono text-text-muted border-t border-accent/30 bg-accent/5">
                    — Tier {player.tier} —
                  </div>
                )}
                <div
                  className={`flex items-center gap-1 px-2 py-1.5 hover:bg-surface-hover border-b border-border cursor-pointer group${player.isDrafted ? ' opacity-40' : ''}`}
                  data-testid={`available-player-${player.player_id}`}
                >
                  {/* Rank */}
                  <span className="text-[10px] text-text-muted w-6 text-right flex-shrink-0 tabular-nums">
                    {player.overall_rank}
                  </span>

                  {/* Position badge */}
                  <PositionBadge position={player.position} />

                  {/* Name + team */}
                  <div className="flex flex-col min-w-0 flex-1">
                    <span className={`font-mono text-[11px] text-text truncate leading-tight${player.isDrafted ? ' line-through' : ''}`}>
                      {player.name}
                    </span>
                    <span className="font-mono text-[10px] text-text-muted leading-none">
                      {player.nfl_team}{player.bye_week ? ` · BYE ${player.bye_week}` : ''}
                    </span>
                  </div>

                  {/* ADP grade badge */}
                  {player.adp_grade && (
                    <span className={`font-mono text-[10px] font-semibold flex-shrink-0 ${GRADE_CLASSES[player.adp_grade] ?? 'text-text-muted'}`}>
                      {player.adp_grade}
                    </span>
                  )}

                  {/* Queue button */}
                  {isQueued ? (
                    <span className="text-[10px] font-mono text-accent flex-shrink-0">&#10003;</span>
                  ) : (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAddToQueue(player.player_id) }}
                      className="text-[10px] font-mono text-text-muted hover:text-accent flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity px-1"
                      aria-label={`Add ${player.name} to queue`}
                    >
                      +Q
                    </button>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
