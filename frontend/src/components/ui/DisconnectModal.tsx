import * as Dialog from '@radix-ui/react-dialog'

interface DisconnectModalProps {
  leagueName: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  loading?: boolean
}

export function DisconnectModal({ leagueName, open, onOpenChange, onConfirm, loading }: DisconnectModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-surface border border-border rounded-xl p-6 w-full max-w-sm z-50 space-y-4">
          <Dialog.Title className="text-base font-semibold text-text">
            Disconnect {leagueName}?
          </Dialog.Title>
          <Dialog.Description className="text-sm text-muted">
            Your credentials will be deleted. Cached data is kept for 30 days then removed. This cannot be undone.
          </Dialog.Description>
          <div className="flex gap-3 pt-2">
            <Dialog.Close asChild>
              <button className="flex-1 bg-raised border border-border text-text font-semibold rounded-lg px-4 py-3 min-h-[44px] hover:border-accent transition-colors">
                Keep League
              </button>
            </Dialog.Close>
            <button
              onClick={onConfirm}
              disabled={loading}
              className="flex-1 bg-danger text-white font-semibold rounded-lg px-4 py-3 min-h-[44px] hover:bg-danger/90 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Disconnecting…' : 'Disconnect League'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
