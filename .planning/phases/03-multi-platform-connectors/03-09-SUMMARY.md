---
plan: "03-09"
status: complete
completed_at: "2026-06-29"
---

# 03-09 Summary — Platform rate limiting: fixed-window Redis, RateLimitedWithCache, X-Rate-Limited header

## What was built

- `backend/app/core/cache.py` — Extended with rate limit keys and TTL:
  - `CacheKey.rate_limit_yahoo(user_id)` → `ratelimit:yahoo:{user_id}`
  - `CacheKey.rate_limit_espn(user_id)` → `ratelimit:espn:{user_id}`
  - `CacheTTL.RATE_WINDOW = 600` (10-minute fixed window)

- `backend/app/core/rate_limit.py` (new):
  - `PLATFORM_LIMITS = {"yahoo": 200, "espn": 100, "sleeper": 100}`
  - `RateLimitedWithCache(Exception)` — non-HTTPException so app handler returns 200 + cached body
  - `rate_limit_check(redis, key, limit, window)` — Redis INCR+EXPIRE fixed-window; TTL set only on count==1
  - `check_platform_rate_limit(platform)` — FastAPI Depends factory; raises 429 or RateLimitedWithCache

- `backend/app/main.py` — Added exception handler for `RateLimitedWithCache`:
  - Returns 200 with cached JSON body + `X-Rate-Limited: true` header

- `frontend/src/lib/api.ts` — Extended response interceptor:
  - Detects `X-Rate-Limited: true` header on successful responses
  - Dispatches `rate-limited` custom DOM event with `{platform}` detail
  - Platform extracted from URL: `/yahoo` → 'Yahoo', `/espn` → 'ESPN'
  - Platform 401s skip the JWT refresh retry (added URL pattern check)

- `frontend/src/App.tsx` — `RateLimitListener` component:
  - Listens for `rate-limited` custom event
  - Shows toast: `"{platform} data rate-limited — showing cached results"`

## Key design decisions
- `RateLimitedWithCache` is a plain Exception (not HTTPException) so the app-level handler can return HTTP 200 (cached hit is not an error)
- Fixed-window counting: TTL only set when count==1 (first call in window) to avoid resetting the window on each request
- Platform 401s exempt from JWT refresh to prevent redirect-to-login on ESPN cookie auth failures
