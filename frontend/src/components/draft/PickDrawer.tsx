/**
 * PickDrawer — bottom slide-in sheet for player detail and quick-pick action (DR-12).
 *
 * Opens when user clicks a PickCell (empty or filled).
 * For empty cells (future picks): shows player detail + Quick Pick + Add to Queue.
 * For filled cells: shows who drafted the player + reactions summary.
 * Quick Pick is only enabled when it's the current user's turn.
 */
import { useEffect } from 'react'
import { useDraftStore } from '@/store/draft'
import { getDraftSocket } from '@/lib/socket'
import { PositionBadge } from './PositionBadge'

export interface PickDrawerState {
  pickNum: number
  playerId: string | null  // null = empty cell (future pick)
  isOpen: boolean
}

interface PickDrawerProps {
  state: PickDrawerState
  onClose: () => void
}

export function PickDrawer({ state, onClose }: PickDrawerProps) {
  const { pickNum, playerId, isOpen } = state
  const availablePlayers = useDraftStore((s) => s.availablePlayers)
  const picks = useDraftStore((s) => s.picks)
  const currentPickNum = useDraftStore((s) => s.currentPickNum)
  const config = useDraftStore((s) => s.config)
  const addToQueue = useDraftStore((s) => s.addToQueue)
  const reactions = useDraftStore((s) => s.reactions[pickNum])

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  if (!isOpen) return null

  // Find player
  const player = playerId ? availablePlayers.find((p) => p.player_id === playerId) : null
  const existingPick = picks.find((p) => p.pick_num === pickNum)
  const draftedPlayer = existingPick
    ? availablePlayers.find((p) => p.player_id === existingPick.player_id) ?? null
    : null

  // Is it the viewer's turn?
  const isMyTurn = config
    ? (() => {
        if (pickNum !== currentPickNum + 1) return false
        const numTeams = config.num_teams
        const roundNum = Math.floor((pickNum - 1) / numTeams) + 1
        const posInRound = (pickNum - 1) % numTeams
        const teamSlot = roundNum % 2 === 1 ? posInRound : numTeams - 1 - posInRound
        const teamAtSlot = config.draft_order[teamSlot]
        return teamAtSlot === config.my_team_id
      })()
    : false

  const handleQuickPick = () => {
    if (!playerId) return
    const socket = getDraftSocket()
    if (!socket) return
    socket.emit('pick', { player_id: playerId }, (resp: { ok: boolean; error?: string }) => {
      if (resp?.ok) onClose()
      else console.warn('Quick pick rejected:', resp?.error)
    })
  }

  const handleAddToQueue = () => {
    if (!playerId) return
    addToQueue(playerId)
    const socket = getDraftSocket()
    if (socket) socket.emit('queue_add', { player_id: playerId })
    onClose()
  }

  const displayPlayer = player ?? draftedPlayer

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-30 bg-bg/40 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className="fixed bottom-0 left-0 right-0 z-40 bg-surface border-t border-border rounded-t-xl p-4 sm:max-w-md sm:left-auto sm:right-4 sm:rounded-xl sm:bottom-4"
        role="dialog"
        aria-modal="true"
        aria-label={displayPlayer ? `Player detail: ${displayPlayer.name}` : `Pick ${pickNum}`}
        data-testid="pick-drawer"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-text-muted text-sm hover:text-text"
          aria-label="Close drawer"
        >
          ✕
        </button>

        {displayPlayer ? (
          <div className="flex flex-col gap-3">
            {/* Player header */}
            <div className="flex items-start gap-2">
              <PositionBadge position={displayPlayer.position} />
              <div>
                <h2 className="text-xl font-mono font-bold text-text leading-tight">
                  {displayPlayer.name}
                </h2>
                <div className="flex gap-2 font-mono text-sm text-text-muted">
                  <span>{displayPlayer.nfl_team}</span>
                  {displayPlayer.bye_week && <span>· BYE {displayPlayer.bye_week}</span>}
                </div>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex gap-3 font-mono text-sm">
              <span className="text-text-muted">ADP <span className="text-text">#{displayPlayer.overall_rank}</span></span>
              {displayPlayer.adp_grade && (
                <span className="text-text-muted">Grade <span className="text-text font-semibold">{displayPlayer.adp_grade}</span></span>
              )}
              {displayPlayer.tier && (
                <span className="text-text-muted">Tier <span className="text-text">{displayPlayer.tier}</span></span>
              )}
            </div>

            {/* Pick status */}
            {existingPick ? (
              <div className="font-mono text-sm text-text-muted">
                Drafted at pick #{existingPick.pick_num}
                {existingPick.is_auto_pick && ' (auto-pick)'}
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {/* Quick Pick — only when my turn */}
                <button
                  onClick={handleQuickPick}
                  disabled={!isMyTurn || !playerId}
                  className="w-full bg-accent text-bg font-mono text-sm py-2 rounded-lg hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  data-testid="quick-pick-button"
                  aria-label={isMyTurn ? `Draft ${displayPlayer.name}` : 'Not your turn'}
                >
                  {isMyTurn ? `Draft ${displayPlayer.name}` : 'Not Your Turn'}
                </button>

                {/* Add to Queue */}
                <button
                  onClick={handleAddToQueue}
                  className="w-full border border-border text-text-muted font-mono text-sm py-2 rounded-lg hover:bg-surface-hover transition-colors"
                  aria-label={`Add ${displayPlayer.name} to queue`}
                >
                  Add to Queue
                </button>
              </div>
            )}

            {/* Reactions summary */}
            {reactions && Object.keys(reactions).length > 0 && (
              <div className="flex gap-2 flex-wrap">
                {Object.entries(reactions).map(([emoji, users]) => {
                  const emojiChar = ({ fire: '🔥', laugh: '😂', skeptical: '🤨', applause: '👏' } as Record<string, string>)[emoji] ?? emoji
                  return (
                    <span key={emoji} className="font-mono text-sm">
                      {emojiChar} <span className="text-text-muted text-xs">{users.length}</span>
                    </span>
                  )
                })}
              </div>
            )}
          </div>
        ) : (
          <div className="font-mono text-sm text-text-muted">
            Pick #{pickNum} — no player data available
          </div>
        )}
      </div>
    </>
  )
}
