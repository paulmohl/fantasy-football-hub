import { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface OptionPillProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean
}

export function OptionPill({ selected, disabled, className, children, ...props }: OptionPillProps) {
  return (
    <button
      disabled={disabled}
      className={cn(
        'bg-raised border rounded-full px-4 py-2 text-sm font-semibold transition-all min-h-[44px]',
        selected
          ? 'bg-accent border-accent text-white'
          : 'border-border text-text hover:border-accent',
        disabled && 'opacity-40 cursor-not-allowed pointer-events-none',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
