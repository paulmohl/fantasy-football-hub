/**
 * PickCell — individual grid cell in the draft board.
 *
 * States:
 *   empty     — not yet drafted (bg-surface, round.slot label)
 *   filled    — player drafted (position badge, name, team)
 *   active    — current pick on the clock (pulsing ring-accent)
 *   my-pick   — my team filled this slot (ring-my-pick, per D-12)
 *   tier-start — first cell in a new tier (border-t-2 border-accent, per D-11)
 */
import type { DraftPick, DraftPlayer } from '@/store/draft'
import { useDraftStore } from '@/store/draft'
import { PositionBadge } from './PositionBadge'

interface PickCellProps {
  pickNum: number
  round: number
  teamSlot: number
  pick: DraftPick | undefined
  player: DraftPlayer | undefined
  isActive: boolean
  isMyTeam: boolean
  isTierStart: boolean
  onClick?: (pickNum: number) => void
}

export function PickCell({
  pickNum, round, teamSlot, pick, player, isActive, isMyTeam, isTierStart, onClick
}: PickCellProps) {
  const reactions = useDraftStore((s) => s.reactions[pickNum])

  const borderClass = isTierStart ? 'border-t-2 border-accent' : 'border-t border-border'
  const ringClass = isActive
    ? 'ring-2 ring-accent animate-pulse'
    : isMyTeam && pick
      ? 'ring-2 ring-my-pick'
      : ''
  const bgClass = pick ? 'bg-surface-hover' : 'bg-surface'

  return (
    <div
      className={`relative flex flex-col justify-between p-1 min-h-[52px] cursor-pointer
        ${bgClass} border-r border-border ${borderClass} ${ringClass}
        hover:bg-surface-hover transition-colors`}
      onClick={() => onClick?.(pickNum)}
      data-pick-num={pickNum}
      data-testid={`pick-cell-${pickNum}`}
      aria-label={pick ? `Pick ${pickNum}: ${player?.name ?? pick.player_id}` : `Pick ${pickNum}: empty`}
    >
      {/* Pick number — top-left micro label */}
      <span className="text-[9px] font-mono text-muted leading-none">{pickNum}</span>

      {pick && player ? (
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1">
            <PositionBadge position={player.position} />
            {pick.is_auto_pick && (
              <span className="text-[10px] font-mono text-muted">AUTO</span>
            )}
          </div>
          <span className="font-mono text-[11px] text-text truncate leading-tight">
            {player.name}
          </span>
          <span className="font-mono text-[10px] text-muted leading-none">
            {player.nfl_team}
          </span>
        </div>
      ) : pick ? (
        // Pick recorded but player data not yet hydrated
        <div className="flex flex-col gap-0.5">
          <span className="font-mono text-[11px] text-text truncate">{pick.player_id}</span>
        </div>
      ) : (
        // Empty cell — round.slot orientation label
        <span className="font-mono text-[10px] text-muted self-end">
          {round}.{teamSlot + 1}
        </span>
      )}

      {/* Emoji reactions (DR-11) — max 3 shown per D-02 spec */}
      {reactions && Object.keys(reactions).length > 0 && (
        <div className="flex gap-0.5 flex-wrap mt-0.5">
          {Object.entries(reactions).slice(0, 3).map(([emoji, users]) => (
            <span key={emoji} className="text-[10px]" title={`${users.length} reaction`}>
              {emojiChar(emoji)}{users.length > 1 ? users.length : ''}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function emojiChar(name: string): string {
  const map: Record<string, string> = {
    fire: '🔥', laugh: '😂', skeptical: '🤨', applause: '👏',
  }
  return map[name] ?? name
}
