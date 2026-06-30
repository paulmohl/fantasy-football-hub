import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  userId: string | null
  hasLeagues: boolean
  unhealthyPlatforms: string[]
  setAuth: (token: string, userId: string) => void
  setHasLeagues: (value: boolean) => void
  setUnhealthyPlatforms: (platforms: string[]) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      hasLeagues: false,
      unhealthyPlatforms: [],
      setAuth: (token, userId) => set({ token, userId }),
      setHasLeagues: (value) => set({ hasLeagues: value }),
      setUnhealthyPlatforms: (platforms) => set({ unhealthyPlatforms: platforms }),
      clearAuth: () => set({ token: null, userId: null, hasLeagues: false, unhealthyPlatforms: [] }),
    }),
    { name: 'ffhub-auth' },
  ),
)
