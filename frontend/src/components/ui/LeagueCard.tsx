import { cn } from '@/lib/utils'
import { FormatBadge } from './FormatBadge'

interface LeagueItem {
  league_id: string
  name: string
  season: string
  total_rosters: number
  draft_type?: string
  settings?: { type?: string; num_keepers?: number }
}

interface LeagueCardProps {
  league: LeagueItem
  selected: boolean
  onToggle: (id: string) => void
}

export function LeagueCard({ league, selected, onToggle }: LeagueCardProps) {
  const isDynasty = league.settings?.type === 'dynasty'
  const isKeeper = (league.settings?.num_keepers ?? 0) > 0

  return (
    <button
      type="button"
      onClick={() => onToggle(league.league_id)}
      className={cn(
        'w-full bg-raised border rounded-[10px] p-3 flex items-center gap-3 text-left transition-colors',
        selected ? 'border-accent bg-[#0e1a2e]' : 'border-border hover:border-accent/50',
      )}
      role="checkbox"
      aria-checked={selected}
    >
      <div
        className={cn(
          'w-[18px] h-[18px] rounded flex items-center justify-center flex-shrink-0 border',
          selected ? 'bg-accent border-accent' : 'border-border bg-transparent',
        )}
      >
        {selected && (
          <span className="text-white text-[11px] font-semibold leading-none">✓</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-text truncate">{league.name}</p>
        <p className="text-xs text-muted">
          {league.total_rosters} teams · {league.season}
        </p>
      </div>
      <FormatBadge isDynasty={isDynasty} isKeeper={isKeeper} />
    </button>
  )
}
