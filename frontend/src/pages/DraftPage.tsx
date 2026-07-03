/**
 * DraftPage — top-level draft routing shell.
 *
 * DR-05 / D-12: Routes to PreDraftLobby, DraftRoom, or DraftRecap based on
 * draft.status from the server (fetched on mount, then kept live via socket).
 *
 * NOTE: PreDraftLobby, DraftRoom, DraftRecap are created in plans 04-11 and 04-12.
 * This plan provides placeholder divs that display the status so DraftPage compiles
 * and App.tsx route works. Plan 04-11 replaces placeholders with real imports.
 */
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useDraftStore } from '@/store/draft'
import type { DraftPick } from '@/store/draft'
import { connectDraftSocket, disconnectDraftSocket } from '@/lib/socket'
import { api } from '@/lib/api'

type DraftStatus = 'pending' | 'live' | 'paused' | 'complete' | 'loading' | 'error'

// Replay event data from Redis XRANGE — all pick fields are flat strings (not nested)
interface ReplayEventData {
  id: string
  type: string
  // Flat pick fields for pick_confirmed / auto_drafted replay events
  player_id?: string
  team_id?: string
  round?: string
  is_auto_pick?: string
  pick_num?: string
  // For reaction_added events
  reactions?: Record<string, string[]>
  // For chat_message events
  message?: { user_id: string; message: string; created_at: string }
}

export function DraftPage() {
  const [searchParams] = useSearchParams()
  const draftId = searchParams.get('draft_id')
  const [status, setStatus] = useState<DraftStatus>('loading')
  const [error, setError] = useState<string | null>(null)

  const token = useAuthStore((s) => s.token)
  const lastEventId = useDraftStore((s) => s.lastEventId)
  const muteAudio = useDraftStore((s) => s.muteAudio)
  const setConfig = useDraftStore((s) => s.setConfig)
  const addPick = useDraftStore((s) => s.addPick)
  const setPickDeadline = useDraftStore((s) => s.setPickDeadline)
  const setPaused = useDraftStore((s) => s.setPaused)
  const setResumeCountdown = useDraftStore((s) => s.setResumeCountdown)
  const addChatMessage = useDraftStore((s) => s.addChatMessage)
  const updateReactions = useDraftStore((s) => s.updateReactions)
  const setLastEventId = useDraftStore((s) => s.setLastEventId)
  const addAlert = useDraftStore((s) => s.addAlert)

  // D-06 LOCKED: audio refs — initialized in effect to avoid SSR issues
  const pickSoundRef = useRef<HTMLAudioElement | null>(null)
  const turnSoundRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (!draftId || !token) {
      setStatus('error')
      setError('Missing draft_id or auth token')
      return
    }

    // Initialize audio elements (D-06 LOCKED: pick.mp3 all participants; your-turn.mp3 on-clock only)
    pickSoundRef.current = new Audio('/sounds/pick.mp3')
    turnSoundRef.current = new Audio('/sounds/your-turn.mp3')

    // Fetch initial draft state
    api
      .get(`/drafts/${draftId}`)
      .then((res) => {
        const data = res.data
        setConfig({
          draft_id: draftId,
          league_id: data.league_id,
          num_teams: data.num_teams,
          num_rounds: data.num_rounds,
          pick_clock_seconds: data.pick_clock_seconds,
          my_team_id: data.my_team_id ?? '',
          draft_order: data.draft_order ?? [],
          status: data.status,
        })
        setStatus(data.status as DraftStatus)
      })
      .catch(() => {
        setStatus('error')
        setError('Failed to load draft')
      })

    // Connect to Socket.IO /draft namespace
    const socket = connectDraftSocket({ token, draft_id: draftId })

    socket.on('connect', () => {
      // DR-15: Replay missed events since last known event
      socket.emit('reconnect', { last_event_id: lastEventId })
    })

    socket.on('pick_confirmed', (data: { pick_num: number; player_id: string; team_id: string; round: number; is_auto_pick: boolean; reactions: Record<string, string[]>; event_id: string }) => {
      addPick({ ...data, reactions: data.reactions ?? {} })
      // D-06 LOCKED: play pick sound for all participants on confirmed pick
      if (!muteAudio) pickSoundRef.current?.play().catch(() => {})
    })

    // B-new-1 / DR-08: auto_drafted emitted by arq worker via AsyncRedisManager — board must update
    socket.on('auto_drafted', (data: { pick: DraftPick; deadline: number; next_pick_num: number }) => {
      addPick({ ...data.pick, reactions: {} })
      setPickDeadline(data.deadline)
      addAlert(`${data.pick.player_id} auto-drafted`)
      if (!muteAudio) pickSoundRef.current?.play().catch(() => {})
    })

    socket.on('pick_deadline_sync', (data: { deadline: number; pick_num?: number }) => {
      setPickDeadline(data.deadline)
      // D-06 LOCKED: play your-turn sound when it becomes this user's pick
      if (data.pick_num !== undefined) {
        const state = useDraftStore.getState()
        const numTeams = state.config?.num_teams ?? 12
        const roundNum = Math.floor((data.pick_num - 1) / numTeams) + 1
        const posInRound = (data.pick_num - 1) % numTeams
        const teamSlot = roundNum % 2 === 1 ? posInRound : numTeams - 1 - posInRound
        const activeTeamId = state.config?.draft_order?.[teamSlot]
        if (!muteAudio && activeTeamId && activeTeamId === state.config?.my_team_id) {
          turnSoundRef.current?.play().catch(() => {})
        }
      }
    })

    socket.on('draft_paused', () => {
      setPaused(true)
      addAlert('Draft paused by commissioner')
    })

    // D-05 LOCKED: keep isPaused=true; show countdown overlay; unpause only when countdown hits 0
    socket.on('draft_resuming', (data: { countdown: number }) => {
      setResumeCountdown(data.countdown)
      const tick = setInterval(() => {
        setResumeCountdown((prev) => {
          if (prev === null || prev <= 1) {
            clearInterval(tick)
            setPaused(false)
            return null
          }
          return prev - 1
        })
      }, 1000)
    })

    socket.on('draft_complete', () => {
      setStatus('complete')
    })

    socket.on('chat_message', (data: { user_id: string; message: string; created_at: string }) => {
      addChatMessage(data)
    })

    socket.on('reaction_added', (data: { pick_num: number; reactions: Record<string, string[]> }) => {
      updateReactions(data.pick_num, data.reactions)
    })

    // D-07 LOCKED / DR-15: replay_event rebuilds full board state — no separate REST snapshot
    socket.on('replay_event', (data: ReplayEventData) => {
      setLastEventId(data.id)
      switch (data.type) {
        case 'pick_confirmed':
        case 'auto_drafted':
          // Stream emits flat fields — construct DraftPick (no nested data.pick key in replays)
          if (data.player_id) {
            addPick({
              pick_num: Number(data.pick_num),
              player_id: data.player_id,
              team_id: data.team_id ?? '',
              round: Number(data.round),
              is_auto_pick: data.is_auto_pick === 'true',
              reactions: {},
              event_id: data.id,
            })
          }
          break
        case 'draft_paused':
          setPaused(true)
          break
        case 'draft_resuming':
          // no-op during replay — live handler manages countdown
          break
        case 'chat_message':
          if (data.message) addChatMessage(data.message)
          break
        case 'reaction_added':
          if (data.pick_num !== undefined && data.reactions) updateReactions(Number(data.pick_num), data.reactions)
          break
        case 'draft_complete':
          setStatus('complete')
          break
      }
    })

    return () => {
      socket.off('pick_confirmed')
      socket.off('auto_drafted')
      socket.off('pick_deadline_sync')
      socket.off('draft_paused')
      socket.off('draft_resuming')
      socket.off('draft_complete')
      socket.off('chat_message')
      socket.off('reaction_added')
      socket.off('replay_event')
      disconnectDraftSocket()
    }
  }, [draftId, token])

  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-text-muted font-mono text-sm">
        CONNECTING TO DRAFT ROOM...
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-red-400 font-mono text-sm">
        {error ?? 'Draft unavailable'}
      </div>
    )
  }

  // Phase 04-11 will replace these placeholder divs with real component imports:
  // PreDraftLobby, DraftRoom, DraftRecap
  if (status === 'pending') {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-amber-400 font-mono text-sm" data-testid="pre-draft-lobby-placeholder">
        PRE-DRAFT LOBBY — status: {status}
      </div>
    )
  }

  if (status === 'complete') {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-emerald-400 font-mono text-sm" data-testid="draft-recap-placeholder">
        DRAFT RECAP — status: {status}
      </div>
    )
  }

  // 'live' | 'paused'
  return (
    <div className="h-screen bg-bg text-text font-mono" data-testid="draft-room-placeholder">
      <div className="flex items-center justify-center h-full text-sm text-text-muted">
        DRAFT ROOM — pick #{useDraftStore.getState().currentPickNum + 1} — status: {status}
      </div>
    </div>
  )
}

export default DraftPage
