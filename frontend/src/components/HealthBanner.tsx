import { AlertTriangle } from 'lucide-react'
import { useAuthStore } from '@/store/auth'

const PLATFORM_LABEL: Record<string, string> = {
  yahoo: 'Yahoo',
  espn: 'ESPN',
}

const RECONNECT_PATH: Record<string, string> = {
  yahoo: '/api/v1/auth/yahoo',
  espn: '/connect?reconnect=espn',
}

export default function HealthBanner() {
  const unhealthyPlatforms = useAuthStore((s) => s.unhealthyPlatforms)

  if (unhealthyPlatforms.length === 0) return null

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2">
      {unhealthyPlatforms.map((platform) => (
        <div key={platform} className="flex items-center gap-2 text-sm text-amber-600">
          <AlertTriangle size={14} />
          <span>
            Your {PLATFORM_LABEL[platform] ?? platform} connection has expired.{' '}
            <a
              href={RECONNECT_PATH[platform] ?? `/connect?reconnect=${platform}`}
              className="underline font-medium hover:text-amber-700"
            >
              Reconnect
            </a>
          </span>
        </div>
      ))}
    </div>
  )
}
