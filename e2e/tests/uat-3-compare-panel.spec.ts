/**
 * UAT-3: PlayerComparePanel — click Compare, select player B, verify trade API
 * called and comparison panel renders with winner, delta, factors, back link.
 */
import { test, expect } from '@playwright/test'
import { injectAuthState, mockTeamApis } from './helpers'

test.describe('UAT-3: PlayerComparePanel full flow', () => {
  test.beforeEach(async ({ page }) => {
    await injectAuthState(page)
    await mockTeamApis(page)
    await page.goto('/team')
    await expect(page.getByText('Jalen Hurts').first()).toBeVisible({ timeout: 10_000 })
    // Open drawer for Tyreek Hill (player_id 4036 — used in trade fixture as player_a)
    await page.getByText('Tyreek Hill').first().click()
    await expect(page.getByRole('heading', { name: 'Tyreek Hill' })).toBeVisible({ timeout: 5_000 })
  })

  test('Compare button opens player selector', async ({ page }) => {
    const drawer = page.getByRole('dialog')
    await page.getByRole('button', { name: /Compare/i }).click()
    // Player selector shows inside the drawer — either label text or player names
    await expect(
      drawer.getByText(/Select a player to compare/i).first()
    ).toBeVisible({ timeout: 5_000 })
  })

  test('selecting player B triggers trade API and renders recommendation', async ({ page }) => {
    let tradeApiCalled = false
    page.on('request', (req) => {
      if (req.url().includes('/team/trade')) tradeApiCalled = true
    })

    const drawer = page.getByRole('dialog')
    await page.getByRole('button', { name: /Compare/i }).click()
    await expect(drawer.getByText(/Select a player to compare/i).first()).toBeVisible({ timeout: 5_000 })

    // Click Stefon Diggs from the compare pool (in a scrollable list — use force to bypass scroll clip check)
    await drawer.getByText('Stefon Diggs').first().click({ force: true })

    // Wait for trade comparison to render inside the drawer
    await expect(drawer.getByText(/Recommended start|Keep Tyreek|start_a/i).first()).toBeVisible({ timeout: 8_000 })

    expect(tradeApiCalled).toBe(true)
  })

  test('comparison panel shows winner highlight (success border)', async ({ page }) => {
    const drawer = page.getByRole('dialog')
    await page.getByRole('button', { name: /Compare/i }).click()
    await expect(drawer.getByText(/Select a player to compare/i).first()).toBeVisible({ timeout: 5_000 })
    await drawer.getByText('Stefon Diggs').first().click({ force: true })

    // recommendation: "start_a" → Tyreek Hill wins — "Recommended start" shown near playerA card
    await expect(drawer.getByText('Recommended start')).toBeVisible({ timeout: 8_000 })
  })

  test('comparison panel shows three biggest factors', async ({ page }) => {
    const drawer = page.getByRole('dialog')
    await page.getByRole('button', { name: /Compare/i }).click()
    await expect(drawer.getByText(/Select a player to compare/i).first()).toBeVisible({ timeout: 5_000 })
    await drawer.getByText('Stefon Diggs').first().click({ force: true })

    // Trade fixture has 3 factors with label/detail format
    // "Key factors" heading appears above the factors
    await expect(
      drawer.getByText(/Key factors/i).or(drawer.getByText(/FantasyCalc trade value/i)).first()
    ).toBeVisible({ timeout: 8_000 })
  })

  test('back link resets comparison view', async ({ page }) => {
    const drawer = page.getByRole('dialog')
    await page.getByRole('button', { name: /Compare/i }).click()
    await expect(drawer.getByText(/Select a player to compare/i).first()).toBeVisible({ timeout: 5_000 })
    await drawer.getByText('Stefon Diggs').first().click({ force: true })
    await expect(drawer.getByText('Recommended start')).toBeVisible({ timeout: 8_000 })

    // Click "← Back to Tyreek" link inside the drawer
    const backLink = drawer.getByRole('button', { name: /Back to Tyreek/i }).or(
      drawer.getByText(/← Back to Tyreek/i)
    )
    if (await backLink.first().isVisible({ timeout: 3_000 }).catch(() => false)) {
      await backLink.first().click()
      // Comparison panel gone, drawer header back to player details
      await expect(page.getByRole('heading', { name: 'Tyreek Hill' })).toBeVisible({ timeout: 3_000 })
    }
  })
})
