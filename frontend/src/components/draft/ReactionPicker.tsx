/**
 * ReactionPicker — 4-emoji popover for pick cell reactions (DR-11).
 *
 * Displayed as a popover when user right-clicks or long-presses a PickCell.
 * Calls socket.emit('react', {pick_num, emoji}) on selection.
 */
import { useEffect, useRef } from 'react'
import { getDraftSocket } from '@/lib/socket'

const REACTIONS = [
  { name: 'fire', emoji: '🔥', label: 'Fire pick' },
  { name: 'laugh', emoji: '😂', label: 'Funny' },
  { name: 'skeptical', emoji: '🤨', label: 'Skeptical' },
  { name: 'applause', emoji: '👏', label: 'Good pick' },
] as const

interface ReactionPickerProps {
  pickNum: number
  onClose: () => void
  position?: { top: number; left: number }
}

export function ReactionPicker({ pickNum, onClose, position }: ReactionPickerProps) {
  const ref = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const handleReact = (emojiName: string) => {
    const socket = getDraftSocket()
    if (!socket) { onClose(); return }
    socket.emit('react', { pick_num: pickNum, emoji: emojiName }, () => {
      onClose()
    })
  }

  return (
    <div
      ref={ref}
      className="absolute z-30 bg-surface border border-border rounded-lg shadow-lg p-2 flex gap-2"
      style={position ? { top: position.top, left: position.left } : undefined}
      role="menu"
      aria-label="React to pick"
      data-testid="reaction-picker"
    >
      {REACTIONS.map(({ name, emoji, label }) => (
        <button
          key={name}
          onClick={() => handleReact(name)}
          className="text-xl hover:scale-125 transition-transform cursor-pointer p-1 rounded hover:bg-surface-hover"
          aria-label={label}
          data-testid={`react-${name}`}
        >
          {emoji}
        </button>
      ))}
    </div>
  )
}
