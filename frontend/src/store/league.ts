import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface LineupOverride {
  [slot: string]: string  // slot_type (e.g. "RB1") -> player_id
}

interface LeagueState {
  activeLeagueId: string | null
  weekOverrides: Record<number, LineupOverride>  // week number -> slot overrides
  setActiveLeague: (id: string) => void
  setOverride: (week: number, slot: string, playerId: string) => void
  clearOverrides: (week: number) => void
  clearAllOverrides: () => void
}

export const useLeagueStore = create<LeagueState>()(
  persist(
    (set) => ({
      activeLeagueId: null,
      weekOverrides: {},

      setActiveLeague: (id) => set({ activeLeagueId: id }),

      setOverride: (week, slot, playerId) =>
        set((s) => ({
          weekOverrides: {
            ...s.weekOverrides,
            [week]: { ...(s.weekOverrides[week] ?? {}), [slot]: playerId },
          },
        })),

      clearOverrides: (week) =>
        set((s) => {
          const { [week]: _, ...rest } = s.weekOverrides
          return { weekOverrides: rest }
        }),

      clearAllOverrides: () => set({ weekOverrides: {} }),
    }),
    { name: 'ffhub-league' },
  ),
)
