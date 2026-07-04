/**
 * DraftRoom — Bloomberg Terminal 4-column layout shell (D-01 LOCKED).
 *
 * Columns (left to right, per D-01):
 *   [200px]  Col 1 — Left sidebar: QueuePanel + AlertsPanel stacked
 *   [1fr]    Col 2 — Center-left: DraftBoard — primary focal point
 *   [320px]  Col 3 — Center-right: BestAvailable
 *   [200px]  Col 4 — Right sidebar: RosterPanel + ChatPanel stacked
 *
 * CRITICAL (04-UI-SPEC Section 5A): center column requires min-w-0 to prevent
 * CSS grid blowout when the inner board is wider than the available viewport space.
 * CRITICAL: outer div must be `relative` for PauseOverlay `absolute inset-0` to work.
 */
import { useState } from 'react'
import { useDraftStore } from '@/store/draft'
import { DraftBoard } from './DraftBoard'
import { PickClock } from './PickClock'
import { QueuePanel } from './QueuePanel'
import { AlertsPanel } from './AlertsPanel'
import { BestAvailable } from './BestAvailable'
import { RosterPanel } from './RosterPanel'
import { ChatPanel } from './ChatPanel'
import { PauseOverlay } from './PauseOverlay'
import { PickDrawer } from './PickDrawer'
import type { PickDrawerState } from './PickDrawer'

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

  const [drawerState, setDrawerState] = useState<PickDrawerState>({
    pickNum: 0,
    playerId: null,
    isOpen: false,
  })

  const handlePickClick = (pickNum: number) => {
    const picks = useDraftStore.getState().picks
    const existingPick = picks.find((p) => p.pick_num === pickNum)
    setDrawerState({
      pickNum,
      playerId: existingPick?.player_id ?? null,
      isOpen: true,
    })
  }

  const handleDrawerClose = () => {
    setDrawerState((prev) => ({ ...prev, isOpen: false }))
  }

  const activeTeamName = config?.draft_order
    ? (config.draft_order[snakeSlot(currentPickNum, config.draft_order.length)] ?? '—')
    : '—'

  const currentRound = config
    ? Math.floor(currentPickNum / config.num_teams) + 1
    : 1

  // commissioner_user_id added to config in plan 04-12; null until then
  const commissionerUserId = (config as (typeof config & { commissioner_user_id?: string }) | null)?.commissioner_user_id ?? null

  return (
    <div className="relative grid grid-cols-[200px_1fr_320px_200px] h-screen overflow-hidden bg-bg">

      {/* Column 1: Left sidebar — QueuePanel + AlertsPanel stacked */}
      <div className="flex flex-col border-r border-border overflow-hidden" data-testid="queue-alerts-column">
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">Queue</span>
        </div>
        <div className="flex-[3] min-h-0 overflow-hidden">
          <QueuePanel />
        </div>
        <div className="h-px bg-border flex-shrink-0" />
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">Alerts</span>
        </div>
        <div className="flex-[2] min-h-0 overflow-hidden">
          <AlertsPanel />
        </div>
      </div>

      {/* Column 2: Center-left — DraftBoard (MUST have min-w-0 — see comment above) */}
      <div className="flex flex-col min-w-0 overflow-hidden" data-testid="draft-board-column">
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

        <div className="flex-1 min-h-0 overflow-hidden">
          <DraftBoard onPickClick={handlePickClick} />
        </div>
      </div>

      {/* Column 3: Center-right — BestAvailable */}
      <div className="flex flex-col border-l border-border overflow-hidden" data-testid="best-available-column">
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">Best Available</span>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <BestAvailable />
        </div>
      </div>

      {/* Column 4: Right sidebar — RosterPanel + ChatPanel stacked */}
      <div className="flex flex-col border-l border-border overflow-hidden" data-testid="roster-chat-column">
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">My Roster</span>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <RosterPanel />
        </div>
        <div className="h-px bg-border flex-shrink-0" />
        <div className="h-8 flex items-center px-3 border-b border-border bg-surface flex-shrink-0">
          <span className="font-mono text-[10px] font-semibold tracking-widest text-muted uppercase">Chat</span>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <ChatPanel />
        </div>
      </div>

      {/* PauseOverlay — absolute inset-0 z-50 (D-05 LOCKED) */}
      <PauseOverlay commissionerUserId={commissionerUserId} />

      {/* PickDrawer — fixed bottom sheet, managed by DraftRoom */}
      <PickDrawer state={drawerState} onClose={handleDrawerClose} />

    </div>
  )
}
