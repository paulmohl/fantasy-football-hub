// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'

const post = vi.fn()
vi.mock('@/lib/api', () => ({ api: { post: (...a: unknown[]) => post(...a) } }))

const isInstalled = vi.fn()
const requestCookies = vi.fn()
vi.mock('@/lib/espnExtension', async () => {
  const actual = await vi.importActual<typeof import('@/lib/espnExtension')>('@/lib/espnExtension')
  return { ...actual, isInstalled: () => isInstalled(), requestCookies: () => requestCookies() }
})

import { EspnExtensionError } from '@/lib/espnExtension'
import EspnExtensionConnect from './EspnExtensionConnect'

const COOKIES = { swid: '{ABC}', espn_s2: 'AE%2Bxyz' }
const onConnected = vi.fn()
const onAdvanced = vi.fn()

function setup() {
  return render(<EspnExtensionConnect onConnected={onConnected} onAdvanced={onAdvanced} />)
}

beforeEach(() => {
  vi.clearAllMocks()
  isInstalled.mockResolvedValue(true)
})
afterEach(cleanup)

describe('EspnExtensionConnect', () => {
  it('shows install button when the extension is missing and re-pings on "Check again"', async () => {
    isInstalled.mockResolvedValueOnce(false)
    setup()
    expect(await screen.findByText(/install the extension/i)).toBeTruthy()
    isInstalled.mockResolvedValueOnce(true)
    fireEvent.click(screen.getByText(/check again/i))
    expect(await screen.findByText(/connect espn/i)).toBeTruthy()
    expect(isInstalled).toHaveBeenCalledTimes(2)
  })

  it('lists leagues, then connects the chosen one with the cookies', async () => {
    requestCookies.mockResolvedValue(COOKIES)
    post.mockImplementation(async (url: string) => {
      if (url === '/espn/leagues') {
        return { data: { leagues: [{ league_id: '1409037', name: 'Sunday Degenerates', season: 2026 }] } }
      }
      return { data: { id: 'x' } }
    })
    setup()
    fireEvent.click(await screen.findByText(/connect espn/i))
    fireEvent.click(await screen.findByText('Sunday Degenerates'))
    await waitFor(() => expect(onConnected).toHaveBeenCalled())
    expect(post).toHaveBeenCalledWith('/espn/leagues', { swid: '{ABC}', espn_s2: 'AE%2Bxyz' })
    expect(post).toHaveBeenCalledWith('/espn/connect', {
      swid: '{ABC}',
      espn_s2: 'AE%2Bxyz',
      league_id: '1409037',
    })
  })

  it('falls back to manual League ID entry when no leagues are found', async () => {
    requestCookies.mockResolvedValue(COOKIES)
    post.mockResolvedValueOnce({ data: { leagues: [] } })
    setup()
    fireEvent.click(await screen.findByText(/connect espn/i))
    const input = await screen.findByLabelText(/league id/i)
    fireEvent.change(input, { target: { value: '1409037' } })
    post.mockResolvedValueOnce({ data: { id: 'x' } })
    fireEvent.click(screen.getByText(/^connect league/i))
    await waitFor(() => expect(onConnected).toHaveBeenCalled())
    expect(post).toHaveBeenLastCalledWith('/espn/connect', {
      swid: '{ABC}',
      espn_s2: 'AE%2Bxyz',
      league_id: '1409037',
    })
  })

  it('falls back to manual entry when the leagues lookup fails for a non-auth reason', async () => {
    requestCookies.mockResolvedValue(COOKIES)
    post.mockRejectedValueOnce({ response: { status: 502, data: { detail: 'bad gateway' } } })
    setup()
    fireEvent.click(await screen.findByText(/connect espn/i))
    expect(await screen.findByLabelText(/league id/i)).toBeTruthy()
  })

  it.each([
    ['denied', /declined|denied|not allowed/i],
    ['not_signed_in', /sign in to espn/i],
    ['busy', /already waiting|approval/i],
  ] as const)('shows a message for %s and re-enables the button', async (code, message) => {
    requestCookies.mockRejectedValue(new EspnExtensionError(code))
    setup()
    fireEvent.click(await screen.findByText(/connect espn/i))
    expect(await screen.findByText(message)).toBeTruthy()
    expect((screen.getByText(/connect espn/i) as HTMLButtonElement).disabled).toBe(false)
  })

  it('shows the backend error when ESPN rejects the cookies', async () => {
    requestCookies.mockResolvedValue(COOKIES)
    post.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'ESPN cookies are expired or invalid. Re-export.' } },
    })
    setup()
    fireEvent.click(await screen.findByText(/connect espn/i))
    expect(await screen.findByText(/ESPN cookies are expired or invalid/)).toBeTruthy()
  })

  it('exposes the advanced fallback', async () => {
    setup()
    fireEvent.click(await screen.findByText(/advanced/i))
    expect(onAdvanced).toHaveBeenCalled()
  })
})
