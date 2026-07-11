// @ts-check
import { defineConfig, devices } from '@playwright/test'

// Tier-2 browser smoke (R02 검토 노트 · devlog 134 §Tier 2). NON-BLOCKING and opt-in:
// not wired into `npm run build` or deploy/build.sh — run manually before a release against a
// freshly-deployed instance. Tier 1 (backend `test_ci_flow.py`) already locks the API contract;
// this only verifies the browser seam pytest can't (SPA boot, React Flow mount, CSRF login in real JS).
//
// Target an already-running server via E2E_BASE_URL (default = the test server on :8011).
// The login smoke runs only when E2E_USER/E2E_PASS are set (else it is skipped) — it never mutates data.
const BASE_URL = process.env.E2E_BASE_URL || 'http://127.0.0.1:8011'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
