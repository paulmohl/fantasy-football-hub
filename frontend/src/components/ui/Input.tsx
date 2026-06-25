import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  label?: string
  errorMessage?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error, label, errorMessage, className, id, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className="block text-sm text-text mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            'w-full bg-raised border rounded-lg px-3 py-3 text-sm text-text',
            'placeholder:text-muted focus:outline-none transition-colors min-h-[44px]',
            error ? 'border-danger focus:border-danger' : 'border-border focus:border-accent',
            className,
          )}
          aria-invalid={error}
          aria-describedby={errorMessage && id ? `${id}-error` : undefined}
          {...props}
        />
        {errorMessage && (
          <p
            id={id ? `${id}-error` : undefined}
            className="mt-1 text-danger text-sm bg-danger/10 border border-danger/20 rounded-lg px-3 py-2"
          >
            {errorMessage}
          </p>
        )}
      </div>
    )
  }
)
Input.displayName = 'Input'
