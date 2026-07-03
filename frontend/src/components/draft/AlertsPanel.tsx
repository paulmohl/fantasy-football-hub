/**
 * AlertsPanel — draft event notification feed.
 *
 * Events appended by DraftPage socket handlers via useDraftStore.addAlert.
 * Shows latest 50 events (store capped at 50).
 */
import { useDraftStore } from '@/store/draft'

const ALERT_PATTERNS = [
  { prefix: '[AUTO]', color: 'text-text-muted', match: /AUTO/ },
  { prefix: '[PAUSE]', color: 'text-amber-400', match: /paus/i },
  { prefix: '[RESUME]', color: 'text-emerald-400', match: /resum/i },
  { prefix: '[PICK]', color: 'text-emerald-400', match: /pick/i },
  { prefix: '[CLOCK]', color: 'text-red-400', match: /clock|time|expir/i },
]

function getAlertStyle(msg: string): { prefix: string; color: string } {
  for (const p of ALERT_PATTERNS) {
    if (p.match.test(msg)) return { prefix: p.prefix, color: p.color }
  }
  return { prefix: '[INFO]', color: 'text-text-muted' }
}

export function AlertsPanel() {
  const alerts = useDraftStore((s) => s.alerts)

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-2 py-1 border-b border-border bg-surface flex-shrink-0 flex items-center justify-between">
        <span className="font-mono text-[10px] text-text-muted uppercase tracking-wider">Draft Alerts</span>
        {alerts.length > 0 && (
          <span className="font-mono text-[10px] text-text-muted">{alerts.length}</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-0.5" role="log" aria-live="polite" aria-label="Draft alerts">
        {alerts.length === 0 ? (
          <p className="text-center font-mono text-[10px] text-text-muted mt-4">No events yet</p>
        ) : (
          [...alerts].reverse().map((msg, idx) => {
            const { prefix, color } = getAlertStyle(msg)
            return (
              <div key={idx} className="font-mono text-[10px] leading-snug flex gap-1">
                <span className={`flex-shrink-0 ${color}`}>{prefix}</span>
                <span className="text-text-muted break-words">{msg}</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
