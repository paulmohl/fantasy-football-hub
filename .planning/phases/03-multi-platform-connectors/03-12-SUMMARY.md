---
plan: "03-12"
status: complete
completed_at: "2026-06-29"
---

# 03-12 Summary — E2E and integration tests: Playwright connect flows, pytest service fixtures, MP-09 keeper validation

## What was built

### Backend pytest tests (backend/tests/test_auth_service.py — 10 tests)

**Group 1: Credential health in /users/me (MP-06)**
- `test_get_me_no_credentials_returns_empty_health` — GET /users/me with no credentials → `credential_health: []`
- `test_get_me_with_healthy_yahoo_credential` — healthy Yahoo credential → `[{platform:'yahoo', is_healthy:True}]`
- `test_get_me_with_unhealthy_espn_credential` — unhealthy ESPN credential → `[{platform:'espn', is_healthy:False}]`

**Group 2: Rate limit 429 response (MP-07)**
- `test_rate_limit_yahoo_returns_429_when_exceeded` — count > 200 → 429 with `X-Rate-Limited: true`
- `test_rate_limit_within_budget_returns_200` — count ≤ 200 → 200 (no rate limit)
- `test_rate_limit_espn_budget_100` — ESPN limit is 100; count=101 → 429

**Group 3: Keeper field extraction (MP-09)**
- `test_yahoo_keeper_extraction_from_fixture` — `normalize_yahoo_scoring` from fixture extracts `keeper_settings.max_keepers`
- `test_yahoo_unmodeled_rules_populated` — unknown stat_id populates `keeper_settings.unmodeled_rules`
- `test_espn_keeper_extraction_from_fixture` — `normalize_espn_scoring` extracts `acquisitionSettings.keeperCount`
- `test_espn_unmodeled_stat_id_in_list` — unknown statId populates `keeper_settings.unmodeled_rules`

### Backend pytest tests (backend/tests/test_rate_limit.py — 12 tests)
- CacheKey.rate_limit_yahoo / rate_limit_espn produce correct Redis key format
- `rate_limit_check`: count=1 sets TTL, count ≤ limit returns True, count > limit returns False
- `check_platform_rate_limit` dependency: within budget passes, over budget raises HTTPException 429
- `RateLimitedWithCache` exception returns 200 + cached body via app-level handler

### Backend pytest tests (backend/tests/test_yahoo_routes.py — 4 tests)
- No credential → 401
- Valid credential → 200 with leagues list
- Empty league list → handled gracefully
- /auth/yahoo unconfigured → 503

### Backend pytest tests (backend/tests/test_espn_routes.py — 5 tests)
- Invalid cookies → 401
- League not found → 404
- Private success → 200
- Public success → 200
- Public but private league → 403

### Playwright E2E specs (e2e/tests/)

**uat-7-espn-connect.spec.ts (5 tests)**
- ESPN option appears on platform selection step
- Clicking ESPN shows Private and Public sub-options
- ESPN private form has SWID, espn_s2, and League ID inputs
- Invalid ESPN cookies show inline error (not generic alert)
- ESPN public form has only League ID input (no SWID)

**uat-8-yahoo-connect.spec.ts (4 tests)**
- Yahoo option appears on platform selection
- Clicking Yahoo triggers navigation to /auth/yahoo
- `/connect?platform=yahoo` shows Yahoo connected state
- `/connect?reconnect=yahoo` shows platform selection (onboarding)

**uat-9-rate-limit.spec.ts (1 test)**
- `rate-limited` custom DOM event triggers visible toast notification

### Bug fixes discovered during testing
- `App.tsx`: `<RateLimitListener />` was placed inside `<Routes>` (invalid per React Router v6 — non-Route children aren't rendered). Moved to just before `<Routes>`.
- `api.ts`: 401 interceptor was retrying token refresh for platform-specific 401s (ESPN cookie invalid), causing redirect to login instead of showing inline error. Added URL pattern check to skip refresh for `/espn/`, `/yahoo/`, `/sleeper/` routes.
- Playwright `getByText` strict mode: Radix Toast renders both a visible `<span>` and an ARIA live region `<span role="status">`. Used `.first()` to target only the visible element.
- Playwright timing: `page.evaluate()` dispatched the event before React's `useEffect` registered the listener. Fixed with `page.waitForLoadState('networkidle')` before dispatch.

## Test counts
- Backend pytest: 150 passed, 2 skipped
- Playwright E2E: 49 passed, 1 skipped (out of 50 total across all UAT specs)
