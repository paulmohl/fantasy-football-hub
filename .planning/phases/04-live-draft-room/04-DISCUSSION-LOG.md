# Phase 4: Live Draft Room (Snake) — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-30
**Phase:** 04-live-draft-room
**Areas discussed:** Panel layout & density, Pick clock & auto-draft, Rankings & queue UX, Pre-draft flow

---

## Panel Layout & Density

| Option | Description | Selected |
|--------|-------------|----------|
| 4-column fixed grid | Left (queue+alerts) / Center-left (board) / Center-right (best avail) / Right (roster+chat) | ✓ |
| 2-column split | Large board + tabbed right sidebar | |
| 3-column with floating chat | Board center dominates, chat overlays | |

**User's choice:** 4-column fixed grid (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed cells + horizontal scroll | Fixed cell size, board scrolls for large leagues | ✓ |
| Compact cells — full board always visible | Tiny cells fit everything without scroll | |
| Infinite vertical scroll | One column per round | |

**User's choice:** Fixed-size cells, horizontal scroll (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Panel headers with label + collapse | JetBrains Mono label + chevron toggle | ✓ |
| No headers | No panel labels | |
| Headers but no collapse | Labels without collapse | |

**User's choice:** Panel headers with collapse toggle (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Name + position badge + team | Color-coded position pill + muted team abbr | ✓ |
| Name + position + round/pick number | Includes pick number | |
| Name + photo thumbnail + position | 24x24 player photo | |

**User's choice:** Name + position badge + team (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Column highlight + pulsing accent border | Active column glows, clock in board header | ✓ |
| Full-width banner above board | Banner above board, column highlighted | |
| Pick clock in left sidebar only | Clock lives in sidebar | |

**User's choice:** Team column highlighted + pulsing accent border (recommended)

---

## Pick Clock & Auto-Draft

| Option | Description | Selected |
|--------|-------------|----------|
| Server-authoritative Redis deadline | Server writes deadline, clients count down from it | ✓ |
| Client countdown with server sync | Server sends tick events, clients run own countdown | |
| Pure client countdown | Server validates on submit only | |

**User's choice:** Server-authoritative (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| 30s + 10s warnings | Amber at 30s, red+pulse at 10s | ✓ |
| 60s + 30s + 10s three-stage | More granular escalation | |
| Single 20s threshold | One threshold | |

**User's choice:** 30s + 10s (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pure ADP | Best available by ADP rank | |
| ADP + positional need weighting | ADP + bonus for unfilled starter slots | ✓ |
| ADP + skip full positions | Filter out positions at roster cap | |

**User's choice:** ADP + positional need weighting (NOT recommended default — user overrode)
**Notes:** More intelligent auto-pick behavior preferred despite implementation complexity.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pause overlay for all | Semi-transparent overlay 'DRAFT PAUSED' + 5s resume countdown | ✓ |
| Pause banner only | Banner above board, no overlay | |
| Pause with reason field | Commissioner types reason for pause | |

**User's choice:** Pause overlay (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pick + your-turn sounds | Chime on pick, distinct tone when your turn | ✓ |
| Pick sound only | Only plays on pick submit | |
| No audio / browser notification | Browser Notification API instead | |

**User's choice:** Pick + your-turn sounds (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Redis stream replay from last_event_id | Client tracks last_event_id, server replays on reconnect | ✓ |
| REST snapshot on reconnect | GET /draft/{id}/state for full state | |
| Hybrid snapshot + stream | REST for board, stream for chat | |

**User's choice:** Redis stream replay (recommended)

---

## Rankings & Queue UX

| Option | Description | Selected |
|--------|-------------|----------|
| Sleeper ADP | From connected league format | |
| FantasyCalc rankings | Already integrated in Phase 2 | ✓ |
| User-defined only | No default, user imports or ranks | |

**User's choice:** FantasyCalc rankings (NOT recommended default — user overrode)
**Notes:** FantasyCalc already integrated; avoids separate Sleeper ADP fetch.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Each participant has personal rankings & queue | Personal best available sort per user | ✓ |
| Shared ranking managed by commissioner | One ranking for all | |
| Shared default + per-user local overrides | Starts shared, override locally | |

**User's choice:** Personal per-user rankings (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Star/heart button on hover | Click to queue, click again to remove | ✓ |
| Drag from best available to queue panel | Pure drag interaction | |
| Right-click context menu | Context menu with queue/star/stats | |

**User's choice:** Star/heart button (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Position tabs + live search | Tab strip ALL/QB/RB/WR/TE/K/DEF + search box | ✓ |
| Position filter only | Tab strip, no search | |
| Dropdown + search | Dropdown instead of tabs + search | |

**User's choice:** Position tabs + live search (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Visual tier dividers in best available | Horizontal divider rows in list | ✓ |
| Separate cheat sheet panel | Replaces best available for non-active pickers | |
| Popup cheat sheet on position tab click | Tier overlay popup | |

**User's choice:** Visual tier dividers (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Top 3 queue items + full list below when on clock | "FROM YOUR QUEUE" section at top | ✓ |
| Single suggested pick banner | Banner with top queue item | |
| No special on-clock UI | Queue and best available always independent | |

**User's choice:** Top 3 queue items section (recommended)

---

## Pre-Draft Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Draft setup page from My Connections | Schedule Draft button on league card | ✓ |
| Draft setup from /draft page | Setup form inline on /draft | |
| /draft/setup sub-route | Separate route for commissioner setup | |

**User's choice:** Draft setup from My Connections (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-draft lobby with participant list + countdown | Online/offline presence, queue setup, commissioner controls | ✓ |
| No lobby — draft room in waiting state | Full room visible, empty board with start datetime | |
| Simple confirmation page | Single Join button | |

**User's choice:** Pre-draft lobby (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Three modes: randomize + drag + import | All three in commissioner lobby panel | ✓ |
| Randomize only | One button, no manual control | |
| Manual only | Drag-and-drop only, no randomize or import | |

**User's choice:** Three modes (recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-loads recap in same room after final pick | Transitions in place, screenshot + CSV export | ✓ |
| Separate /draft/recap page | Redirect to own URL | |
| Recap accessible from dashboard | Notification-driven | |

**User's choice:** Auto-loads recap in same room (recommended)

---

## Claude's Discretion

- Emoji reactions (DR-11): reaction storage, display, badge placement
- Pick details drawer layout
- Chat message format
- Alert panel content
- Redis key naming
- DB model schemas for Draft, DraftPick, DraftQueue, DraftChatMessage, UserDraftRanking
- Audio file selection (royalty-free, ≤100KB)
- Commissioner pick-for-someone controls
- Pick clock configuration per round (likely single setting per draft)
- ICS invite format/content

## Deferred Ideas

- PDF export → Phase 8
- Mobile collapse → Phase 8
- Video/audio → Phase 6
- Auction variant → Phase 5
- Observer/spectator mode → V2
