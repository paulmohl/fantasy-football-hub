import { useState } from 'react'
import { useDraftStore } from '@/store/draft'
import { api } from '@/lib/api'

export function PreDraftLobby() {
  const config = useDraftStore((s) => s.config)
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)

  if (!config) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-text-muted font-mono text-sm">
        LOADING DRAFT...
      </div>
    )
  }

  const handleStart = async () => {
    if (!config.draft_id || config.draft_order.length === 0) {
      setStartError('Set draft order before starting')
      return
    }
    setStarting(true)
    setStartError(null)
    try {
      await api.put(`/drafts/${config.draft_id}/order`, {
        draft_order: config.draft_order,
        lock_and_start: true,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setStartError(msg ?? 'Failed to start draft')
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-bg">
      <div className="bg-surface border border-border rounded-lg p-8 flex flex-col gap-6 max-w-md w-full mx-4" data-testid="pre-draft-lobby">
        {/* Header */}
        <div className="text-center">
          <h1 className="font-mono text-xl font-bold text-text tracking-wide">PRE-DRAFT LOBBY</h1>
          <p className="font-mono text-sm text-text-muted mt-1">Draft room is ready</p>
        </div>

        {/* Draft info grid */}
        <div className="grid grid-cols-2 gap-3 font-mono text-sm">
          <div>
            <span className="text-text-muted text-[10px] tracking-widest uppercase">Teams</span>
            <p className="text-text font-semibold">{config.num_teams}</p>
          </div>
          <div>
            <span className="text-text-muted text-[10px] tracking-widest uppercase">Rounds</span>
            <p className="text-text font-semibold">{config.num_rounds}</p>
          </div>
          <div>
            <span className="text-text-muted text-[10px] tracking-widest uppercase">Pick Clock</span>
            <p className="text-text font-semibold">{config.pick_clock_seconds}s</p>
          </div>
          <div>
            <span className="text-text-muted text-[10px] tracking-widest uppercase">Status</span>
            <p className="text-amber-400 font-semibold uppercase">Pending</p>
          </div>
        </div>

        {/* Draft order (if set) */}
        {config.draft_order && config.draft_order.length > 0 && (
          <div>
            <span className="font-mono text-[10px] tracking-widest uppercase text-text-muted">Draft Order</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {config.draft_order.map((teamId, i) => (
                <span key={teamId} className="font-mono text-xs bg-surface-hover border border-border rounded px-2 py-0.5">
                  {i + 1}. {teamId.slice(0, 8)}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Start error */}
        {startError && (
          <p className="font-mono text-xs text-red-400" role="alert">{startError}</p>
        )}

        {/* Commissioner start button — shown to all; 04-12 will gate on commissioner_user_id */}
        <button
          onClick={handleStart}
          disabled={starting}
          className="w-full bg-accent text-bg font-mono text-sm py-3 rounded-lg hover:bg-accent-hover disabled:opacity-50 transition-colors"
          data-testid="start-draft-button"
        >
          {starting ? 'STARTING...' : 'START DRAFT'}
        </button>

        <p className="font-mono text-xs text-text-muted text-center">
          Waiting for commissioner to start the draft
        </p>
      </div>
    </div>
  )
}
