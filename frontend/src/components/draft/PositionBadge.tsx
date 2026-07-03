/**
 * PositionBadge — colored pill showing position abbreviation.
 * Colors per 04-UI-SPEC Section 4 / D-02 (Bloomberg Terminal palette).
 * Custom tokens (text-pos-*, bg-pos-*) defined in tailwind.config.
 */
const POSITION_CLASSES: Record<string, string> = {
  QB:  'text-pos-qb bg-pos-qb/10',
  RB:  'text-pos-rb bg-pos-rb/10',
  WR:  'text-pos-wr bg-pos-wr/10',
  TE:  'text-pos-te bg-pos-te/10',
  K:   'text-pos-k  bg-pos-k/10',
  DEF: 'text-pos-def bg-pos-def/10',
}

interface PositionBadgeProps {
  position: string
  className?: string
}

export function PositionBadge({ position, className = '' }: PositionBadgeProps) {
  const colorClass = POSITION_CLASSES[position] ?? 'text-muted bg-surface'
  return (
    <span
      className={`inline-flex items-center justify-center rounded px-1 py-0.5 font-mono text-[10px] font-semibold leading-none ${colorClass} ${className}`}
    >
      {position}
    </span>
  )
}
