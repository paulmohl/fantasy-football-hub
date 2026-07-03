/**
 * DraftRoom — Bloomberg Terminal 4-column layout shell (D-01 LOCKED).
 *
 * Columns (left to right, per D-01):
 *   [200px]  Col 1 — Left sidebar: Queue + Alerts stacked (wired in 04-11)
 *   [1fr]    Col 2 — Center-left: DraftBoard — primary focal point (this plan)
 *   [320px]  Col 3 — Center-right: BestAvailable (wired in 04-11)
 *   [200px]  Col 4 — Right sidebar: Roster + Chat stacked (wired in 04-11)
 *
 * Cols 1, 3, 4 use placeholder divs here. Plan 04-11 replaces them with real components.
 *
 * CRITICAL (04-UI-SPEC Section 5A): center column requires min-w-0 to prevent
 * CSS grid blowout when the inner board is wider than the available viewport space.
 */
import { useDraftStore } from '@/store/draft'
import { DraftBoard } from './DraftBoard'
import { PickClock } from './PickClock'

/**
 * Derives the 0-based team slot that is currently on the clock.
 * Uses currentPickNum (last completed pick, 0 = no picks yet) to find
 * which slot picks next. Odd rounds reverse direction (snake).
 */
function snakeSlot(pickNum: number, numTeams: number): number {
  const round = Math.floor(pickNum / numTeams)
  const offset = pickNum % numTeams
  return round % 2 === 0 ? offset : numTeams - 1 - offset
}

export function DraftRoom() {
  const config = useDraftStore((s) => s.config)
  const isPaused = useDraftStore((s) => s.isPaused)
  const currentPickNum = useDraftStore((s) => s.currentPickNum)

  // draft_order is string[] (team IDs). Display team ID as label until
  // team-name lookup is wired in 04-11 (PreDraftLobby populates team metadata).
  const activeTeamName = config?.draft_order
    ? (config.draft_order[snakeSlot(currentPickNum, config.draft_order.length)] ?? '—')
    : '—'

  const currentRound = config
    ? Math.floor(currentPickNum / config.num_teams) + 1
    : 1

  return (
    <div className="grid grid-cols-[200px_1fr_320px_200px] h-screen overflow-hidden bg-bg">

      {/* Column 1: Left sidebar — Queue + Alerts stacked (wired in 04-11) */}
      <div className="flex flex-col border-r border-border overflow-hidden" data-testid="queue-alerts-column">
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">Queue</span>
        </div>
        <div className="flex-1 flex items-center justify-center text-muted font-mono text-xs">
          Loading...
        </div>
      </div>

      {/* Column 2: Center-left — DraftBoard (MUST have min-w-0 — see comment above) */}
      <div className="flex flex-col min-w-0 overflow-hidden" data-testid="draft-board-column">
        {/* Board header bar — primary focal point: team name + pick clock */}
        <div className="h-10 flex items-center gap-4 px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-sm font-semibold text-text flex-1 truncate">
            {isPaused
              ? 'DRAFT PAUSED'
              : `${activeTeamName} on the clock`}
          </span>
          {config && (
            <PickClock totalSeconds={config.pick_clock_seconds} />
          )}
          <span className="font-mono text-[10px] text-muted flex-shrink-0">
            {config ? `Round ${currentRound} / ${config.num_rounds}` : ''}
          </span>
        </div>

        {/* Draft board fills remaining height */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <DraftBoard />
        </div>
      </div>

      {/* Column 3: Center-right — BestAvailable (wired in 04-11) */}
      <div className="flex flex-col border-l border-border overflow-hidden" data-testid="best-available-column">
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">Best Available</span>
        </div>
        <div className="flex-1 flex items-center justify-center text-muted font-mono text-xs">
          Loading...
        </div>
      </div>

      {/* Column 4: Right sidebar — Roster + Chat stacked (wired in 04-11) */}
      <div className="flex flex-col border-l border-border overflow-hidden" data-testid="roster-chat-column">
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">My Roster</span>
        </div>
        <div className="flex-1 flex items-center justify-center text-muted font-mono text-xs">
          Loading...
        </div>
      </div>

    </div>
  )
}
