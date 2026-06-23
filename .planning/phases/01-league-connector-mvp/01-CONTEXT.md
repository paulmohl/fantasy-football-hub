---
phase: 1
phase_name: League Connector MVP
status: decisions-recorded
created: 2026-06-23
source: developer decisions during plan verification
---

# Phase 1 Context — League Connector MVP

## Phase Boundary

Phase 1 delivers user authentication, Sleeper league connection, and the connections management UI. It does NOT include lineup recommendations, waiver wire, or trade evaluation (Phase 2+).

## Implementation Decisions

### Authentication
- JWT access tokens: 15-minute expiry (in-memory on client, not localStorage)
- Refresh tokens: httpOnly cookie, 30-day rotating
- Google OAuth via authlib; email/password via bcrypt
- Email verification required before first sign-in

### Sleeper Integration
- No OAuth required — Sleeper public API, username-based lookup
- Season fetched dynamically from `/v1/state/nfl`, not hardcoded
- All Sleeper responses stored as JSONB verbatim before validation

### Dependencies
- Replace `python-jose` with `PyJWT 2.x` (python-jose is near-abandoned)
- Add: `authlib`, `itsdangerous`, `fastapi-mail` to backend
- Add: `@radix-ui/react-checkbox` to frontend

### Multi-tenant Safety
- All league endpoints filter through `get_league_for_user` dependency
- Unauthorized access returns 404 (not 403) to avoid resource enumeration

### Frontend
- ConnectPage.tsx rebuilt as dual-mode: conversational onboarding (hasLeagues=false) OR My Connections (hasLeagues=true)
- Auth state in Zustand store with `hasLeagues` flag
- 401 interceptor in api.ts: retry once via POST /auth/refresh before redirecting to login

### Claude's Discretion
- SMTP service: Gmail App Password for dev (no-ops when unconfigured)
- Alembic migration naming convention
- Test fixture structure (async SQLAlchemy session + mock Redis)

## Deferred Decisions (explicit)

### LC-04 — Scoring Table Display → Phase 2
**Decision date:** 2026-06-23
**Decision:** Scoring rules are stored as JSONB in Phase 1 and returned via `GET /leagues/{id}`. The UI component that renders the full scoring table with non-standard rule flags is deferred to Phase 2.
**Rationale:** MVP focus — data capture is more important than display for the initial connection flow. Phase 2 Team Manager will surface scoring context where it matters (lineup decisions).

### LC-05 — Visual Roster Shape → Phase 2
**Decision date:** 2026-06-23
**Decision:** Roster format (slot positions and eligibility) is stored as JSONB in Phase 1 and returned via `GET /leagues/{id}`. The visual roster shape component on the connection summary is deferred to Phase 2.
**Rationale:** Same as LC-04 — data is captured; display surface is Team Manager context where it's actionable.

## Deferred Ideas

- Yahoo OAuth connect flow (Phase 3)
- ESPN cookie-based auth (Phase 3)
- Push notification opt-in (Phase 8)
- PWA install prompt (Phase 8)
- "Skip setup" anonymous demo path (open question — not blocking Phase 1)
- Left rail navigation desktop layout (Phase 8)

---

*Phase: 01-league-connector-mvp*
*Context recorded: 2026-06-23 — post-plan-verification decisions*
