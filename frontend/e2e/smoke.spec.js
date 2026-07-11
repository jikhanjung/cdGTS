// @ts-check
import { test, expect } from '@playwright/test'

// Tier-2 happy-path browser smoke. Verifies the seam Tier 1 (backend) cannot: the SPA actually boots,
// React Flow mounts a graph in a real browser, and — when creds are supplied — the CSRF login round-trip
// works in real JS. Read-mostly: no fork/edit/propose here (Tier 1 covers that flow deterministically).

const USER = process.env.E2E_USER
const PASS = process.env.E2E_PASS

test('app boots — brand and nav render', async ({ page }) => {
  const errors = []
  page.on('pageerror', (e) => errors.push(String(e)))
  await page.goto('/')

  await expect(page.locator('.brand')).toContainText('cdGTS')
  for (const label of ['Editor', 'Vault', 'Proposals', 'Bibliography']) {
    await expect(page.getByRole('button', { name: label, exact: true })).toBeVisible()
  }
  // Logged-out control is present (invite-only: a Login button, no signup).
  await expect(page.getByRole('button', { name: 'Login', exact: true })).toBeVisible()
  expect(errors, `uncaught page errors: ${errors.join('\n')}`).toEqual([])
})

test('editor mounts a graph in the browser (read-only, anonymous)', async ({ page }) => {
  await page.goto('/')
  // The editor auto-loads the first visible (system) graph; React Flow must mount and render nodes.
  await expect(page.locator('.react-flow')).toBeVisible()
  await expect(page.locator('.react-flow__node').first()).toBeVisible({ timeout: 15_000 })
})

// The browser-only seam: session login sends the csrftoken cookie back as X-CSRFToken from real JS.
// Runs only when creds are provided (never mutates data — just logs in and out).
test('login CSRF round-trip', async ({ page }) => {
  test.skip(!USER || !PASS, 'set E2E_USER and E2E_PASS to run the authenticated smoke')
  await page.goto('/')

  await page.getByRole('button', { name: 'Login', exact: true }).click()
  const dialog = page.locator('.login-dialog')
  await expect(dialog).toBeVisible()
  await dialog.getByLabel('Username').fill(USER)
  await dialog.getByLabel('Password').fill(PASS)
  await dialog.getByRole('button', { name: 'Sign in' }).click()

  // Authenticated state: the nav shows the username + a Logout button.
  await expect(page.locator('.login-user')).toContainText(USER, { timeout: 10_000 })
  const logout = page.getByRole('button', { name: 'Logout', exact: true })
  await expect(logout).toBeVisible()

  // Clean up: log back out so the run leaves no session behind.
  await logout.click()
  await expect(page.getByRole('button', { name: 'Login', exact: true })).toBeVisible()
})
