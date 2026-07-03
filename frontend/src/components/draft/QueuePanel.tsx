/**
 * QueuePanel — drag-to-reorder personal pick queue (D-09).
 *
 * Queue top player = auto-draft fallback if clock expires (DR-04).
 * Reorder updates local store immediately (optimistic), then syncs to server.
 * Uses @dnd-kit/sortable v10 — replicate LineupCard.tsx drag pattern.
 */
import { useCallback } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useDraftStore } from '@/store/draft'
import { getDraftSocket } from '@/lib/socket'
import { PositionBadge } from './PositionBadge'

// ---- SortableQueueItem ----

interface SortableQueueItemProps {
  player_id: string
  rank: number
  name: string
  position: string
  nfl_team: string
  onRemove: (id: string) => void
}

function SortableQueueItem({ player_id, rank, name, position, nfl_team, onRemove }: SortableQueueItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: player_id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-1.5 px-2 py-1.5 border-b border-border bg-surface hover:bg-surface-hover
        ${isDragging ? 'shadow-lg z-10 relative' : ''}`}
      data-testid={`queue-item-${player_id}`}
    >
      {/* Drag handle */}
      <span
        {...attributes}
        {...listeners}
        className="text-text-muted cursor-grab active:cursor-grabbing text-[12px] flex-shrink-0 select-none"
        aria-label="Drag to reorder"
      >
        &#10271;
      </span>

      {/* Queue rank */}
      <span className="text-[10px] text-text-muted w-4 text-right flex-shrink-0 tabular-nums">{rank}</span>

      {/* Position badge */}
      <PositionBadge position={position} />

      {/* Name + team */}
      <div className="flex flex-col min-w-0 flex-1">
        <span className="font-mono text-[11px] text-text truncate">{name}</span>
        <span className="font-mono text-[10px] text-text-muted">{nfl_team}</span>
      </div>

      {/* Remove button */}
      <button
        onClick={() => onRemove(player_id)}
        className="text-[10px] font-mono text-text-muted hover:text-red-400 flex-shrink-0 px-1"
        aria-label={`Remove ${name} from queue`}
      >
        &#10005;
      </button>
    </div>
  )
}

// ---- QueuePanel ----

export function QueuePanel() {
  const queuedPlayerIds = useDraftStore((s) => s.queuedPlayerIds)
  const availablePlayers = useDraftStore((s) => s.availablePlayers)
  const reorderQueue = useDraftStore((s) => s.reorderQueue)
  const removeFromQueue = useDraftStore((s) => s.removeFromQueue)

  // Build player lookup for rendering
  const playerMap = Object.fromEntries(availablePlayers.map((p) => [p.player_id, p]))

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event
      if (!over || active.id === over.id) return

      const oldIndex = queuedPlayerIds.indexOf(String(active.id))
      const newIndex = queuedPlayerIds.indexOf(String(over.id))
      if (oldIndex === -1 || newIndex === -1) return

      const newOrder = arrayMove(queuedPlayerIds, oldIndex, newIndex)

      // Optimistic update
      reorderQueue(newOrder)

      // Sync to server
      const socket = getDraftSocket()
      if (socket) {
        socket.emit('queue_reorder', { order: newOrder })
      }
    },
    [queuedPlayerIds, reorderQueue]
  )

  const handleRemove = useCallback(
    (player_id: string) => {
      removeFromQueue(player_id)
      const socket = getDraftSocket()
      if (socket) {
        socket.emit('queue_remove', { player_id })
      }
    },
    [removeFromQueue]
  )

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-2 py-1 border-b border-border bg-surface flex-shrink-0 flex items-center justify-between">
        <span className="font-mono text-[10px] text-text-muted uppercase tracking-wider">My Queue</span>
        {queuedPlayerIds.length > 0 && (
          <span className="font-mono text-[10px] text-text-muted">{queuedPlayerIds.length} queued</span>
        )}
      </div>

      {/* Sortable list */}
      <div className="flex-1 overflow-y-auto">
        {queuedPlayerIds.length === 0 ? (
          <div className="px-2 py-4 text-center font-mono text-xs text-text-muted">
            <p>No players queued</p>
            <p className="mt-1 text-[10px]">Add from Best Available &#8594;</p>
          </div>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={queuedPlayerIds} strategy={verticalListSortingStrategy}>
              {queuedPlayerIds.map((player_id, idx) => {
                const player = playerMap[player_id]
                return (
                  <SortableQueueItem
                    key={player_id}
                    player_id={player_id}
                    rank={idx + 1}
                    name={player?.name ?? player_id}
                    position={player?.position ?? '—'}
                    nfl_team={player?.nfl_team ?? ''}
                    onRemove={handleRemove}
                  />
                )
              })}
            </SortableContext>
          </DndContext>
        )}
      </div>

      {/* Footer: auto-pick hint */}
      {queuedPlayerIds.length > 0 && (
        <div className="px-2 py-1 border-t border-border bg-surface/50 flex-shrink-0">
          <span className="font-mono text-[10px] text-text-muted">
            Auto-pick: {playerMap[queuedPlayerIds[0]]?.name ?? queuedPlayerIds[0]}
          </span>
        </div>
      )}
    </div>
  )
}
