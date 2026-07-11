# Tier-2 browser smoke (Playwright)

A single happy-path browser smoke. **Opt-in and non-blocking** — it is *not* run by `npm run build` or
`deploy/build.sh`. Run it by hand before promoting a release, against a freshly-deployed instance.

## Why this exists (and what it does NOT do)

- **Tier 1** (`test_ci_flow.py`, backend pytest) already drives the whole flow — login → fork → edit →
  bake → diff → propose → ratify — through the real session + CSRF path. That locks the API contract.
- **Tier 2 (this)** only verifies the seam Tier 1 cannot: the SPA actually boots, React Flow mounts a
  graph in a real browser, and the CSRF login round-trip works in real JavaScript.
- It is deliberately read-mostly: it does **not** fork/edit/propose (Tier 1 owns that, deterministically),
  so a run leaves no data behind.

See the R02 review note and devlog 134 (§Tier 2) for the rationale and priority.

## Run

One-time (downloads the Chromium binary):

```
cd frontend
npm install            # picks up @playwright/test
npm run e2e:install    # playwright install chromium
```

Then, against a running server (defaults to the test server on `:8011`):

```
npm run e2e                                   # anonymous smokes only (app boots · editor renders)
E2E_USER=<u> E2E_PASS=<p> npm run e2e         # + the login CSRF round-trip
E2E_BASE_URL=https://cdgts.paleobytes.info npm run e2e   # point at another deployment
npm run e2e:ui                                # interactive UI mode
```

- `E2E_BASE_URL` — target base URL (default `http://127.0.0.1:8011`).
- `E2E_USER` / `E2E_PASS` — if set, the login smoke runs; otherwise it is skipped. It logs in and out only
  (no mutation). Do not hardcode credentials — pass them via env at run time.

Artifacts (`playwright-report/`, `test-results/`) are git-ignored.
