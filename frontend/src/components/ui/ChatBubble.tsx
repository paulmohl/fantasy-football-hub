import { cn } from '@/lib/utils'

interface ChatBubbleProps {
  variant: 'app' | 'user'
  children: React.ReactNode
  className?: string
}

export function ChatBubble({ variant, children, className }: ChatBubbleProps) {
  return (
    <div
      className={cn(
        'rounded-[20px] py-3 px-4 text-sm animate-fade-in',
        variant === 'app' && 'bg-surface border border-border text-text self-start max-w-[85%]',
        variant === 'user' && 'bg-accent text-white self-end ml-auto max-w-[85%]',
        className,
      )}
    >
      {children}
    </div>
  )
}
