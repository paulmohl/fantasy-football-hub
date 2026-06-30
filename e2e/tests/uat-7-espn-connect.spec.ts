/**
 * UAT-7: ESPN Connect Flows (03-12)
 * Tests the ESPN platform selection, sub-option steps, private form, and public form
 * against a running dev stack at localhost:5173.
 */
import { test, expect } from '@playwright/test'

test.describe('ESPN Connect Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Inject auth with hasLeagues=false so the onboarding flow opens
    await page.addInitScript(() => {
      localStorage.setItem('ffhub-auth', JSON.stringify({
        state: {
          token: 'fake-jwt-token-for-testing',
          userId: 'user-test-001',
          hasLeagues: false,
          unhealthyPlatforms: [],
        },
        version: 0,
      }))
    })
    // Mock /users/me so RequireAuth doesn't clear hasLeagues
    await page.route('**/api/v1/users/me**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-test-001',
          email: 'test@example.com',
          is_verified: true,
          has_leagues: false,
          credential_health: [],
        }),
      }),
    )
    await page.goto('/connect')
  })

  test('ESPN option appears on platform selection step', async ({ page }) => {
    await expect(page.getByText('ESPN')).toBeVisible()
  })

  test('clicking ESPN shows Private and Public sub-options', async ({ page }) => {
    await page.getByRole('button', { name: /ESPN/ }).click()
    await expect(page.getByRole('button', { name: /Private league/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /Public league/ })).toBeVisible()
  })

  test('ESPN private form has SWID, espn_s2, and league ID inputs', async ({ page }) => {
    await page.getByRole('button', { name: /ESPN/ }).click()
    await page.getByRole('button', { name: /Private league/ }).click()
    await expect(page.getByLabel('ESPN SWID cookie')).toBeVisible()
    await expect(page.getByLabel('ESPN espn_s2 cookie')).toBeVisible()
    await expect(page.getByLabel('ESPN League ID')).toBeVisible()
  })

  test('invalid ESPN cookies show inline error not generic alert', async ({ page }) => {
    await page.route('**/api/v1/espn/connect**', (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'ESPN cookies are expired or invalid.' }),
      }),
    )
    await page.getByRole('button', { name: /ESPN/ }).click()
    await page.getByRole('button', { name: /Private league/ }).click()
    await page.getByLabel('ESPN SWID cookie').fill('{12345}')
    await page.getByLabel('ESPN espn_s2 cookie').fill('fake_token')
    await page.getByLabel('ESPN League ID').fill('123')
    await page.getByRole('button', { name: /Connect ESPN League/i }).click()
    await expect(page.getByText('ESPN cookies are expired or invalid.')).toBeVisible()
  })

  test('ESPN public form has only league ID input (no SWID)', async ({ page }) => {
    await page.getByRole('button', { name: /ESPN/ }).click()
    await page.getByRole('button', { name: /Public league/ }).click()
    await expect(page.getByLabel('ESPN League ID')).toBeVisible()
    await expect(page.getByLabel('ESPN SWID cookie')).not.toBeVisible()
  })
})
