---
phase: 2
slug: team-manager-core
status: draft
nyquist_compliant: false
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
| 2-01-01 | 01 | 1 | TM-01 | — | N/A | unit | `docker compose exec backend pytest tests/test_lineup.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_lineup_optimizer.py` — stubs for TM-01, TM-02
- [ ] `backend/tests/test_waiver_ranker.py` — stubs for TM-05, TM-06, TM-07
- [ ] `backend/tests/test_projection_service.py` — stubs for TM-03, TM-04
- [ ] `backend/tests/test_trade_evaluator.py` — stubs for TM-08
- [ ] `backend/tests/conftest.py` — extend with mock FantasyCalc + Sleeper clients

*Existing pytest infrastructure from Phase 1 covers the framework install.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Weather chip display on card | TM-09 | UI rendering, not logic | Open player card for outdoor QB in rainy week; verify weather chip visible |
| Drag lineup override persists | TM-15 | dnd-kit interaction | Drag RB to flex, refresh page, verify override remembered |
| League switcher context swap | DECISION-004 | Multi-league state | Import 2 leagues, switch between them, verify all data re-fetches |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
