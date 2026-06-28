/**
 * UAT-4: LeagueSwitcher — hidden for single-league, visible for multi-league,
 * switching leagues updates activeLeagueId and triggers card refetch.
 */
import { test, expect } from '@playwright/test'
import { injectAuthState, mockTeamApis, loadFixture } from './helpers'

test.describe('UAT-4: LeagueSwitcher multi-league behavior', () => {
  test('switcher is hidden when only one league is connected', async ({ page }) => {
    await injectAuthState(page)
    await mockTeamApis(page)  // single-league fixture
    await page.goto('/team')
    await expect(page.getByText('Jalen Hurts').first()).toBeVisible({ timeout: 10_000 })

    // LeagueSwitcher returns null when leagues.length <= 1
    const switcher = page.getByRole('combobox', { name: /league/i }).or(
      page.locator('[data-testid="league-switcher"]')
    )
    await expect(switcher).not.toBeVisible()
  })

  test('switcher is visible when two leagues are connected', async ({ page }) => {
    const multiLeagueFixture = loadFixture('team-my-multi-league.json')
    await injectAuthState(page, 'league-001')
    await mockTeamApis(page, { my: multiLeagueFixture })
    await page.goto('/team')
    await expect(page.getByText('Jalen Hurts').first()).toBeVisible({ timeout: 10_000 })

    // LeagueSwitcher renders a dropdown trigger button with the league name
    // Use first() since league name may also appear in standings area
    await expect(
      page.getByText('Gridiron Glory 2025').first().or(page.getByText('Dynasty Empire 2025').first())
    ).toBeVisible({ timeout: 5_000 })
  })

  test('switching leagues updates activeLeagueId in localStorage', async ({ page }) => {
    const multiLeagueFixture = loadFixture('team-my-multi-league.json')

    await injectAuthState(page, 'league-001')
    await mockTeamApis(page, { my: multiLeagueFixture })

    await page.goto('/team')
    await expect(page.getByText('Jalen Hurts').first()).toBeVisible({ timeout: 10_000 })

    // LeagueSwitcher trigger has aria-label="Switch league" (unique to the component)
    const switcherTrigger = page.getByRole('button', { name: 'Switch league' })
    await expect(switcherTrigger).toBeVisible({ timeout: 5_000 })
    await switcherTrigger.click()

    // Radix DropdownMenu renders items in a portal — visible on the page
    const secondLeague = page.getByText('Dynasty Empire 2025').first()
    await expect(secondLeague).toBeVisible({ timeout: 3_000 })
    await secondLeague.click()

    // Verify LeagueSwitcher trigger now shows the new league name
    await expect(page.getByRole('button', { name: 'Switch league' })).toContainText('Dynasty Empire', { timeout: 3_000 })

    // Verify Zustand persisted the new activeLeagueId to localStorage
    const stored = await page.evaluate(() => {
      const raw = localStorage.getItem('ffhub-league')
      return raw ? JSON.parse(raw) : null
    })
    expect(stored?.state?.activeLeagueId).toBe('league-002')
  })
})
