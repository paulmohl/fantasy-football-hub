# Decisions Intel
# Source: DESIGN_CONCEPTS.md (ADR, locked: true)
# Synthesized by gsd-doc-synthesizer

---

## DECISION-001 — League Connector Screen Direction

status: LOCKED
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Screen 1 — League Connector onboarding UI

Decision statement: Option C (Conversational onboarding chat) is the chosen direction for the League Connector screen. A full-height chat interface asks one question at a time and guides the user through platform selection, credential entry, and league selection in a conversational flow.

Rationale recorded in source: Differentiated from competitors; approachable tone; easy to extend with help replies.

Constraint imposed: Do not re-open voting on this decision. Open a new issue to propose a revision.

---

## DECISION-002 — Team Manager Dashboard Screen Direction

status: LOCKED
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Screen 2 — Team Manager Dashboard layout

Decision statement: Option B (Card-based, scannable vertical stack) is the chosen direction for the Team Manager Dashboard. A vertical stack of focused cards, each answering one question, designed for thumb-scroll on mobile and comfortable on desktop.

Rationale recorded in source: Scannable; excellent on mobile; friendly to new users.

Constraint imposed: Do not re-open voting on this decision. Open a new issue to propose a revision.

---

## DECISION-003 — Draft Room Screen Direction

status: LOCKED
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Screen 3 — Live Draft Room layout

Decision statement: Option B (Bloomberg Terminal — high-density data) is the chosen direction for the Live Draft Room. Maximum information per pixel, treating the draft as a fast-moving data stream. All data — board, best available, roster, queue, chat, alerts — is visible simultaneously in a dense terminal layout.

Rationale recorded in source: Maximum info per pixel; power-user gold; looks unlike any other fantasy app.

Constraint imposed: Do not re-open voting on this decision. Open a new issue to propose a revision.

Note: PHASES.md task 4.4 references "Broadcast aesthetic CSS pass (Option A or C from DESIGN_CONCEPTS.md)" — this is superseded by the locked DECISION-003 which selects Option B. See INFO entry in INGEST-CONFLICTS.md.

---

## DECISION-004 — Trade Evaluator Screen Direction

status: LOCKED
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Screen 4 — Trade Evaluator layout

Decision statement: Option C (Decision-tree impact analysis) is the chosen direction for the Trade Evaluator. The trade is presented as a decision tree of consequences — starting lineup change, net weekly impact, playoff-week impact, roster shape risk, and dynasty value — with AI verdict at the bottom.

Rationale recorded in source: Most decision-useful; treats the user as smart; differentiated.

Constraint imposed: Do not re-open voting on this decision. Open a new issue to propose a revision.

Note: PHASES.md task 7.3 references "Side-by-side value totals (Option A from DESIGN_CONCEPTS.md)" — this is superseded by the locked DECISION-004 which selects Option C. See INFO entry in INGEST-CONFLICTS.md.

---

## DECISION-005 — Navigation Pattern

status: LOCKED
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Cross-screen navigation pattern (all screens)

Decision statement: Option C (Bottom tab bar on mobile + top navigation bar on desktop) is the chosen navigation pattern. Mobile uses bottom tabs (home, team, league, draft, more). Desktop uses a left rail. The Draft Room overrides navigation entirely with a full-screen broadcast mode.

Rationale recorded in source: Best mobile pattern; pairs with top nav on desktop.

Constraint imposed: Do not re-open voting on this decision. Open a new issue to propose a revision.

---

## DECISION-006 — Design Tokens (Proposed)

status: proposed (not locked — tokens table marked "proposed" in source)
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Visual design system — color palette and typography

Decision statement: A dark-first palette with the following token values is proposed for all screens. Light palette to be derived in V1. Draft Room is always dark regardless of user preference.

Token values:
- Background (dark): #0B0E14
- Surface: #141822
- Surface elevated: #1B2030
- Primary accent: #3DA9FC (electric blue, used sparingly)
- Success: #5CC8A9
- Warning: #F2B66D
- Danger: #F26D6D
- Text primary: #E8ECF1
- Text secondary: #9AA3B2
- Border: #262C3A
- Font (UI): Inter
- Font (data tables): JetBrains Mono

---

## DECISION-007 — Cross-Screen UX Patterns (Proposed)

status: proposed (part of locked ADR document but described as cross-screen proposals, not voted decisions)
source: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md
scope: Empty states, loading states, toasts, alerts, iconography, accessibility

Decision statement: The following cross-screen UX patterns apply to all screens:

Empty states: Explicit empty-state design required per screen; big CTA, no skeletons; must never look like errors.

Loading states: Skeletons preferred over spinners for predictable-shape views (rosters, lineups, draft board). Spinners only for short indeterminate actions (sending a trade, applying a lineup).

Toasts and alerts:
- Toasts: ephemeral, non-blocking, top-right; 4-second auto-dismiss for info; sticky for errors
- Modal alerts: only for confirmations and destructive actions
- Banners: persistent, top of page, for state requiring user action (broken connection, stale data)

Iconography: Lucide React for line icons; sport-specific glyphs (helmet, football) as custom SVG.

Accessibility: WCAG 2.1 AA contrast on all text; every interactive element keyboard-reachable; ARIA labels on icon-only buttons; focus traps in modals; reduced-motion media query honored.
