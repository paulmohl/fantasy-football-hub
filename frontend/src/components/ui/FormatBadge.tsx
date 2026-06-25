interface FormatBadgeProps {
  format?: string
  isDynasty?: boolean
  isKeeper?: boolean
}

export function FormatBadge({ format, isDynasty, isKeeper }: FormatBadgeProps) {
  if (isDynasty || format === 'dynasty') {
    return (
      <span className="text-xs font-semibold bg-[#1a1a3a] text-[#B39DDB] px-2 py-0.5 rounded">
        Dynasty
      </span>
    )
  }
  if (isKeeper || format === 'keeper') {
    return (
      <span className="text-xs font-semibold bg-[#2a2010] text-warning px-2 py-0.5 rounded">
        Keeper
      </span>
    )
  }
  return (
    <span className="text-xs font-semibold bg-[#1a2a1a] text-success px-2 py-0.5 rounded">
      Redraft
    </span>
  )
}
