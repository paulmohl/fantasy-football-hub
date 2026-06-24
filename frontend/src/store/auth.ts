import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  userId: string | null
  hasLeagues: boolean
  setAuth: (token: string, userId: string) => void
  setHasLeagues: (value: boolean) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      hasLeagues: false,
      setAuth: (token, userId) => set({ token, userId }),
      setHasLeagues: (value) => set({ hasLeagues: value }),
      clearAuth: () => set({ token: null, userId: null, hasLeagues: false }),
    }),
    { name: 'ffhub-auth' },
  ),
)
