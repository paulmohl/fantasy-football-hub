import { cn } from '@/lib/utils'

type HealthStatus = 'healthy' | 'unhealthy' | 'syncing'

interface HealthDotProps {
  status: HealthStatus
  onReconnect?: () => void
}

export function HealthDot({ status, onReconnect }: HealthDotProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full',
          status === 'healthy' && 'bg-success',
          status === 'unhealthy' && 'bg-danger',
          status === 'syncing' && 'bg-warning animate-pulse',
        )}
      />
      {status === 'healthy' && <span className="text-xs text-success">Connected</span>}
      {status === 'unhealthy' && (
        <span className="text-xs text-danger">
          Sync failed —{' '}
          {onReconnect && (
            <button onClick={onReconnect} className="text-accent hover:underline">
              Reconnect
            </button>
          )}
        </span>
      )}
      {status === 'syncing' && <span className="text-xs text-warning">Syncing…</span>}
    </div>
  )
}
