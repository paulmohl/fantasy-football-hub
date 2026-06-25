import { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  fullWidth?: boolean
}

export function Button({ variant = 'primary', fullWidth, className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'font-semibold rounded-lg px-4 py-3 min-h-[44px] transition-colors disabled:opacity-50',
        variant === 'primary' && 'bg-accent hover:bg-accent/90 text-white',
        variant === 'secondary' && 'bg-raised border border-border text-text hover:border-accent',
        variant === 'ghost' && 'text-accent hover:underline px-0',
        variant === 'danger' && 'bg-danger text-white hover:bg-danger/90',
        fullWidth && 'w-full',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
