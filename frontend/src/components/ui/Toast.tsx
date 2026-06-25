import * as ToastPrimitive from '@radix-ui/react-toast'
import { createContext, useContext, useState } from 'react'
import { cn } from '@/lib/utils'

type ToastVariant = 'info' | 'error'

interface ToastItem {
  id: string
  message: string
  variant: ToastVariant
  sticky?: boolean
}

interface ToastContextType {
  toast: (message: string, variant?: ToastVariant, sticky?: boolean) => void
}

const ToastContext = createContext<ToastContextType>({ toast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  function toast(message: string, variant: ToastVariant = 'info', sticky = false) {
    const id = crypto.randomUUID()
    setToasts((prev) => [...prev, { id, message, variant, sticky }])
    if (!sticky) {
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000)
    }
  }

  return (
    <ToastContext.Provider value={{ toast }}>
      <ToastPrimitive.Provider>
        {children}
        {toasts.map((t) => (
          <ToastPrimitive.Root
            key={t.id}
            open
            onOpenChange={(open) => {
              if (!open) setToasts((prev) => prev.filter((item) => item.id !== t.id))
            }}
            duration={t.sticky ? Infinity : 4000}
          >
            <ToastPrimitive.Description
              className={cn(
                'bg-surface border rounded-lg px-4 py-3 shadow-lg text-sm text-text fixed top-4 right-4 z-50',
                t.variant === 'error' ? 'border-danger/40' : 'border-border',
              )}
            >
              <span>{t.message}</span>
              {t.sticky && (
                <ToastPrimitive.Close className="ml-3 text-muted hover:text-text text-xs">
                  Dismiss
                </ToastPrimitive.Close>
              )}
            </ToastPrimitive.Description>
          </ToastPrimitive.Root>
        ))}
        <ToastPrimitive.Viewport />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  )
}
