/**
 * PauseOverlay — full-screen pause overlay (D-05, DR-09).
 *
 * T-4-04: Resume button shown only to commissioner. Server enforces role
 * on on_resume handler — this is UI-only gating for UX, not security.
 *
 * Rendered inside DraftRoom when isPaused=true.
 * Position: absolute inset-0 z-50 (DraftRoom must have relative positioning).
 */
import { useState } from 'react'
import { useDraftStore } from '@/store/draft'
import { useAuthStore } from '@/store/auth'
import { getDraftSocket } from '@/lib/socket'

interface PauseOverlayProps {
  commissionerUserId: string | null
}

export function PauseOverlay({ commissionerUserId }: PauseOverlayProps) {
  const isPaused = useDraftStore((s) => s.isPaused)
  const resumeCountdown = useDraftStore((s) => s.resumeCountdown)
  const userId = useAuthStore((s) => s.userId)
  const addAlert = useDraftStore((s) => s.addAlert)
  const [resuming, setResuming] = useState(false)

  if (!isPaused) return null

  // D-05 LOCKED: show countdown when resuming
  const isResuming = resumeCountdown !== null && resumeCountdown > 0

  const isCommissioner = commissionerUserId && userId && commissionerUserId === userId

  const handleResume = () => {
    const socket = getDraftSocket()
    if (!socket || resuming) return
    setResuming(true)
    socket.emit('resume', {}, (resp: { ok: boolean; error?: string }) => {
      setResuming(false)
      if (!resp?.ok) {
        addAlert(`Resume failed: ${resp?.error ?? 'unknown error'}`)
      }
    })
  }

  return (
    <div
      className="absolute inset-0 z-50 flex items-center justify-center bg-bg/80 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Draft paused"
      data-testid="pause-overlay"
    >
      <div className="bg-surface border border-border rounded-lg p-6 flex flex-col items-center gap-4 max-w-sm w-full mx-4">
        {/* Pause icon */}
        <div className="text-4xl">⏸</div>

        {isResuming ? (
          <>
            <h2 className="text-[28px] font-mono font-bold text-accent">
              Resuming in {resumeCountdown}...
            </h2>
            <p className="text-sm font-mono text-text-muted text-center">
              Get ready — the clock restarts shortly.
            </p>
          </>
        ) : (
          <>
            <h2 className="text-2xl font-mono font-bold text-amber-400">DRAFT PAUSED</h2>
            <p className="text-sm font-mono text-text-muted text-center">
              The commissioner has paused the clock.
              <br />
              Hang tight...
            </p>
          </>
        )}

        {/* Commissioner-only resume button — UI gate only; server enforces role */}
        {isCommissioner && (
          <button
            onClick={handleResume}
            disabled={resuming}
            className="bg-accent text-bg font-mono text-sm px-6 py-2 rounded hover:bg-accent-hover disabled:opacity-50 transition-colors w-full"
            aria-label="Resume draft"
            data-testid="resume-button"
          >
            {resuming ? 'Resuming...' : 'Resume Draft'}
          </button>
        )}
      </div>
    </div>
  )
}
