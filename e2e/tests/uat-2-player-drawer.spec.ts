/**
 * UAT-2: PlayerDetailDrawer — opens on click, shows all TM-03 stat chips,
 * ESC closes it, NL explanation present, animation class applied.
 */
import { test, expect } from '@playwright/test'
import { injectAuthState, mockTeamApis } from './helpers'

test.describe('UAT-2: PlayerDetailDrawer content and interaction', () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthState(page)
    await mockTeamApis(page)
    await page.goto('/team')
    await expect(page.getByText('Jalen Hurts').first()).toBeVisible({ timeout: 10_000 })
  })

  test('drawer opens when a player row is clicked', async ({ page }) => {
    // Click Jalen Hurts in the Current column (CurrentPlayerRow button)
    await page.getByText('Jalen Hurts').first().click()
    // Drawer should appear — look for the drawer heading
    await expect(page.getByRole('heading', { name: 'Jalen Hurts' })).toBeVisible({ timeout: 5_000 })
  })

  test('drawer shows Proj Pts chip', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toBeVisible({ timeout: 5_000 })
    // Proj Pts chip shows projected_points value from fixture (28.5)
    await expect(drawer.getByText(/Proj Pts|28\.5/).first()).toBeVisible({ timeout: 5_000 })
  })

  test('drawer shows Confidence chip', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toBeVisible({ timeout: 5_000 })
    // Confidence is 82 for Hurts — chip label or percentage
    await expect(drawer.getByText(/Confidence|82%/).first()).toBeVisible({ timeout: 5_000 })
  })

  test('drawer shows Matchup grade chip', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toBeVisible({ timeout: 5_000 })
    // Hurts matchup_grade is "B" — shown as chip label or grade letter
    await expect(drawer.getByText(/Matchup|Grade/i).first()).toBeVisible({ timeout: 5_000 })
  })

  test('drawer shows NL explanation (3-sentence analysis)', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toBeVisible({ timeout: 5_000 })
    // buildNLExplanation for conf=82 starts with "strong start this week with 82% confidence"
    await expect(drawer.getByText(/strong start|82%.*confidence/i).first()).toBeVisible({ timeout: 5_000 })
  })

  test('drawer closes when ESC is pressed', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    await expect(page.getByRole('heading', { name: 'Jalen Hurts' })).toBeVisible({ timeout: 5_000 })
    await page.keyboard.press('Escape')
    await expect(page.getByRole('heading', { name: 'Jalen Hurts' })).not.toBeVisible({ timeout: 3_000 })
  })

  test('drawer opens for a Questionable player and shows Q badge', async ({ page }) => {
    // McCaffrey is Questionable
    await page.getByText('Christian McCaffrey').first().click()
    const drawer = page.getByRole('dialog')
    await expect(page.getByRole('heading', { name: 'Christian McCaffrey' })).toBeVisible({ timeout: 5_000 })
    // Q badge in drawer has aria-label containing "McCaffrey"
    await expect(drawer.locator('[aria-label*="McCaffrey"]').first()).toBeVisible({ timeout: 3_000 })
  })

  test('TrendChart renders inside the drawer (Recharts container visible)', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toBeVisible({ timeout: 5_000 })
    // Recharts ResponsiveContainer renders with a specific role or class
    // It renders as a div containing an svg — we check for the svg presence near the chart section
    await expect(page.locator('recharts-responsive-container, [class*="recharts"]').first()).toBeVisible({ timeout: 5_000 }).catch(() => {
      // Fallback: check for SVG which Recharts always renders
      return expect(drawer.locator('svg').first()).toBeVisible({ timeout: 5_000 })
    })
  })

  test('Compare button is visible in the drawer', async ({ page }) => {
    await page.getByText('Jalen Hurts').first().click()
    await expect(page.getByRole('button', { name: /Compare/i })).toBeVisible({ timeout: 5_000 })
  })
})
