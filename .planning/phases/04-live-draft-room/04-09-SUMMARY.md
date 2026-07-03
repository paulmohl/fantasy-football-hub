---
phase: 04-live-draft-room
plan: 09
subsystem: frontend/components/draft
tags: [react, tailwind, zustand, socket.io-client, draft-chat, draft-alerts, roster-panel, bloomberg-terminal]

dependency_graph:
  requires:
    - 04-06 (useDraftStore: chatMessages, alerts, myRoster, availablePlayers, config; getDraftSocket from socket.ts)
    - 04-07 (PositionBadge: reused in RosterPanel for per-pick position pills)
  provides:
    - frontend/src/components/draft/ChatPanel.tsx (live draft chat with socket send, 500-char limit, auto-scroll)
    - frontend/src/components/draft/AlertsPanel.tsx (draft event feed, newest-first, colored prefixes)
    - frontend/src/components/draft/RosterPanel.tsx (user roster by round with PositionBadge)
  affects:
    - 04-11 (DraftPage wiring — replaces col 4 placeholder in DraftRoom with RosterPanel + ChatPanel stacked)

tech-stack:
  added: []
  patterns:
    - ChatPanel reads useDraftStore.chatMessages (server-pushed state); sends via getDraftSocket().emit('chat', ...)
    - AlertsPanel reverses alerts array for newest-first display; regex-based prefix matching for color coding
    - RosterPanel groups myRoster picks by round (Record<number, DraftPick[]>) with Object.keys().sort()
    - All three panels read exclusively from useDraftStore; no local state for message/alert/pick lists

key-files:
  created:
    - frontend/src/components/draft/ChatPanel.tsx
    - frontend/src/components/draft/AlertsPanel.tsx
    - frontend/src/components/draft/RosterPanel.tsx

key-decisions:
  - "useAuthStore(s => s.userId) not s.user_id — auth.ts field is camelCase userId; plan used (s as any).user_id which always returns undefined"
  - "POSITION_ORDER constant removed from RosterPanel — declared but never used; noUnusedLocals in tsconfig.app.json would fail compile"
  - "RosterPanel groups by round not position — plan spec says 'grouped by round'; position grouping deferred to 04-11 or future enhancement"
  - "Char count shown only when draft.length > 400 — less visual noise for typical messages; visible in danger zone approaching 500-char server limit"

requirements-completed:
  - DR-05
  - DR-06
  - DR-10

duration: ~4min
completed: "2026-07-03"
---

# Phase 4 Plan 09: ChatPanel, AlertsPanel, RosterPanel Summary

**Live draft chat (socket send + auto-scroll + 500-char limit), colored draft event feed (newest-first with regex prefix matching), and real-time roster panel (grouped by round with PositionBadge) — right sidebar components for the Bloomberg Terminal draft room**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-07-03T14:03:55Z
- **Completed:** 2026-07-03T14:07:44Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created ChatPanel: reads `useDraftStore.chatMessages`, sends via `getDraftSocket().emit('chat', ...)` with ack callback; Enter-to-send (no Shift); auto-scroll on new messages; 500-char limit with char counter at >400; highlights own messages ("You:") in text-accent; `data-testid="chat-input"` for E2E
- Created AlertsPanel: reads `useDraftStore.alerts`; reverses for newest-first; regex-based ALERT_PATTERNS classify events into [AUTO]/[PAUSE]/[RESUME]/[PICK]/[CLOCK]/[INFO] with matching Tailwind colors; alert count badge in header
- Created RosterPanel: reads `useDraftStore.myRoster` and `availablePlayers`; groups picks by round with round headers; PositionBadge per pick; player name/team/bye week from availablePlayers lookup; AUTO badge + opacity-60 for auto-picks; drafted/totalRounds counter; `data-testid="roster-pick-{pick_num}"` on each row

## Task Commits

1. **Task 1: ChatPanel with auto-scroll and socket send** - `e4f98e59` (feat)
2. **Task 2: AlertsPanel and RosterPanel** - `de38f039` (feat)

## Files Created/Modified

- `frontend/src/components/draft/ChatPanel.tsx` — Live chat: useDraftStore.chatMessages, socket.emit('chat'), auto-scroll, 500-char limit, own-message highlight
- `frontend/src/components/draft/AlertsPanel.tsx` — Draft event feed: newest-first, regex prefix classification, amber/emerald/red color coding
- `frontend/src/components/draft/RosterPanel.tsx` — User roster by round: PositionBadge, player lookup from availablePlayers, auto-pick indicator

## Decisions Made

- `useAuthStore((s) => s.userId)` — Plan used `(s as any).user_id` but auth.ts defines `userId` (camelCase). The snake_case access always returns `undefined`, making every message appear from "other" user. Fixed to proper typed access.
- Removed `POSITION_ORDER` constant from RosterPanel — plan code declared it but never referenced it in JSX. With `noUnusedLocals: true` in tsconfig.app.json, this causes a compile error.
- Grouped by round (not position) in RosterPanel — plan spec says "grouped by round" in must_have truths; position grouping could be a future enhancement in 04-11 wiring.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed useAuthStore userId field name in ChatPanel**
- **Found during:** Task 1 (reading auth.ts before writing ChatPanel)
- **Issue:** Plan code: `useAuthStore((s) => (s as any).user_id as string | null ?? '')` — auth.ts defines field as `userId` (camelCase), not `user_id` (snake_case). The `(s as any).user_id` access always returns `undefined`. Every chat message would show "other user" styling even for own messages.
- **Fix:** Changed to `useAuthStore((s) => s.userId ?? '')` — directly typed, no cast needed.
- **Files modified:** `frontend/src/components/draft/ChatPanel.tsx`
- **Verification:** TypeScript compiles without errors; `s.userId` matches auth.ts interface
- **Committed in:** `e4f98e59` (Task 1 commit)

**2. [Rule 1 - Bug] Removed unused POSITION_ORDER constant from RosterPanel**
- **Found during:** Task 2 (RosterPanel implementation)
- **Issue:** Plan code declared `const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']` but never used it anywhere in the JSX or grouping logic. With `noUnusedLocals: true` in tsconfig.app.json, this is a TypeScript compile error.
- **Fix:** Removed the constant entirely. Grouping is by round (using `Object.keys(byRound).sort()`); position grouping is not implemented in this plan.
- **Files modified:** `frontend/src/components/draft/RosterPanel.tsx`
- **Verification:** 0 TypeScript errors for RosterPanel.tsx
- **Committed in:** `de38f039` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — correctness)
**Impact on plan:** Both fixes required for correct behavior and TypeScript compilation under strict settings. No scope changes.

## Issues Encountered

None beyond the two auto-fixed deviations above.

## Known Stubs

None. All three panels read live data from useDraftStore. No hardcoded values flow to UI rendering.

- Note: `config?.num_rounds ?? 15` in RosterPanel is a sensible runtime default (not a stub) — renders 0/15 until config loads from socket, which is expected behavior before draft starts.

## Threat Surface Scan

ChatPanel sends `socket.emit('chat', { message })` — this is within the trust boundary documented in the plan's threat model (T-4-03): server's `on_chat` handler validates 500-char limit and authenticates via Socket.IO session; only server-emitted events update the chat message list (no client-fabricated messages persist).

No new network endpoints or auth paths introduced.

## Pre-existing Issues (Out of Scope)

- 19 TypeScript errors across `@/lib/utils` missing module in 19 existing components — pre-existing, not caused by this plan (same errors noted in 04-06-SUMMARY.md). Zero new errors introduced.

## Self-Check: PASSED

- `frontend/src/components/draft/ChatPanel.tsx` exists: FOUND
- `frontend/src/components/draft/AlertsPanel.tsx` exists: FOUND
- `frontend/src/components/draft/RosterPanel.tsx` exists: FOUND
- Task 1 commit `e4f98e59` in git log: FOUND
- Task 2 commit `de38f039` in git log: FOUND
- Zero TypeScript errors for the 3 new files: VERIFIED (grep returns empty)
- `bottomRef.current?.scrollIntoView` in ChatPanel useEffect: VERIFIED
- `socket.emit('chat', { message }` in handleSend: VERIFIED
- `maxLength={500}` and `data-testid="chat-input"` on textarea: VERIFIED
- `[...alerts].reverse()` for newest-first display in AlertsPanel: VERIFIED
- `text-amber-400` for PAUSE, `text-emerald-400` for RESUME/PICK, `text-red-400` for CLOCK: VERIFIED
- `useDraftStore((s) => s.myRoster)` in RosterPanel: VERIFIED
- Round grouping with `byRound[round]` map in RosterPanel: VERIFIED
- `pick.is_auto_pick` opacity-60 + AUTO badge in RosterPanel: VERIFIED
- `data-testid={roster-pick-${pick.pick_num}}` on each row: VERIFIED

---
*Phase: 04-live-draft-room*
*Completed: 2026-07-03*
