import { cn } from '@/lib/utils'

interface ConfidenceBadgeProps {
  confidence: number
}

function confidenceTierClass(confidence: number): string {
  if (confidence >= 70) return 'bg-success/15 text-success'
  if (confidence >= 55) return 'bg-warning/15 text-warning'
  return 'bg-danger/15 text-danger'
}

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  return (
    <span
      className={cn(
        'text-xs font-semibold font-mono px-1.5 py-0.5 rounded-full',
        confidenceTierClass(confidence),
      )}
      aria-label={`${confidence}% confidence`}
    >
      {confidence}
    </span>
  )
}
