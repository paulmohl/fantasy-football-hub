/**
 * UAT-9: Rate Limit Toast (03-12)
 * Verifies that a 'rate-limited' custom event triggers a visible toast notification.
 */
import { test, expect } from '@playwright/test'

test.describe('Rate Limit Toast', () => {
  test('rate-limited custom event shows toast notification', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('ffhub-auth', JSON.stringify({
        state: {
          token: 'fake-jwt-token-for-testing',
          userId: 'user-test-001',
          hasLeagues: true,
          unhealthyPlatforms: [],
        },
        version: 0,
      }))
      localStorage.setItem('ffhub-league', JSON.stringify({
        state: { activeLeagueId: 'league-001', weekOverrides: {} },
        version: 0,
      }))
    })

    // Mock all team APIs so page loads without real backend
    await page.route('**/api/v1/users/me**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-test-001',
          email: 'test@example.com',
          is_verified: true,
          has_leagues: true,
          credential_health: [],
        }),
      }),
    )
    await page.route('**/api/v1/leagues/mine**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
    )
    await page.route('**/api/v1/team/**', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }),
    )
    await page.route('**/api/v1/auth/refresh**', (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'expired' }) }),
    )

    await page.goto('/connect')
    // Wait for network idle so React effects (event listener registration) have run
    await page.waitForLoadState('networkidle')

    // Dispatch the custom event from the page context
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('rate-limited', { detail: { platform: 'Yahoo' } }))
    })

    // Toast should appear containing rate limit text (first element, not the ARIA live region)
    await expect(page.getByText(/rate-limited|cached results/i).first()).toBeVisible({ timeout: 5000 })
  })
})
