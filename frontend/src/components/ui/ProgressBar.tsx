import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

interface ProgressBarProps {
  estimatedSeconds?: number
  pulsing?: boolean
  className?: string
}

export function ProgressBar({ estimatedSeconds = 10, pulsing = false, className }: ProgressBarProps) {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    if (pulsing) return
    const start = Date.now()
    const interval = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000
      const pct = Math.min(95, (elapsed / estimatedSeconds) * 100)
      setWidth(pct)
      if (pct >= 95) clearInterval(interval)
    }, 100)
    return () => clearInterval(interval)
  }, [estimatedSeconds, pulsing])

  return (
    <div className={cn('h-1 bg-border rounded-full overflow-hidden', className)}>
      <div
        className={cn(
          'h-full bg-accent rounded-full transition-all',
          pulsing && 'animate-pulse w-full',
        )}
        style={!pulsing ? { width: `${width}%`, transition: 'width 0.1s linear' } : undefined}
      />
    </div>
  )
}
