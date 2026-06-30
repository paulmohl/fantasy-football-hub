interface PlatformIconProps {
  platform: 'sleeper' | 'yahoo' | 'espn'
  size?: number
}

const ICON_CONFIG = {
  sleeper: { label: 'S', bg: 'bg-green-500', text: 'text-white' },
  yahoo: { label: 'Y!', bg: 'bg-purple-600', text: 'text-white' },
  espn: { label: 'E', bg: 'bg-red-600', text: 'text-white' },
}

export function PlatformIcon({ platform, size = 36 }: PlatformIconProps) {
  const config = ICON_CONFIG[platform] ?? { label: '?', bg: 'bg-muted', text: 'text-white' }
  return (
    <div
      className={`flex items-center justify-center rounded-lg font-bold text-xs shrink-0 ${config.bg} ${config.text}`}
      style={{ width: size, height: size }}
      aria-label={platform}
    >
      {config.label}
    </div>
  )
}
