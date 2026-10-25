// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('@/lib/api', () => ({ api: { post: vi.fn(), get: vi.fn() } }))

const isInstalled = vi.fn()
vi.mock('@/lib/espnExtension', async () => {
  const actual = await vi.importActual<typeof import('@/lib/espnExtension')>('@/lib/espnExtension')
  return { ...actual, isInstalled: () => isInstalled(), requestCookies: vi.fn() }
})

const isNative = vi.fn()
vi.mock('@/plugins/espn-cookie', () => ({
  EspnCookieNative: { extractCookies: vi.fn() },
  isNative: () => isNative(),
}))

import ConnectPage from './ConnectPage'

function renderAt(path: string) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <ConnectPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  isInstalled.mockResolvedValue(true)
  isNative.mockReturnValue(false)
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
})
afterEach(cleanup)

describe('ConnectPage ESPN reconnect', () => {
  it('?reconnect=espn skips platform selection and offers the extension connect button', async () => {
    renderAt('/connect?reconnect=espn')
    expect(await screen.findByText(/connect espn/i)).toBeTruthy()
    expect(screen.queryByText(/which platform is your league on/i)).toBeNull()
  })

  it('native shell still renders the native sign-in button', async () => {
    isNative.mockReturnValue(true)
    renderAt('/connect?reconnect=espn')
    expect(await screen.findByRole('button', { name: /sign in to espn/i })).toBeTruthy()
  })

  it('?reconnect=yahoo still starts at platform selection', async () => {
    renderAt('/connect?reconnect=yahoo')
    expect(await screen.findByText(/which platform is your league on/i)).toBeTruthy()
  })
})
