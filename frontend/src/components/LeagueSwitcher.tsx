import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { ChevronDown } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useLeagueStore } from '@/store/league'

interface LeagueOption {
  league_id: string
  name: string
  season: string
  platform: string
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '…' : s
}

export function LeagueSwitcher() {
  const { activeLeagueId, setActiveLeague } = useLeagueStore()

  const { data: myTeam } = useQuery<{ leagues: LeagueOption[] }>({
    queryKey: ['my-team-leagues'],
    queryFn: () => api.get('/team/my').then((r) => r.data),
  })

  const leagues = myTeam?.leagues ?? []
  if (leagues.length <= 1) return null

  const active = leagues.find((l) => l.league_id === activeLeagueId) ?? leagues[0]

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          className="bg-raised border border-border rounded-lg px-3 py-1.5 flex items-center gap-2 text-xs font-semibold text-text min-h-[36px] hover:border-accent/50 transition-colors"
          aria-label="Switch league"
        >
          <span className="bg-[#15BC7E]/15 text-[#15BC7E] text-xs font-semibold px-1 py-0.5 rounded uppercase">
            {active.platform === 'sleeper' ? 'SLP' : active.platform.slice(0, 3).toUpperCase()}
          </span>
          <span className="truncate max-w-[120px]">{truncate(active.name, 20)}</span>
          <span className="font-mono text-xs text-muted shrink-0">{active.season}</span>
          <ChevronDown size={14} className="text-muted shrink-0" />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="bg-surface border border-border rounded-xl shadow-lg min-w-[240px] z-50 py-1"
          sideOffset={4}
          align="end"
        >
          {leagues.map((league) => {
            const isActive = league.league_id === (activeLeagueId ?? leagues[0]?.league_id)
            return (
              <DropdownMenu.Item
                key={league.league_id}
                onSelect={() => setActiveLeague(league.league_id)}
                className={cn(
                  'px-4 py-3 flex items-center gap-3 hover:bg-raised cursor-pointer outline-none',
                  isActive && 'bg-raised border-l-2 border-accent',
                )}
              >
                <span className="bg-[#15BC7E]/15 text-[#15BC7E] text-xs font-semibold px-1 py-0.5 rounded">
                  {league.platform === 'sleeper' ? 'SLP' : league.platform.slice(0, 3).toUpperCase()}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-text truncate">{league.name}</div>
                  <div className="text-xs text-muted font-mono">{league.season}</div>
                </div>
              </DropdownMenu.Item>
            )
          })}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
