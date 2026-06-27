import { Wind, CloudRain, CloudSnow } from 'lucide-react'

interface WeatherChipProps {
  wind_mph: number
  precipitation_mm: number
  weather_code: number
  is_indoor?: boolean
  size?: 'compact' | 'full'
}

const SNOW_CODE_MIN = 71
const SNOW_CODE_MAX = 77
const HEAVY_RAIN_CODE = 63
const HEAVY_RAIN_MM = 2.5
const WIND_THRESHOLD = 20

export function WeatherChip({
  wind_mph,
  precipitation_mm,
  weather_code,
  is_indoor = false,
  size = 'compact',
}: WeatherChipProps) {
  if (is_indoor) return null

  const hasWind = wind_mph >= WIND_THRESHOLD
  const hasRain = precipitation_mm >= HEAVY_RAIN_MM || weather_code >= HEAVY_RAIN_CODE
  const hasSnow = weather_code >= SNOW_CODE_MIN && weather_code <= SNOW_CODE_MAX

  if (!hasWind && !hasRain && !hasSnow) return null

  const Icon = hasSnow ? CloudSnow : hasRain ? CloudRain : Wind
  const label = hasWind
    ? `${Math.round(wind_mph)} mph wind`
    : hasRain
    ? 'Heavy rain'
    : 'Snow'
  const ariaLabel = `Weather alert: ${label}`

  if (size === 'compact') {
    return (
      <span
        className="bg-warning/10 rounded-full px-1.5 py-0.5 inline-flex items-center gap-0.5"
        title={ariaLabel}
        aria-label={ariaLabel}
      >
        <Icon size={14} className="text-warning" aria-hidden />
      </span>
    )
  }

  return (
    <div className="space-y-1">
      <div className="bg-raised border border-border rounded-full flex items-center gap-1.5 px-2 py-1 w-fit">
        <Icon size={14} className="text-warning" aria-label={ariaLabel} />
        <span className="text-xs font-semibold text-warning">{label}</span>
      </div>
      <p className="text-xs text-muted">Projection adjusted down</p>
    </div>
  )
}
