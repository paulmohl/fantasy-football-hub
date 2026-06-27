import { cn } from '@/lib/utils'

const INJURY_CONFIG: Record<string, { label: string; className: string }> = {
  Questionable: { label: 'Q',    className: 'bg-warning/15 text-warning' },
  Doubtful:     { label: 'D',    className: 'bg-warning/20 text-warning' },
  Out:          { label: 'OUT',  className: 'bg-danger/15 text-danger' },
  IR:           { label: 'IR',   className: 'bg-danger/10 text-danger' },
  Suspended:    { label: 'SUSP', className: 'bg-danger/10 text-danger' },
  PUP:          { label: 'PUP',  className: 'bg-danger/10 text-danger' },
  NA:           { label: 'NA',   className: 'bg-danger/10 text-danger' },
}

interface InjuryBadgeProps {
  status: string | null | undefined
  playerName?: string
}

export function InjuryBadge({ status, playerName }: InjuryBadgeProps) {
  if (!status) return null
  const config = INJURY_CONFIG[status]
  if (!config) return null

  return (
    <span
      className={cn(
        'text-xs font-semibold font-mono rounded px-1 py-0.5 ml-1.5',
        config.className,
      )}
      title={`${status}${playerName ? ` — ${playerName}` : ''}`}
      aria-label={`${status}${playerName ? ` — ${playerName}` : ''}`}
    >
      {config.label}
    </span>
  )
}
