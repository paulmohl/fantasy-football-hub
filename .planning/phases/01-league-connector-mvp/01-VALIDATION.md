---
phase: 1
phase_slug: league-connector-mvp
created: 2026-06-23
source: extracted from 01-RESEARCH.md § Validation Architecture
---

# Validation Strategy: Phase 1 — League Connector MVP

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.2.0 + pytest-asyncio 0.23.0 |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd backend && pytest tests/ -x -q` |
| Full suite command | `cd backend && pytest tests/ --cov=app --cov-report=term-missing` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File |
|--------|----------|-----------|-------------------|------|
| AUTH-01 | POST /auth/register creates unverified user | integration | `pytest tests/test_auth.py::test_register -x` | Wave 1 |
| AUTH-01 | Unverified user cannot sign in | integration | `pytest tests/test_auth.py::test_unverified_login -x` | Wave 1 |
| AUTH-02 | GET /auth/google redirects to Google | integration | `pytest tests/test_oauth.py::test_google_redirect -x` | Wave 1 |
| AUTH-03 | POST /auth/forgot-password sends email (mocked) | integration | `pytest tests/test_auth.py::test_forgot_password -x` | Wave 1 |
| AUTH-04 | /users/me returns has_leagues=False for new user | integration | `pytest tests/test_users.py::test_me_no_leagues -x` | Wave 1 |
| LC-01 | Sleeper lookup proxies Sleeper API correctly | unit (mock httpx) | `pytest tests/test_sleeper.py::test_lookup -x` | Wave 1 |
| LC-08 | Bad username returns 404 with detail | integration | `pytest tests/test_sleeper.py::test_bad_username -x` | Wave 1 |
| LC-09 | User cannot access another user's league | integration | `pytest tests/test_leagues.py::test_ownership -x` | Wave 1 |
| LC-10 | Two users import same league → one league row | integration | `pytest tests/test_leagues.py::test_dedup -x` | Wave 1 |
| LC-11 | Disconnect deletes league_member, not league | integration | `pytest tests/test_leagues.py::test_disconnect -x` | Wave 1 |

## Sampling Rate

- **Per task commit:** `cd backend && pytest tests/ -x -q`
- **Per wave merge:** `cd backend && pytest tests/ --cov=app --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd-verify-work`

## Wave 0 Gaps (files that must be created before tests can run)

- [ ] `backend/tests/__init__.py` — test package init
- [ ] `backend/tests/conftest.py` — async test client, test DB, test Redis (mock or in-memory)
- [ ] `backend/tests/test_auth.py` — AUTH-01, AUTH-03
- [ ] `backend/tests/test_oauth.py` — AUTH-02
- [ ] `backend/tests/test_users.py` — AUTH-04
- [ ] `backend/tests/test_sleeper.py` — LC-01, LC-08 (mock httpx)
- [ ] `backend/tests/test_leagues.py` — LC-09, LC-10, LC-11
- [ ] `docker-compose.yml` at repo root — if absent

## Deferred Coverage

LC-04 (scoring table display) and LC-05 (visual roster shape) — data is stored and returned via API in Phase 1. Display UI deferred to Phase 2 by explicit developer decision (2026-06-23). These requirements are not covered by Phase 1 tests.
