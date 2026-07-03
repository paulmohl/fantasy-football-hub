/**
 * Zustand draft store — client state for the live draft room.
 *
 * PERSISTENCE RULE (D-07, 04-RESEARCH Pattern 8):
 * Only lastEventId, muteAudio, and queuedPlayerIds survive page refresh.
 * All other state (picks, available players, draft status, deadlines) is volatile
 * and must be reconstructed from the server on reconnect via the replay mechanism.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ---- Types ----

export interface DraftPick {
  pick_num: number
  round: number
  player_id: string
  team_id: string
  is_auto_pick: boolean
  reactions: Record<string, string[]>
  event_id?: string
}

export interface DraftPlayer {
  player_id: string
  name: string
  position: string
  nfl_team: string
  bye_week?: number
  overall_rank: number
  tier?: number
  adp_grade?: string
  isDrafted?: boolean  // D-10: dim in place (opacity-40, strikethrough) rather than remove
}

export interface DraftConfig {
  draft_id: string
  league_id: string
  num_teams: number
  num_rounds: number
  pick_clock_seconds: number
  my_team_id: string
  draft_order: string[]  // team_id[] in snake order
  status: 'pending' | 'live' | 'paused' | 'complete'
}

export interface DraftState {
  // Volatile — reconstructed on reconnect
  config: DraftConfig | null
  picks: DraftPick[]
  availablePlayers: DraftPlayer[]
  currentPickNum: number
  pickDeadlineEpoch: number | null
  isPaused: boolean
  resumeCountdown: number | null    // D-05: seconds remaining before clock restarts on resume
  myRoster: DraftPick[]
  chatMessages: Array<{ user_id: string; message: string; created_at: string }>
  alerts: string[]
  reactions: Record<number, Record<string, string[]>>  // pick_num → {emoji: user_ids[]}

  // Persisted — survive refresh
  lastEventId: string
  muteAudio: boolean
  queuedPlayerIds: string[]

  // Actions — store mutations
  setConfig: (config: DraftConfig) => void
  addPick: (pick: DraftPick) => void
  setAvailablePlayers: (players: DraftPlayer[]) => void
  setCurrentPickNum: (n: number) => void
  setPickDeadline: (epoch: number | null) => void
  setPaused: (paused: boolean) => void
  setLastEventId: (id: string) => void
  addChatMessage: (msg: { user_id: string; message: string; created_at: string }) => void
  addAlert: (msg: string) => void
  setMuteAudio: (mute: boolean) => void
  addToQueue: (player_id: string) => void
  removeFromQueue: (player_id: string) => void
  reorderQueue: (ids: string[]) => void
  updateReactions: (pick_num: number, reactions: Record<string, string[]>) => void
  setResumeCountdown: (n: number | null | ((prev: number | null) => number | null)) => void
  reset: () => void
}

const initialVolatile = {
  config: null,
  picks: [],
  availablePlayers: [],
  currentPickNum: 0,
  pickDeadlineEpoch: null,
  isPaused: false,
  resumeCountdown: null,
  myRoster: [],
  chatMessages: [],
  alerts: [],
  reactions: {},
}

export const useDraftStore = create<DraftState>()(
  persist(
    (set, get) => ({
      // Volatile defaults
      ...initialVolatile,

      // Persisted defaults
      lastEventId: '-',
      muteAudio: false,
      queuedPlayerIds: [],

      // Config
      setConfig: (config) => set({ config }),

      // Pick management
      addPick: (pick) =>
        set((state) => {
          const picks = [...state.picks, pick]
          const myRoster = get().config?.my_team_id === pick.team_id
            ? [...state.myRoster, pick]
            : state.myRoster
          // D-10: dim drafted players in place (opacity-40 strikethrough) rather than removing
          // BestAvailable renders isDrafted players with 'opacity-40 line-through' for tier context
          const availablePlayers = state.availablePlayers.map(
            (p) => p.player_id === pick.player_id ? { ...p, isDrafted: true } : p
          )
          return {
            picks,
            myRoster,
            availablePlayers,
            currentPickNum: Math.max(state.currentPickNum, pick.pick_num),
            lastEventId: pick.event_id ?? state.lastEventId,
          }
        }),

      setAvailablePlayers: (players) => set({ availablePlayers: players }),
      setCurrentPickNum: (n) => set({ currentPickNum: n }),
      setPickDeadline: (epoch) => set({ pickDeadlineEpoch: epoch }),
      setPaused: (paused) => set({ isPaused: paused }),
      setResumeCountdown: (n) =>
        set((state) => ({
          resumeCountdown: typeof n === 'function' ? n(state.resumeCountdown) : n,
        })),
      setLastEventId: (id) => set({ lastEventId: id }),

      // Chat
      addChatMessage: (msg) =>
        set((state) => ({ chatMessages: [...state.chatMessages, msg].slice(-200) })),

      // Alerts
      addAlert: (msg) =>
        set((state) => ({ alerts: [...state.alerts, msg].slice(-50) })),

      // Audio
      setMuteAudio: (mute) => set({ muteAudio: mute }),

      // Queue (D-09) — queuedPlayerIds is persisted
      addToQueue: (player_id) =>
        set((state) => {
          if (state.queuedPlayerIds.includes(player_id)) return state
          return { queuedPlayerIds: [...state.queuedPlayerIds, player_id] }
        }),
      removeFromQueue: (player_id) =>
        set((state) => ({ queuedPlayerIds: state.queuedPlayerIds.filter((id) => id !== player_id) })),
      reorderQueue: (ids) => set({ queuedPlayerIds: ids }),

      // Reactions
      updateReactions: (pick_num, reactions) =>
        set((state) => ({
          reactions: { ...state.reactions, [pick_num]: reactions },
        })),

      // Reset volatile on new draft
      reset: () => set({ ...initialVolatile }),
    }),
    {
      name: 'draft-storage',
      // CRITICAL: Only persist non-volatile state
      partialize: (state) => ({
        lastEventId: state.lastEventId,
        muteAudio: state.muteAudio,
        queuedPlayerIds: state.queuedPlayerIds,
      }),
    }
  )
)
