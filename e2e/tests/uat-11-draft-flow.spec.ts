import { test, expect } from '@playwright/test'

/**
 * UAT-11: Full Draft Flow — DR-07, DR-09
 * Stub: implement in plan 04-13 (Wave 7) after all frontend complete.
 * Tests the full happy path: schedule → lobby → picks → auto-draft → pause/resume → recap.
 */
test.describe('Full Draft Flow (DR-07, DR-09)', () => {
  test.skip(true, 'stub: implement in plan 04-13 after full draft frontend complete')

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('ffhub-auth', JSON.stringify({
        state: { token: 'fake-jwt-token-for-testing', userId: 'user-test-001', hasLeagues: true, unhealthyPlatforms: [] },
        version: 0,
      }))
    })
  })

  test('commissioner schedules draft and ICS invite is sent', async ({ page }) => {
    // TODO (04-13): POST /drafts, assert 201, assert email sent
    expect(true).toBe(true)
  })

  test('pick propagates to all participants within 500ms', async ({ page }) => {
    // TODO (04-13): measure Date.now() delta between pick emit and pick_confirmed receive
    expect(true).toBe(true)
  })

  test('commissioner can pause and resume the draft', async ({ page }) => {
    // TODO (04-13): emit pause, assert overlay shown, emit resume, assert countdown
    expect(true).toBe(true)
  })

  test('post-draft recap shows team grades', async ({ page }) => {
    // TODO (04-13): navigate to recap, assert grade cards visible
    expect(true).toBe(true)
  })
})
