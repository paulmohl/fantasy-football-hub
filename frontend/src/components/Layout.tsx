import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { Home, Users, Zap, ArrowLeftRight, MoreHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'
import HealthBanner from '@/components/HealthBanner'

const tabs = [
  { to: '/team', icon: Home, label: 'My Team' },
  { to: '/connect', icon: Users, label: 'League' },
  { to: '/draft', icon: Zap, label: 'Draft' },
  { to: '/trades', icon: ArrowLeftRight, label: 'Trades' },
  { to: '/more', icon: MoreHorizontal, label: 'More' },
]

const REQUIRES_LEAGUE = ['/team', '/draft', '/trades']

export default function Layout() {
  const location = useLocation()
  const isDraft = location.pathname === '/draft'
  const hasLeagues = useAuthStore((s) => s.hasLeagues)

  return (
    <div className="flex flex-col h-screen bg-bg overflow-hidden">
      <HealthBanner />
      <main className={cn('flex-1 overflow-y-auto', isDraft && 'pb-0')}>
        <Outlet />
      </main>

      {!isDraft && (
        <nav className="shrink-0 bg-surface border-t border-border safe-area-pb">
          <div className="flex items-center justify-around h-16 px-2">
            {tabs.map(({ to, icon: Icon, label }) => {
              const isDisabled = !hasLeagues && REQUIRES_LEAGUE.some((r) => to.startsWith(r))
              return (
                <NavLink
                  key={to}
                  to={to}
                  aria-disabled={isDisabled}
                  tabIndex={isDisabled ? -1 : undefined}
                  className={({ isActive }) =>
                    cn(
                      'flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg transition-colors',
                      isDisabled
                        ? 'opacity-40 pointer-events-none text-muted'
                        : isActive
                          ? 'text-accent'
                          : 'text-muted hover:text-text',
                    )
                  }
                >
                  <Icon size={22} strokeWidth={1.75} />
                  <span className="text-xs font-semibold">{label}</span>
                </NavLink>
              )
            })}
          </div>
        </nav>
      )}
    </div>
  )
}
