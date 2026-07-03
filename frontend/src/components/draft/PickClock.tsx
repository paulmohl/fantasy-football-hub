/**
 * PickClock — server-authoritative countdown clock (D-03 LOCKED).
 *
 * Server writes pick_deadline_epoch (UTC unix timestamp) on each pick.
 * Client computes remaining as deadline - Date.now()/1000. No drift.
 * D-06 audio (pick.mp3 / your-turn.mp3) is handled in DraftPage.tsx, not here.
 */
import { useEffect, useRef, useState } from 'react'
import { useDraftStore } from '@/store/draft'

interface PickClockProps {
  totalSeconds: number  // pick_clock_seconds from config (for progress bar)
}

export function PickClock({ totalSeconds }: PickClockProps) {
  const pickDeadlineEpoch = useDraftStore((s) => s.pickDeadlineEpoch)
  const isPaused = useDraftStore((s) => s.isPaused)
  const [remaining, setRemaining] = useState<number>(totalSeconds)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    if (!pickDeadlineEpoch || isPaused) return

    const tick = () => {
      const rem = Math.max(0, pickDeadlineEpoch - Date.now() / 1000)
      setRemaining(Math.round(rem))
    }
    tick()
    intervalRef.current = setInterval(tick, 1000)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [pickDeadlineEpoch, isPaused])

  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  const is30s = remaining <= 30 && remaining > 10   // D-03: amber warning at 30s
  const is10s = remaining <= 10 && remaining > 0    // D-03: red danger + pulse at 10s
  const pct = totalSeconds > 0 ? Math.max(0, Math.min(100, (remaining / totalSeconds) * 100)) : 0

  return (
    <div className="flex flex-col items-center gap-1">
      <span
        className={`font-mono text-[28px] font-semibold tabular-nums ${
          is10s ? 'text-danger animate-pulse' : is30s ? 'text-warning' : 'text-text'
        } ${isPaused ? 'opacity-50' : ''}`}
        aria-live={is10s ? 'assertive' : 'polite'}
        aria-label={`${display} remaining`}
      >
        {isPaused ? 'PAUSED' : display}
      </span>
      {/* Progress bar — fills accent→warning→danger as time depletes */}
      <div className="h-1 w-full rounded-full bg-border overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${
            is10s ? 'bg-danger' : is30s ? 'bg-warning' : 'bg-accent'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
