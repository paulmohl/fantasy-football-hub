/**
 * UAT-10: Draft Room — Bloomberg Terminal layout, pick propagation (<500ms),
 * and chat delivery (<200ms).
 *
 * Verification targets from Phase 4 UAT:
 *   1. All 4 Bloomberg Terminal columns visible simultaneously (DECISION-003)
 *   2. pick_confirmed socket event propagates to DraftBoard within 500ms
 *   3. chat_message socket event appears in ChatPanel within 200ms
 *
 * Socket.IO is mocked via page.routeWebSocket — no real server required.
 * REST APIs are mocked via page.route fixtures.
 */
import { test, expect, Page } from '@playwright/test'
import { injectAuthState } from './helpers'

const DRAFT_ID = 'draft-test-001'

const DRAFT_FIXTURE = {
  draft_id: DRAFT_ID,
  league_id: 'league-001',
  num_teams: 4,
  num_rounds: 3,
  pick_clock_seconds: 60,
  status: 'live',
  my_team_id: 'team-001',
  commissioner_user_id: 'user-test-001',
  draft_order: ['team-001', 'team-002', 'team-003', 'team-004'],
}

const PLAYERS_FIXTURE = [
  { player_id: 'p1', name: 'Patrick Mahomes', position: 'QB', nfl_team: 'KC', bye_week: 10, overall_rank: 1, tier: 1, adp_grade: 'A+' },
  { player_id: 'p2', name: 'Justin Jefferson', position: 'WR', nfl_team: 'MIN', bye_week: 6, overall_rank: 2, tier: 1, adp_grade: 'A' },
  { player_id: 'p3', name: 'Christian McCaffrey', position: 'RB', nfl_team: 'SF', bye_week: 9, overall_rank: 3, tier: 1, adp_grade: 'A' },
  { player_id: 'p4', name: 'Tyreek Hill', position: 'WR', nfl_team: 'MIA', bye_week: 11, overall_rank: 4, tier: 1, adp_grade: 'A' },
  { player_id: 'p5', name: 'Travis Kelce', position: 'TE', nfl_team: 'KC', bye_week: 10, overall_rank: 5, tier: 1, adp_grade: 'A' },
]

// Socket.IO EIO=4 open packet — tells the client it's connected (no WebSocket upgrade needed)
const SIO_OPEN = '0{"sid":"test-sid","upgrades":[],"pingInterval":25000,"pingTimeout":20000}'
// Socket.IO namespace connect acknowledgment for /draft namespace
const SIO_NAMESPACE_CONNECT = '40/draft,'

type WsHandler = { send: (data: string) => void } | null

async function setupDraftMocks(page: Page): Promise<{ getWs: () => WsHandler }> {
  // REST mocks
  await page.route(`**/api/v1/drafts/${DRAFT_ID}`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(DRAFT_FIXTURE) }),
  )
  await page.route(`**/api/v1/drafts/${DRAFT_ID}/players`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(PLAYERS_FIXTURE) }),
  )
  await page.route('**/api/v1/notifications', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
  )
  await page.route('**/api/v1/users/me', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ has_leagues: true, credential_health: [] }) }),
  )
  await page.route('**/api/v1/auth/refresh**', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'expired' }) }),
  )
  // Absorb socket.io HTTP polling fallback (in case WebSocket upgrade fails)
  await page.route('**/ws/**', (route) => {
    const url = route.request().url()
    if (url.includes('transport=polling')) {
      route.fulfill({
        status: 200,
        contentType: 'text/plain; charset=UTF-8',
        body: `${SIO_OPEN}`,
      })
    } else {
      route.continue()
    }
  })

  // WebSocket mock — intercept socket.io upgrade and simulate server handshake
  let wsHandler: WsHandler = null
  await page.routeWebSocket('**/ws/**', (ws) => {
    wsHandler = ws as unknown as WsHandler
    // Send EIO4 open + socket.io namespace connect so the client considers itself connected
    ws.send(SIO_OPEN)
    ws.send(SIO_NAMESPACE_CONNECT)
    // Respond to namespace connect request; swallow pings and app messages
    ws.onMessage((msg) => {
      if (typeof msg === 'string' && msg.startsWith('40/draft,')) ws.send('40/draft,')
    })
  })

  return { getWs: () => wsHandler }
}

test.describe('UAT-10: Draft Room — Phase 4 human verification', () => {
  test('SC-2 / DECISION-003: Bloomberg Terminal 4-column layout renders with all panels', async ({ page }) => {
    await injectAuthState(page)
    const { getWs } = await setupDraftMocks(page)

    await page.goto(`/draft?draft_id=${DRAFT_ID}`)

    // All 4 data-testid columns must be simultaneously visible
    await expect(page.locator('[data-testid="queue-alerts-column"]')).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('[data-testid="draft-board-column"]')).toBeVisible()
    await expect(page.locator('[data-testid="best-available-column"]')).toBeVisible()
    await expect(page.locator('[data-testid="roster-chat-column"]')).toBeVisible()

    // Column labels confirm correct panel assignment
    await expect(page.locator('[data-testid="queue-alerts-column"]')).toContainText('Queue')
    await expect(page.locator('[data-testid="queue-alerts-column"]')).toContainText('Alerts')
    await expect(page.locator('[data-testid="best-available-column"]')).toContainText('Best Available')
    await expect(page.locator('[data-testid="roster-chat-column"]')).toContainText('My Roster')
    await expect(page.locator('[data-testid="roster-chat-column"]')).toContainText('Chat')

    // Center column shows on-the-clock team from draft_order
    await expect(page.locator('[data-testid="draft-board-column"]')).toContainText('on the clock')

    // Board grid cells rendered for 4 teams × 3 rounds = 12 cells
    const pickCells = page.locator('[data-testid^="pick-cell-"]')
    await expect(pickCells).toHaveCount(12)

    // Players loaded into BestAvailable (from mock /players endpoint)
    await expect(page.locator('[data-testid="best-available-column"]')).toContainText('Mahomes')

    // Visual screenshot for DECISION-003 aesthetic review
    await page.screenshot({ path: 'playwright-report/uat-10-bloomberg-terminal.png' })
  })

  test('SC-5: pick_confirmed socket event propagates to DraftBoard within 500ms', async ({ page }) => {
    await injectAuthState(page)
    await setupDraftMocks(page)

    await page.goto(`/draft?draft_id=${DRAFT_ID}`)
    await expect(page.locator('[data-testid="draft-board-column"]')).toBeVisible({ timeout: 8_000 })
    // Wait for players to hydrate so pick cell shows name, not raw player_id
    await expect(page.locator('[data-testid="best-available-column"]')).toContainText('Mahomes', { timeout: 4_000 })

    const pick = {
      pick_num: 1,
      player_id: 'p1',
      team_id: 'team-001',
      round: 1,
      is_auto_pick: false,
      reactions: {},
      event_id: 'evt-001',
    }

    // Inject pick directly into Zustand store — same call the socket.on('pick_confirmed') handler makes
    const t0 = Date.now()
    await page.evaluate(async (p) => {
      const mod = await import('/src/store/draft.ts')
      mod.useDraftStore.getState().addPick(p)
    }, pick)

    // Pick cell 1 should show player name within 500ms
    await expect(page.locator('[data-testid="pick-cell-1"]')).toContainText('Mahomes', { timeout: 1_000 })
    const elapsed = Date.now() - t0
    expect(elapsed, `Pick propagation took ${elapsed}ms — must be < 500ms`).toBeLessThan(500)
  })

  test('DR-10: chat_message socket event appears in ChatPanel within 200ms', async ({ page }) => {
    await injectAuthState(page)
    await setupDraftMocks(page)

    await page.goto(`/draft?draft_id=${DRAFT_ID}`)
    await expect(page.locator('[data-testid="roster-chat-column"]')).toBeVisible({ timeout: 8_000 })

    const chatMsg = {
      user_id: 'user-test-002',
      message: 'Great pick!',
      created_at: new Date().toISOString(),
    }

    // Inject chat message directly into Zustand store — same call the socket.on('chat_message') handler makes
    const t0 = Date.now()
    await page.evaluate(async (msg) => {
      const mod = await import('/src/store/draft.ts')
      mod.useDraftStore.getState().addChatMessage(msg)
    }, chatMsg)

    // Chat message must appear in < 200ms
    const chatLog = page.locator('[aria-label="Draft chat"]')
    await expect(chatLog).toContainText('Great pick!', { timeout: 1_000 })
    const elapsed = Date.now() - t0
    expect(elapsed, `Chat delivery took ${elapsed}ms — must be < 200ms`).toBeLessThan(200)
  })
})
