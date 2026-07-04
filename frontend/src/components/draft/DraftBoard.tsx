/**
 * DraftBoard — full snake draft board grid (D-02 LOCKED).
 *
 * Layout: num_rounds rows × num_teams columns.
 * Snake ordering: odd rounds L→R, even rounds R→L (snakePickToSlot).
 * Tier dividers: border-t-2 border-accent on first cell of a new player tier (D-11).
 * Horizontal scroll on container allows >12 teams without layout blowout.
 */
import { useMemo } from 'react'
import { useDraftStore } from '@/store/draft'
import { PickCell } from './PickCell'

/** Maps 1-based pick_num to [roundNum, teamSlot] for snake ordering. */
function snakePickToSlot(pickNum: number, numTeams: number): [number, number] {
  const roundNum = Math.floor((pickNum - 1) / numTeams) + 1
  const posInRound = (pickNum - 1) % numTeams
  const teamSlot = roundNum % 2 === 1 ? posInRound : numTeams - 1 - posInRound
  return [roundNum, teamSlot]
}

interface DraftBoardProps {
  onPickClick?: (pickNum: number) => void
}

export function DraftBoard({ onPickClick }: DraftBoardProps) {
  const config = useDraftStore((s) => s.config)
  const picks = useDraftStore((s) => s.picks)
  const availablePlayers = useDraftStore((s) => s.availablePlayers)
  const currentPickNum = useDraftStore((s) => s.currentPickNum)
  const myTeamId = config?.my_team_id ?? ''
  const numTeams = config?.num_teams ?? 12
  const numRounds = config?.num_rounds ?? 15

  // Build lookup: pick_num → DraftPick
  const pickByNum = useMemo(() => {
    const m: Record<number, (typeof picks)[0]> = {}
    for (const p of picks) m[p.pick_num] = p
    return m
  }, [picks])

  // Build lookup: player_id → DraftPlayer
  const playerById = useMemo(() => {
    const m: Record<string, (typeof availablePlayers)[0]> = {}
    for (const p of availablePlayers) m[p.player_id] = p
    return m
  }, [availablePlayers])

  // Tier boundaries: set of pick_num where a new tier starts (D-11)
  const tierStartPicks = useMemo(() => {
    const s = new Set<number>()
    for (const pick of picks) {
      const player = playerById[pick.player_id]
      if (player?.tier) {
        const prevPick = pickByNum[pick.pick_num - 1]
        if (prevPick) {
          const prevPlayer = playerById[prevPick.player_id]
          if (!prevPlayer || prevPlayer.tier !== player.tier) s.add(pick.pick_num)
        }
      }
    }
    return s
  }, [picks, pickByNum, playerById])

  // Build grid: [roundIdx][teamSlot] → pick_num
  const grid = useMemo(() => {
    return Array.from({ length: numRounds }, (_, r) =>
      Array.from({ length: numTeams }, (_, s) => {
        const roundNum = r + 1
        const posInRound = roundNum % 2 === 1 ? s : numTeams - 1 - s
        return roundNum * numTeams - numTeams + posInRound + 1
      })
    )
  }, [numRounds, numTeams])

  if (!config) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted font-mono text-sm">
        Loading board...
      </div>
    )
  }

  const draftOrder = config.draft_order

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Column headers — team name row */}
      <div
        className="grid border-b border-border bg-surface flex-shrink-0"
        style={{ gridTemplateColumns: `repeat(${numTeams}, minmax(0, 1fr))` }}
      >
        {Array.from({ length: numTeams }, (_, i) => {
          const teamId = draftOrder[i]
          const isMySlot = teamId === myTeamId
          return (
            <div
              key={i}
              className={`px-1 py-1 font-mono text-[10px] text-center truncate border-r border-border last:border-r-0
                ${isMySlot ? 'text-accent font-semibold' : 'text-muted'}`}
            >
              {isMySlot ? 'YOU' : `T${i + 1}`}
            </div>
          )
        })}
      </div>

      {/* Board rows — scrollable */}
      <div className="flex-1 overflow-y-auto">
        {grid.map((row, roundIdx) => (
          <div
            key={roundIdx}
            className="grid"
            style={{ gridTemplateColumns: `repeat(${numTeams}, minmax(0, 1fr))` }}
          >
            {row.map((pickNum) => {
              const [round, teamSlot] = snakePickToSlot(pickNum, numTeams)
              const pick = pickByNum[pickNum]
              const player = pick ? playerById[pick.player_id] : undefined
              const isActive = pickNum === currentPickNum + 1
              const teamId = draftOrder[teamSlot]
              const isMyTeam = teamId === myTeamId
              return (
                <PickCell
                  key={pickNum}
                  pickNum={pickNum}
                  round={round}
                  teamSlot={teamSlot}
                  pick={pick}
                  player={player}
                  isActive={isActive}
                  isMyTeam={isMyTeam}
                  isTierStart={tierStartPicks.has(pickNum)}
                  onClick={onPickClick}
                />
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
