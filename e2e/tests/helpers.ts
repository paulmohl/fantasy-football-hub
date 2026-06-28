import { Page } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

const FIXTURES_DIR = path.join(__dirname, '..', 'fixtures')

export function loadFixture(name: string) {
  return JSON.parse(fs.readFileSync(path.join(FIXTURES_DIR, name), 'utf8'))
}

/**
 * Inject auth + league state into localStorage so the app bypasses login
 * and goes straight to TeamPage for league-001.
 */
export async function injectAuthState(page: Page, leagueId = 'league-001') {
  await page.addInitScript(({ leagueId }) => {
    // Zustand persist format: { state: {...}, version: 0 }
    localStorage.setItem('ffhub-auth', JSON.stringify({
      state: {
        token: 'fake-jwt-token-for-testing',
        userId: 'user-test-001',
        hasLeagues: true,
      },
      version: 0,
    }))
    localStorage.setItem('ffhub-league', JSON.stringify({
      state: {
        activeLeagueId: leagueId,
        weekOverrides: {},
      },
      version: 0,
    }))
  }, { leagueId })
}

/**
 * Set up all standard API mocks for the TeamPage.
 * Pass overrides to replace specific fixtures.
 */
export async function mockTeamApis(
  page: Page,
  overrides: { my?: object; lineup?: object; waiver?: object; standings?: object } = {},
) {
  const my = overrides.my ?? loadFixture('team-my.json')
  const lineup = overrides.lineup ?? loadFixture('lineup.json')
  const waiver = overrides.waiver ?? loadFixture('waiver.json')
  const standings = overrides.standings ?? loadFixture('standings.json')
  const trade = loadFixture('trade.json')
  const playerStats = loadFixture('player-stats.json')
  const waiverTrend = loadFixture('waiver-trend.json')

  await page.route('**/api/v1/team/my**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(my) }),
  )
  await page.route('**/api/v1/team/lineup**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(lineup) }),
  )
  await page.route('**/api/v1/team/waiver**', (route) => {
    const url = new URL(route.request().url())
    const mode = url.searchParams.get('mode')
    const data = mode === 'trend' ? waiverTrend : waiver
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) })
  })
  await page.route('**/api/v1/team/standings**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(standings) }),
  )
  await page.route('**/api/v1/team/trade**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(trade) }),
  )
  await page.route('**/api/v1/team/stats/**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(playerStats) }),
  )
  // Catch any auth refresh attempts — return 401 so the interceptor bails cleanly
  await page.route('**/api/v1/auth/refresh**', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'expired' }) }),
  )
}
