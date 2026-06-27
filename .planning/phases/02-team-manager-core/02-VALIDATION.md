---
phase: 2
slug: team-manager-core
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-26
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) / vitest (frontend) |
| **Config file** | backend/pyproject.toml / frontend/vite.config.ts |
| **Quick run command** | `docker compose exec backend pytest tests/ -x -q` |
| **Full suite command** | `docker compose exec backend pytest tests/ && docker compose exec frontend npm run test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec backend pytest tests/ -x -q`
- **After every plan wave:** Run full suite
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | TM-01 | — | N/A | unit | `docker compose exec backend pytest tests/test_lineup_optimizer.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | TM-01 | — | N/A | unit | `docker compose exec backend pytest tests/test_lineup_optimizer.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | TM-02, TM-03 | — | N/A | unit | `docker compose exec backend pytest tests/test_projection_service.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | TM-03, TM-04 | — | N/A | unit | `docker compose exec backend pytest tests/test_lineup_optimizer.py -x -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 2 | TM-09 | T-02-03-01 | Indoor stadiums return null | unit | `docker compose exec backend pytest tests/test_weather_service.py -x -q` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 2 | TM-09 | T-02-03-01 | Wind threshold 20 mph | unit | `docker compose exec backend pytest tests/test_weather_service.py -x -q` | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 2 | TM-05, TM-06, TM-07 | — | N/A | unit | `docker compose exec backend pytest tests/test_waiver_ranker.py -x -q` | ❌ W0 | ⬜ pending |
| 2-04-02 | 04 | 2 | TM-06, TM-07 | — | N/A | unit | `docker compose exec backend pytest tests/test_waiver_ranker.py -x -q` | ❌ W0 | ⬜ pending |
| 2-05-01 | 05 | 3 | TM-08 | T-02-05-01 | League isolation via get_league_for_user | integration | `docker compose exec backend pytest tests/test_team_routes.py::test_get_lineup -x -q` | ❌ W0 | ⬜ pending |
| 2-05-02 | 05 | 3 | TM-08 | T-02-05-01 | Route isolation (wrong user 404) | integration | `docker compose exec backend pytest tests/test_team_routes.py::test_isolation -x -q` | ❌ W0 | ⬜ pending |
| 2-06-01 | 06 | 3 | TM-08, TM-12 | T-02-06-01 | League isolation via get_league_for_user | integration | `docker compose exec backend pytest tests/test_team_routes.py::test_get_waiver -x -q` | ❌ W0 | ⬜ pending |
| 2-06-02 | 06 | 3 | TM-05, TM-07 | T-02-06-01 | FAAB vs rolling detection | integration | `docker compose exec backend pytest tests/test_team_routes.py::test_waiver_type_detection -x -q` | ❌ W0 | ⬜ pending |
| 2-07-01 | 07 | 4 | TM-01, TM-02 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-07-02 | 07 | 4 | TM-04 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-08-01 | 08 | 4 | DECISION-004 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-09-01 | 09 | 5 | TM-01, TM-02, TM-04 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-09-02 | 09 | 5 | TM-10, TM-15 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-10-01 | 10 | 5 | TM-05, TM-06, TM-07, TM-12 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-10-02 | 10 | 5 | TM-06, TM-12 | — | N/A | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-11-01 | 11 | 6 | TM-09, TM-13 | T-02-11-01 | No new data exposed | manual | `docker compose exec frontend npx tsc --noEmit 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-11-02 | 11 | 6 | TM-03, TM-08 | T-02-11-01 | Player data already user-visible | manual | `docker compose exec frontend npm run build 2>&1 \| tail -5` | n/a | ⬜ pending |
| 2-12-01 | 12 | 6 | TM-11, TM-14 | T-02-12-01 | League isolation on stats route | integration | `docker compose exec backend python -c "from workers.tasks import fantasycalc_prewarm; print('OK')"` | n/a | ⬜ pending |
| 2-12-02 | 12 | 6 | TM-12, TM-13 | T-02-12-01 | Stats route uses get_league_for_user | integration | `docker compose exec backend python -c "from app.api.v1.team import router; routes=[r.path for r in router.routes]; assert any('stats' in r for r in routes)"` | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_lineup_optimizer.py` — stubs for TM-01, TM-02, TM-04
- [ ] `backend/tests/test_waiver_ranker.py` — stubs for TM-05, TM-06, TM-07
- [ ] `backend/tests/test_projection_service.py` — stubs for TM-03, TM-04
- [ ] `backend/tests/test_trade_evaluator.py` — stubs for TM-08
- [ ] `backend/tests/test_weather_service.py` — stubs for TM-09
- [ ] `backend/tests/test_team_routes.py` — route-level integration stubs for all five /team/* endpoints
- [ ] `backend/tests/conftest.py` — extend with mock FantasyCalc + Sleeper clients

*Existing pytest infrastructure from Phase 1 covers the framework install.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Weather chip display on card | TM-09 | UI rendering, not logic | Open player card for outdoor QB in rainy week; verify weather chip visible |
| Drag lineup override persists | TM-15 | dnd-kit interaction | Drag RB to flex, refresh page, verify override remembered |
| League switcher context swap | DECISION-004 | Multi-league state | Import 2 leagues, switch between them, verify all data re-fetches |
| PlayerDetailDrawer renders matchup_grade + opponent_rank_vs_position + recent_usage_trend | TM-03 | UI rendering | Open drawer for any player; verify all three fields render with non-empty values |
| PlayerComparePanel shows both playerA and playerB with comparison data | TM-08 | UI interaction | Open drawer, click Compare, tap second player; verify recommendation + point delta + three factors render |
| TrendChart uses real data (not dummyTrendData) after Plan 12 | TM-13 | UI rendering | Open player drawer in-season; verify trend line is not a random pattern |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
