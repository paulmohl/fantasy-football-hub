import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DropCandidate {
  player_id: string
  full_name: string
  position: string
  ros_value: number
  injury_status: string | null
}

interface FaabBid {
  mid_bid: number
  confidence_range: number
  min_bid: number
  max_bid: number
}

interface AddPlayerDialogProps {
  open: boolean
  onClose: () => void
  playerName: string
  waiverType: 'faab' | 'rolling'
  dropCandidates: DropCandidate[]
  faabBid: FaabBid | null
  priorityNumber?: number
}

export function AddPlayerDialog({
  open,
  onClose,
  playerName,
  waiverType,
  dropCandidates,
  faabBid,
  priorityNumber,
}: AddPlayerDialogProps) {
  const [selectedDropId, setSelectedDropId] = useState<string | null>(null)
  const [customBid, setCustomBid] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const selectedDrop = dropCandidates.find((c) => c.player_id === selectedDropId)

  function handleAdd() {
    // Phase 2 is read-only — no writes to Sleeper. Phase 3+ will call POST /api/v1/team/waiver/add
    setIsSubmitting(true)
    setTimeout(() => {
      setIsSubmitting(false)
      onClose()
    }, 500)
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40" />
        <Dialog.Content
          className="fixed bottom-0 left-0 right-0 bg-surface border-t border-border rounded-t-2xl z-50 p-6 max-h-[85vh] overflow-y-auto sm:inset-auto sm:top-1/2 sm:left-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-2xl sm:max-w-md sm:w-full"
        >
          <Dialog.Title className="text-base font-semibold text-text">
            Add {playerName}
          </Dialog.Title>

          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-muted hover:text-text transition-colors"
            aria-label="Close player add dialog"
          >
            <X size={20} />
          </button>

          <div className="mt-4 space-y-4">
            {waiverType === 'faab' && faabBid && (
              <div>
                <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">FAAB BID</p>
                <div className="bg-raised rounded-lg px-3 py-1.5 font-mono text-sm text-text inline-block mb-2">
                  ${faabBid.mid_bid} ± ${faabBid.confidence_range}
                </div>
                <input
                  type="number"
                  min={0}
                  placeholder={`Suggested: $${faabBid.mid_bid}`}
                  value={customBid}
                  onChange={(e) => setCustomBid(e.target.value)}
                  className="w-full bg-raised border border-border rounded-lg px-3 py-2 text-sm font-mono text-text min-h-[44px] focus:outline-none focus:border-accent"
                />
              </div>
            )}

            {waiverType === 'rolling' && priorityNumber !== undefined && (
              <div>
                <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-1">WAIVER PRIORITY</p>
                <p className="text-sm text-text">Priority #{priorityNumber}</p>
              </div>
            )}

            {dropCandidates.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">DROP CANDIDATE</p>
                <div className="space-y-2">
                  {dropCandidates.map((candidate) => (
                    <button
                      key={candidate.player_id}
                      onClick={() =>
                        setSelectedDropId(
                          selectedDropId === candidate.player_id ? null : candidate.player_id,
                        )
                      }
                      className={cn(
                        'w-full flex items-center gap-3 p-3 bg-raised border rounded-xl text-left transition-colors',
                        selectedDropId === candidate.player_id
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-accent/50',
                      )}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-text truncate">{candidate.full_name}</p>
                        <p className="text-xs text-muted">{candidate.position}</p>
                      </div>
                      <span className="font-mono text-xs text-muted shrink-0">
                        ROS: {candidate.ros_value}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 bg-raised border border-border rounded-xl py-3 text-sm font-semibold text-muted hover:text-text transition-colors min-h-[44px]"
            >
              Keep my roster
            </button>
            <button
              onClick={handleAdd}
              disabled={isSubmitting}
              className="flex-1 bg-accent text-white rounded-xl py-3 text-sm font-semibold hover:bg-accent/90 transition-colors min-h-[44px] disabled:opacity-50"
            >
              {isSubmitting
                ? 'Adding…'
                : selectedDrop
                ? `Add ${playerName.split(' ')[0]}, Drop ${selectedDrop.full_name.split(' ').pop()}`
                : 'Add to roster'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
