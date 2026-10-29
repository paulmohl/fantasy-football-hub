// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TeamPage from './TeamPage'
import { useLeagueStore } from '@/store/league'

const get = vi.fn()
vi.mock('@/lib/api', () => ({ api: { get: (...args: unknown[]) => get(...args) } }))

vi.mock('@/components/LineupCard', () => ({ LineupCard: () => null }))
vi.mock('@/components/WaiverCard', () => ({ WaiverCard: () => null }))
vi.mock('@/components/StandingsCard', () => ({ StandingsCard: () => null }))
vi.mock('@/components/PlayerDetailDrawer', () => ({ PlayerDetailDrawer: () => null }))
vi.mock('@/components/AddPlayerDialog', () => ({ AddPlayerDialog: () => null }))

const league = (id: string) => ({ league_id: id, name: `League ${id}`, season: '2026', platform: 'espn' })

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <TeamPage />
    </QueryClientProvider>,
  )
}

afterEach(cleanup)

beforeEach(() => {
  get.mockReset()
  useLeagueStore.setState({ activeLeagueId: null })
})

describe('TeamPage league selection', () => {
  it('selects the only league automatically instead of asking for a dropdown that is hidden', async () => {
    get.mockResolvedValue({ data: { leagues: [league('a')] } })
    renderPage()
    await waitFor(() => expect(useLeagueStore.getState().activeLeagueId).toBe('a'))
    expect(screen.queryByText('Select a league')).toBeNull()
  })

  it('replaces a stored league that no longer exists with the first one', async () => {
    useLeagueStore.setState({ activeLeagueId: 'gone' })
    get.mockResolvedValue({ data: { leagues: [league('a'), league('b')] } })
    renderPage()
    await waitFor(() => expect(useLeagueStore.getState().activeLeagueId).toBe('a'))
  })

  it('keeps a stored league that still exists', async () => {
    useLeagueStore.setState({ activeLeagueId: 'b' })
    get.mockResolvedValue({ data: { leagues: [league('a'), league('b')] } })
    renderPage()
    await waitFor(() => expect(get).toHaveBeenCalled())
    expect(useLeagueStore.getState().activeLeagueId).toBe('b')
  })
})

describe('TeamPage header and lineup request', () => {
  const mine = { ...league('a'), team_name: 'Gridiron Ghosts' }

  it('shows the active league team name instead of the generic title', async () => {
    get.mockResolvedValue({ data: { leagues: [mine] } })
    renderPage()
    expect(await screen.findByText('Gridiron Ghosts')).toBeTruthy()
  })

  it('falls back to the generic title when the user has no team in the league', async () => {
    get.mockResolvedValue({ data: { leagues: [{ ...mine, team_name: null }] } })
    renderPage()
    await waitFor(() => expect(useLeagueStore.getState().activeLeagueId).toBe('a'))
    expect(screen.getByText('Team Manager')).toBeTruthy()
  })

  it('sends the active league id with the lineup request', async () => {
    get.mockResolvedValue({ data: { leagues: [mine] } })
    renderPage()
    await waitFor(() =>
      expect(get).toHaveBeenCalledWith('/team/lineup', { params: { league_id: 'a' } }),
    )
  })
})
