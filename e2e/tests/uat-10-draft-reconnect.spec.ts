import { test, expect } from '@playwright/test'

/**
 * UAT-10: Draft Reconnect — DR-15
 * Stub: implement in plan 04-13 (Wave 7) after all frontend complete.
 * Tests that a participant who disconnects mid-draft and reconnects
 * sees the board rebuilt correctly from the Redis stream replay.
 */
test.describe('Draft Reconnect (DR-15)', () => {
  test.skip(true, 'stub: implement in plan 04-13 after full draft frontend complete')

  test('reconnecting client replays missed events and board shows correct picks', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('ffhub-auth', JSON.stringify({
        state: { token: 'fake-jwt-token-for-testing', userId: 'user-test-001', hasLeagues: true, unhealthyPlatforms: [] },
        version: 0,
      }))
      localStorage.setItem('ffhub-draft', JSON.stringify({
        state: { draftId: 'draft-001', lastEventId: null, muteAudio: false },
        version: 0,
      }))
    })

    await page.goto('/draft?id=draft-001')
    // TODO (04-13): simulate disconnect, reconnect, verify board cells
    expect(true).toBe(true) // placeholder
  })
})
