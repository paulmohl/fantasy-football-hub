import { useQuery, useQueryClient } from '@tanstack/react-query'
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
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { positionTone } from '@/lib/position'
import { api } from '@/lib/api'
import { useLeagueStore } from '@/store/league'
import { InjuryBadge } from './InjuryBadge'
import { ConfidenceBadge } from './ConfidenceBadge'

interface SlotData {
  slot: string
  player_id: string | null
  full_name: string | null
  position: string | null
  projected_points: number
  confidence: number
  injury_status: string | null
  is_out: boolean
  replacement_suggestion: string | null
  is_swap_suggested: boolean
  weather: { wind_mph: number; has_chip: boolean } | null
}

interface LineupResponse {
  league_id: string
  season: string
  week: number
  optimal_lineup: SlotData[]
  current_starters: string[]
  total_projected_points: number
  no_strong_call: boolean
  season_type: string
}

function NoStrongCallBanner() {
  return (
    <div
      role="alert"
      className="bg-danger/10 border border-danger/20 rounded-xl p-3 flex items-start gap-3"
    >
      <AlertTriangle size={18} className="text-danger shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-semibold text-danger">No strong call at FLEX</p>
        <p className="text-xs text-muted mt-0.5">
          All flex options are below 55% confidence this week. Go with your gut or check matchups.
        </p>
      </div>
    </div>
  )
}

function SlotChip({ slot }: { slot: string }) {
  return (
    <div
      className={cn(
        'w-9 h-9 rounded-lg flex items-center justify-center text-[10px] font-semibold shrink-0',
        positionTone(slot),
      )}
    >
      {slot.replace(/\d+$/, '')}
    </div>
  )
}

function CurrentPlayerRow({
  slot,
  onPlayerClick,
}: {
  slot: SlotData
  onPlayerClick: (slot: SlotData) => void
}) {
  const isOut = slot.is_out
  return (
    <div
      className={cn(
        'flex items-center gap-2.5 px-2.5 py-2 bg-raised/60 border border-border/70 rounded-xl h-[60px]',
        isOut && 'opacity-60',
      )}
    >
      <SlotChip slot={slot.slot} />
      <button className="flex-1 min-w-0 text-left" onClick={() => onPlayerClick(slot)}>
        <div className="flex items-center min-w-0">
          <span className="text-sm font-medium text-text truncate">{slot.full_name ?? '—'}</span>
          <InjuryBadge status={slot.injury_status} playerName={slot.full_name ?? undefined} />
        </div>
        <p className="text-xs text-muted mt-0.5 truncate">
          {slot.position ?? ''}
          {isOut && slot.replacement_suggestion && ' · start bench player'}
        </p>
      </button>
    </div>
  )
}

function DraggablePlayerRow({
  slot,
  onPlayerClick,
  isOverride,
}: {
  slot: SlotData
  onPlayerClick: (slot: SlotData) => void
  isOverride: boolean
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: slot.slot,
  })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const isOut = slot.is_out

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'group relative flex items-center gap-2.5 px-2.5 py-2 bg-raised/60 border rounded-xl transition-colors hover:bg-raised h-[60px]',
        slot.is_swap_suggested ? 'border-accent/60 bg-accent/5' : 'border-border/70',
        isOut && 'opacity-60',
        isDragging && 'opacity-50 border-dashed border-accent',
      )}
    >
      <button
        className="absolute right-0 inset-y-0 w-9 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity text-muted flex items-center justify-center cursor-grab active:cursor-grabbing"
        {...attributes}
        {...listeners}
        aria-label={`Reorder ${slot.full_name ?? slot.slot}`}
      >
        <GripVertical size={16} />
      </button>

      <button className="flex-1 min-w-0 text-left" onClick={() => onPlayerClick(slot)}>
        <div className="flex items-center min-w-0">
          <span className="text-sm font-medium text-text truncate">
            {slot.full_name ?? '—'}
            {isOverride && (
              <span className="text-xs text-muted italic font-normal ml-1">(override)</span>
            )}
          </span>
          <InjuryBadge status={slot.injury_status} playerName={slot.full_name ?? undefined} />
        </div>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="text-sm font-semibold font-mono text-text leading-none">
            {slot.projected_points.toFixed(1)}
          </span>
          <ConfidenceBadge confidence={slot.confidence} />
          {slot.is_swap_suggested && (
            <span className="text-[10px] font-semibold text-accent uppercase tracking-wide">Swap</span>
          )}
        </div>
      </button>
    </div>
  )
}

export function LineupCard({ onPlayerClick }: { onPlayerClick: (slot: SlotData) => void }) {
  const { activeLeagueId, weekOverrides, setOverride, clearOverrides } = useLeagueStore()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery<LineupResponse>({
    queryKey: ['team-lineup', activeLeagueId],
    queryFn: () =>
      api.get('/team/lineup', { params: { league_id: activeLeagueId } }).then((r) => r.data),
    enabled: !!activeLeagueId,
  })

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id || !data) return

    const week = data.week
    const activeSlot = String(active.id)
    const overSlot = String(over.id)

    const draggedEntry = data.optimal_lineup.find((s) => s.slot === activeSlot)
    if (draggedEntry?.player_id) {
      setOverride(week, overSlot, draggedEntry.player_id)
    }
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-title mb-3">Lineup Optimizer</div>
        <div className="grid grid-cols-2 gap-3">
          {[...Array(7)].map((_, i) => (
            <div key={i} className="h-12 animate-pulse bg-raised rounded-xl col-span-1" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="card">
        <p className="text-sm text-muted">
          Couldn't load lineup.{' '}
          <button
            className="text-accent font-medium underline underline-offset-2"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['team-lineup', activeLeagueId] })}
          >
            Try again
          </button>
        </p>
      </div>
    )
  }

  const starters = data.optimal_lineup.filter(
    (s) => !s.slot.startsWith('BN') && !s.slot.startsWith('IR'),
  )
  const currentWeekOverrides = weekOverrides[data.week] ?? {}
  const sortableIds = starters.map((s) => s.slot)

  const optimalTotal = data.total_projected_points
  const currentTotal = starters.reduce((sum, s) => sum + s.projected_points, 0)
  const delta = optimalTotal - currentTotal

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h2 className="card-title">Lineup Optimizer</h2>
        {Object.keys(currentWeekOverrides).length > 0 && (
          <button
            className="text-xs text-muted hover:text-danger transition-colors"
            onClick={() => clearOverrides(data.week)}
          >
            Clear overrides
          </button>
        )}
      </div>

      {data.season_type === 'off' && (
        <p className="text-xs text-muted italic mb-3">Injury data available in-season.</p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <p className="label">Current</p>
        <p className="label">Optimal</p>

        <div className="space-y-1.5">
          {starters.map((slot) => (
            <CurrentPlayerRow
              key={slot.slot}
              slot={slot}
              onPlayerClick={onPlayerClick}
            />
          ))}
        </div>

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
            <div className="space-y-1.5" aria-label="Drag to reorder lineup">
              {starters.map((slot) => {
                if (slot.slot.includes('FLEX') && data.no_strong_call) {
                  return <NoStrongCallBanner key={slot.slot} />
                }
                return (
                  <DraggablePlayerRow
                    key={slot.slot}
                    slot={slot}
                    onPlayerClick={onPlayerClick}
                    isOverride={!!currentWeekOverrides[slot.slot]}
                  />
                )
              })}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      <div className="mt-4 flex items-center gap-2 text-sm font-semibold font-mono text-text border-t border-border pt-3">
        <span>{currentTotal.toFixed(1)}</span>
        <span className="text-muted">→</span>
        <span className={delta > 0 ? 'text-success' : delta < 0 ? 'text-danger' : 'text-text'}>
          {delta > 0 ? '+' : ''}{delta.toFixed(1)}
        </span>
        <span className="text-muted text-xs font-normal">pts</span>
        <span className="ml-auto text-xs text-muted font-normal">
          Optimal: <span className="font-mono font-semibold text-text">{optimalTotal.toFixed(1)}</span>
        </span>
      </div>
    </div>
  )
}
