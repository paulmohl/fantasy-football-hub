/**
 * ChatPanel — live draft chat with Socket.IO message send (DR-10).
 *
 * Messages stored in useDraftStore.chatMessages (server-pushed via socket event).
 * Auto-scrolls to bottom on new message.
 * 500-char limit matches server validation in on_chat handler.
 */
import { useEffect, useRef, useState } from 'react'
import { useDraftStore } from '@/store/draft'
import { useAuthStore } from '@/store/auth'
import { getDraftSocket } from '@/lib/socket'

const MAX_MSG_LENGTH = 500

export function ChatPanel() {
  const chatMessages = useDraftStore((s) => s.chatMessages)
  // auth.ts exposes userId (camelCase) — not user_id (snake_case)
  const userId = useAuthStore((s) => s.userId ?? '')
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleSend = () => {
    const message = draft.trim()
    if (!message || sending) return
    const socket = getDraftSocket()
    if (!socket) return

    setSending(true)
    socket.emit('chat', { message }, (resp: { ok: boolean }) => {
      setSending(false)
      if (resp?.ok) setDraft('')
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatTime = (created_at: string) => {
    try {
      const ts = parseFloat(created_at) * 1000
      const d = new Date(ts)
      return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    } catch {
      return ''
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-2 py-1 space-y-1" role="log" aria-label="Draft chat" aria-live="polite">
        {chatMessages.length === 0 ? (
          <p className="text-center font-mono text-[10px] text-text-muted mt-4">
            No messages yet. Say hi!
          </p>
        ) : (
          chatMessages.map((msg, idx) => (
            <div key={idx} className="font-mono text-[11px] leading-snug">
              <span className="text-[10px] text-text-muted mr-1">{formatTime(msg.created_at)}</span>
              <span className={`mr-1 ${msg.user_id === userId ? 'text-accent font-semibold' : 'text-text-muted'}`}>
                {msg.user_id === userId ? 'You' : msg.user_id.slice(0, 6)}:
              </span>
              <span className="text-text break-words">{msg.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="flex gap-1 px-2 py-1.5 border-t border-border flex-shrink-0 bg-surface">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value.slice(0, MAX_MSG_LENGTH))}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          className="font-mono text-xs bg-bg border border-border px-2 py-1 flex-1 resize-none h-8 rounded text-text placeholder:text-text-muted focus:outline-none focus:border-accent"
          maxLength={MAX_MSG_LENGTH}
          aria-label="Chat message"
          data-testid="chat-input"
        />
        <button
          onClick={handleSend}
          disabled={!draft.trim() || sending}
          className="text-[10px] font-mono text-accent hover:text-accent-hover disabled:opacity-40 px-2 self-end pb-1"
          aria-label="Send message"
        >
          Send
        </button>
      </div>

      {/* Char count when near limit */}
      {draft.length > 400 && (
        <div className="px-2 py-0.5 flex-shrink-0">
          <span className={`font-mono text-[10px] ${draft.length >= MAX_MSG_LENGTH ? 'text-red-400' : 'text-text-muted'}`}>
            {draft.length}/{MAX_MSG_LENGTH}
          </span>
        </div>
      )}
    </div>
  )
}
