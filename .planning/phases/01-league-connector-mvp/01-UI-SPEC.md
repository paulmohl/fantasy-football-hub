---
phase: 1
phase_name: League Connector MVP
status: draft
created: 2026-06-22
tool: shadcn/ui (Radix UI primitives + Tailwind — copy-in model, no components.json)
---

# UI-SPEC: Phase 1 — League Connector MVP

## Source Pre-Population Summary

| Source | Decisions Used |
|--------|---------------|
| DESIGN_CONCEPTS.md (locked ADR) | Color tokens, typography, navigation pattern, loading/toast/empty-state rules, iconography, accessibility baseline, conversational connector layout (DECISION-001, DECISION-005, DECISION-006, DECISION-007) |
| mockups/01-league-connector.html | Chat bubble sizing, option button styling, league card pattern, input row dimensions, bottom nav active state |
| frontend/tailwind.config.ts | All color tokens already registered; font families confirmed |
| frontend/src/pages/ConnectPage.tsx | Existing step machine (platform → username → leagues → done); interaction flow confirmed |
| frontend/src/pages/LoginPage.tsx | Auth form pattern; error inline below field; CTA button style |
| frontend/src/components/Layout.tsx | Bottom nav tab count, icons (Lucide), active color rule |
| REQUIREMENTS.md | AUTH-01 through AUTH-04, LC-01 through LC-12 — states and interactions mapped |
| User input | None required — all design questions answered by upstream artifacts |

---

## 1. Design System

**Tool:** Radix UI primitives + Tailwind CSS (shadcn/ui copy-in model). No `components.json`. Components built from `@radix-ui/*` packages already in `package.json` plus Tailwind class composition via `clsx` + `tailwind-merge`.

**Registry:** shadcn official patterns only. No third-party registries. Registry safety gate: not applicable.

**Icon library:** Lucide React (`lucide-react@0.395.0`). Already installed. Use `size={20}` / `size={22}` and `strokeWidth={1.75}` throughout. Custom football/helmet SVGs reserved for Phase 4 Draft Room — not needed in Phase 1.

---

## 2. Design Tokens

All tokens are already registered in `frontend/tailwind.config.ts` and `frontend/src/index.css`. Source: DESIGN_CONCEPTS.md DECISION-006.

### Color

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Background | `bg-bg` | `#0B0E14` | Page backgrounds, full-bleed areas |
| Surface | `bg-surface` | `#141822` | Cards, bottom nav, chat bubbles (app), input containers |
| Surface elevated | `bg-raised` | `#1B2030` | Option pills, league item cards, input fields |
| Border | `border-border` | `#262C3A` | All card/input borders default state |
| Accent (electric blue) | `text-accent` / `bg-accent` | `#3DA9FC` | CTA buttons, active nav tab, focus rings, checked states, avatar background, send button, selected option pills |
| Success | `text-success` / `bg-success` | `#5CC8A9` | Import success icon, "Connected" status badge, health = healthy |
| Warning | `text-warning` | `#F2B66D` | Stale sync badge, "expiring soon" credential warning |
| Danger | `text-danger` / `bg-danger` | `#F26D6D` | Inline form errors, destructive confirm button, health = unhealthy |
| Text primary | `text-text` | `#E8ECF1` | All body copy, labels, league names |
| Text secondary | `text-muted` | `#9AA3B2` | Placeholder, meta info, nav labels (inactive) |

**60/30/10 split for Phase 1:**
- 60% `bg-bg` — full-screen backgrounds (auth page, onboarding shell, connections list)
- 30% `bg-surface` / `bg-raised` — chat bubbles, cards, input wells, nav bar
- 10% `bg-accent` — CTA buttons, send button, checked states, active tab, focus borders

**Accent is reserved for:** primary CTA buttons (Import, Sign In, Create Account, Find My Leagues, Connect with Yahoo), checked/selected states on league items and option pills, active bottom nav tab, the "F" avatar on chat messages, focus ring on text inputs, send button background.

**Second semantic color:** `bg-danger` / `text-danger` — used only for: inline error messages, disconnect confirmation button, health status "Unhealthy" badge. Never used as a decorative color.

---

## 3. Typography

**Fonts:** `Inter` (UI) + `JetBrains Mono` (data). Both loaded via Google Fonts in `index.html`. Both registered in `tailwind.config.ts` as `font-sans` and `font-mono`.

### Type Scale (4 sizes)

| Role | Size | Weight | Line Height | Class |
|------|------|--------|-------------|-------|
| Page heading | 24px | 600 (semibold) | 1.2 | `text-2xl font-semibold` |
| Section heading / card heading / logo | 16px | 600 (semibold) | 1.2 | `text-base font-semibold` |
| Body / label | 14px | 400 (regular) | 1.5 | `text-sm` |
| Meta / badge / nav label | 12px | 600 (semibold) | 1.2 | `text-xs font-semibold` |

**Weights in use:** 400 (regular) and 600 (semibold). No other weights.

**JetBrains Mono usage:** Applied only to data values — last-sync timestamps, league season year when displayed in a data context, and (Phase 2+) numeric scores. Apply via `font-mono` utility class.

---

## 4. Spacing

8-point base scale. All spacing values must be multiples of 4px (Tailwind: `p-1`=4px, `p-2`=8px, `p-4`=16px, `p-6`=24px, `p-8`=32px, `p-12`=48px, `p-16`=64px).

| Context | Value | Tailwind |
|---------|-------|----------|
| Page horizontal padding | 16px | `px-4` |
| Page top padding | 48px | `pt-12` |
| Card internal padding | 16px | `p-4` |
| Chat bubble internal padding | 12px × 16px | `py-3 px-4` |
| Gap between stacked cards | 12px | `gap-3` or `space-y-3` |
| Gap between chat messages | 8px per row | `gap-0` on container, `py-2` per row |
| Option pill gap | 8px | `gap-2` |
| Bottom nav height | 64px | `h-16` |
| Top bar / header height | 52px | `h-[52px]` |
| Input height | 44px minimum | `min-h-[44px]` — enforced via min-h, not padding |
| Touch target minimum | 44px | enforced via `min-h-[44px]` on all interactive elements |
| Icon size | 20–22px | `size={20}` or `size={22}` on Lucide |
| Border radius — cards | 12px | `rounded-xl` |
| Border radius — inputs | 8px | `rounded-lg` |
| Border radius — pills / bubbles | 20px | `rounded-full` or `rounded-[20px]` |
| Border radius — buttons (primary) | 8px | `rounded-lg` |
| Border radius — badges | 4px | `rounded` |

---

## 5. Screens and Interaction Contracts

### 5A. Login / Sign Up Page (AUTH-01, AUTH-02, AUTH-03)

**Focal point:** The primary CTA button ("Sign In" / "Create Account") is the visual anchor; form fields and the OAuth button are subordinate entry points.

**Layout:** Single-column centered, `max-w-sm`, `min-h-screen`, vertically centered with `items-center justify-center`. No navigation — this is outside the Layout shell.

**States:**

| State | Visual |
|-------|--------|
| Default (sign in) | Logo mark + wordmark, email field, password field, submit button, toggle to "Create one" link |
| Register mode | Same fields; button label "Create Account"; toggle to "Sign in" link; email verification copy appears after submit |
| Loading | Button shows "Please wait…"; button disabled (`opacity-50`); no spinner — button text is sufficient for this short action |
| Error | Inline below fields: `text-danger text-sm bg-danger/10 border border-danger/20 rounded-lg px-3 py-2`. Error replaces the previous error on re-submit. |
| Post-register (email verification) | Replace form with: centered icon (envelope, Lucide `Mail`), heading "Check your email", body copy (see Section 7), no nav until verified |

**Google OAuth button (AUTH-02):** Render as secondary button below the primary submit. Style: `bg-surface border border-border rounded-lg px-4 py-3 w-full flex items-center gap-3 min-h-[44px]`. Google "G" logo as inline SVG (16×16). Label: "Continue with Google". Positioned above the email form or below — above preferred to reduce friction.

**Forgot password (AUTH-03):** Small link `text-accent text-sm hover:underline` below the password field, right-aligned. Label: "Forgot password?". Clicking opens an inline panel (not a modal) that shows an email input and "Send reset link" button. On success, collapse the panel and show a muted inline message: "Reset link sent — check your inbox."

**Password reset success toast:** Not a toast — inline only. Toasts reserved for async background results.

---

### 5B. Connect League — Conversational Onboarding (DECISION-001, LC-01 through LC-05, LC-08, AUTH-04)

**Focal point:** The most recent app chat bubble is the primary visual anchor; all other elements (option pills, input row, CTA) are subordinate.

**Layout:** Full-height column (`h-screen`), three vertical zones:
1. Top bar (52px) — centered logo (`text-base font-semibold`) + "Skip setup" ghost link at right (only shown during onboarding; hide once a league exists)
2. Chat scroll area (`flex-1 overflow-y-auto`) — centered column `max-w-[600px] w-full mx-auto`, `px-5 py-6`
3. Input row (fixed bottom, above bottom nav) — `max-w-[600px] w-full mx-auto`, `px-5 py-3`, `bg-surface border-t border-border`

**Conversation flow (DECISION-001):**

Step 1 — Platform selection:
- App bubble: "Hey! Welcome to FantasyHub. Which platform is your league on?"
- Inline option pills: [Sleeper] [Yahoo (coming soon, disabled)] [ESPN (coming soon, disabled)] [Other…]
- Disabled pills: `opacity-40 cursor-not-allowed pointer-events-none`
- After selection: user bubble appears with chosen platform name; pills become `pointer-events-none`; next app bubble appears after 400ms delay (simulate thinking)

Step 2 — Sleeper username:
- App bubble: "Got it. What's your Sleeper username? I'll find your leagues — no password needed."
- Inline `<input>` inside the bubble — `bg-raised border border-border rounded-lg px-3 py-3 w-full text-sm mt-3 min-h-[44px]` with placeholder "e.g. paulmohl". Focus border: `focus:border-accent`.
- "Find my leagues →" pill inside bubble — accent colored, enabled when input non-empty.
- Loading state: replace pill with a 3-dot typing indicator (3 dots, `bg-muted`, 7px, bounce animation as in mockup). Do not show a spinner.

Step 3 — League selection:
- App bubble: "Found [N] leagues. Pick the ones you want to import."
- League item cards inside bubble — each card: `bg-raised border border-border rounded-[10px] p-[12px_16px] flex items-center gap-3`. Checked state: `border-accent bg-[#0e1a2e]`.
- Checkbox: 18×18px, `rounded` (4px), checked fill `bg-accent border-accent` with white checkmark "✓" at 11px/semibold. Unchecked: `border-border` empty.
- League name: `text-sm font-semibold` (14px/600). Meta line: `text-xs text-muted` (12px). Format badge: `text-xs font-semibold` (12px/600), dynasty=`bg-[#1a1a3a] text-[#B39DDB]`, redraft=`bg-[#1a2a1a] text-success`, keeper=`bg-[#2a2010] text-warning`.
- "Import [N] league(s) →" CTA inside bubble — accent, updates count dynamically. Disabled + text "Select at least one" when count=0.

Step 4 — Import in progress:
- User bubble: "Import [league names]"
- Typing indicator (400ms) then app bubble: "Done! Importing your roster now — this takes about 10 seconds."
- Show a slim progress bar `h-1 bg-accent rounded-full` inside the bubble, animated width 0→100% over 10 seconds, or a pulsing bar if duration is unknown.

Step 5 — Done:
- App bubble: "You're all set. Head to My Team to see your lineup." with an inline "Go to My Team →" pill.

**Error handling (LC-08):**
- Bad username: app bubble "That username doesn't exist on Sleeper. Double-check the spelling and try again." Re-enable the input.
- No leagues found: app bubble "That account has no active leagues. Try a different username or reach out to your commissioner."
- Import failure: app bubble "Something went wrong importing that league. [Try again] [Contact support]". No partial state.

**Revisit connect flow (after first league):** The conversational shell is replaced by the "My Connections" page (5C). A "Connect another league" CTA at the top of 5C opens a condensed version of this flow (skip the welcome copy; start at Step 1).

---

### 5C. My Connections Page (LC-06, LC-07, LC-09, LC-10, LC-11, LC-12)

**Focal point:** The league name (Row 1) anchors each card; the health indicator (Row 3) is the secondary scan target.

**Layout:** Standard Layout shell (bottom nav visible). Page header inside scrollable content area. No sidebar.

**Page header:** `px-4 pt-12 pb-4`
- Heading: "My Leagues" — `text-2xl font-semibold text-text`
- Subtext (last sync summary): `text-sm text-muted` — "Last synced 3 minutes ago" — use `font-mono` for the time value only.
- Right side: "Connect another →" — `text-accent text-sm hover:underline`

**Connection cards:** One card per connected league.

Card structure (`bg-surface border border-border rounded-xl p-4 flex flex-col gap-3`):

Row 1: League name (`text-sm font-semibold text-text`, 14px/600) + platform badge (`text-xs font-semibold`, 12px/600, `bg-raised px-2 py-0.5 rounded text-muted`).

Row 2: Meta — `text-xs text-muted`: "[N] teams · [format] · [season] · Synced [time ago] (font-mono for time)"

Row 3: Health indicator:
- Healthy: `text-success` dot (6px circle) + "Connected" in `text-xs text-success`
- Unhealthy: `text-danger` dot + "Sync failed — [Reconnect]" where "Reconnect" is `text-accent text-xs hover:underline`
- Syncing: pulsing `text-warning` dot + "Syncing…"

Row 4: Actions row — right-aligned, `flex gap-4 justify-end`:
- "Refresh now" — `text-sm text-accent hover:underline`. While refreshing: replaced with "Refreshing…" in `text-muted` (no button). On complete: inline "Updated" in `text-success` for 2 seconds then reverts. (LC-07)
- "Disconnect" — `text-sm text-danger hover:underline`. (LC-11)

**Refresh progress:** If refresh exceeds 3 seconds, show a slim `h-1 bg-accent` progress bar at the top of the card, animated pulse, until complete or 10-second timeout. After timeout show error toast. (LC-07)

**Empty state (no connections, AUTH-04):**
- Full-screen empty state inside the Layout shell (no cards).
- Centered vertically in the available height.
- Icon: football SVG (`text-muted`, 48×48px placeholder, custom SVG Phase 1 acceptable as emoji `🏈` in `text-4xl`).
- Heading: "Connect your first league" — `text-xl font-semibold text-text`.
- Body: "Link a Sleeper league to unlock your personalized hub." — `text-sm text-muted text-center max-w-xs`.
- CTA button: "Connect a League" — `bg-accent text-white font-semibold rounded-lg px-6 py-3 min-h-[44px]` navigates to onboarding flow.
- This is the only page reachable before a league is connected. All other tabs are inaccessible (disabled in nav with `opacity-40 pointer-events-none` on Team, Draft, Trades, More).

**Disconnect confirmation (LC-11):**
- Modal dialog (Radix `@radix-ui/react-dialog`).
- Title: "Disconnect [League Name]?" — `text-base font-semibold text-text`
- Body: "Your credentials will be deleted. Cached data is kept for 30 days then removed. This cannot be undone."
- Footer buttons: [Keep League] (secondary, `bg-raised border border-border`) and [Disconnect League] (`bg-danger text-white font-semibold`).
- Focus trap inside modal. ESC closes. Background overlay: `bg-black/60 backdrop-blur-sm`.

---

## 6. Navigation

Source: DECISION-005 (locked).

**Mobile (< 640px):** Bottom tab bar, always visible except on Draft page. 5 tabs: My Team, League, Draft, Trades, More.
- Tab bar: `bg-surface border-t border-border h-16 flex items-center justify-around px-2`
- Active tab: icon + label `text-accent`
- Inactive tab: icon + label `text-muted hover:text-text`
- Icon: 22px, `strokeWidth={1.75}`
- Label: `text-xs font-semibold`
- Disabled tabs (before first league connection): `opacity-40 pointer-events-none` on Team, Draft, Trades, More

**Desktop (> 1024px):** Left rail (Phase 8). In Phase 1, mobile-first layout scales to desktop via centered `max-w-[600px]` column on onboarding and `max-w-2xl` on connections list. No desktop-specific rail built in Phase 1.

**Onboarding exception:** During first-time conversational onboarding (no leagues connected yet), the bottom nav is still rendered but tabs other than "League" (current) are disabled.

**Draft Room override:** Not applicable in Phase 1.

---

## 7. Copywriting Contract

### Primary CTAs

| Action | Label |
|--------|-------|
| Sign up | "Create Account" |
| Sign in | "Sign In" |
| OAuth | "Continue with Google" |
| Find leagues | "Find My Leagues" |
| Import (dynamic) | "Import [N] League" / "Import [N] Leagues" |
| Post-import nav | "View My Team →" (in success bubble) |
| Empty state CTA | "Connect a League" |
| Connect another | "Connect another →" |
| Refresh | "Refresh now" |
| Disconnect initiation | "Disconnect" |
| Disconnect confirm | "Disconnect League" (in modal, danger button) |
| Keep league (cancel disconnect) | "Keep League" |
| Send reset link | "Send Reset Link" |
| Skip onboarding | "Skip setup" |

### Empty States

| Screen | Heading | Body |
|--------|---------|------|
| My Connections (no leagues) | "Connect your first league" | "Link a Sleeper league to unlock your personalized hub." |
| Connections list (post-disconnect, none remain) | "No leagues connected" | "Connect a league to get started." |

### Error States

| Trigger | Copy |
|---------|------|
| Bad Sleeper username (LC-08) | "That username doesn't exist on Sleeper. Double-check the spelling and try again." |
| No leagues on account (LC-08) | "That account has no active leagues. Try a different username or reach out to your commissioner." |
| Import failed (LC-08) | "Something went wrong importing that league. [Try again] [Contact support]" |
| Auth — wrong credentials | "Incorrect email or password." |
| Auth — unverified email | "Please verify your email before signing in. [Resend verification email]" |
| Auth — email already registered | "An account with that email already exists. [Sign in instead]" |
| Auth — server error | "Something went wrong. Please try again." |
| Password reset — email not found | "No account found with that email address." |
| Password reset link sent | "Reset link sent — check your inbox." (inline success, not toast) |
| Refresh timeout (> 10s, LC-07) | Toast: "Sync timed out. Sleeper may be slow — try again in a moment." (sticky until dismissed) |
| Sync failure on connections page | Inline on card: "Sync failed — [Reconnect]" |
| Accessing another user's league (LC-09) | 404 page: "League not found." (no additional detail) |

### Destructive Action Copy

| Action | Confirmation approach |
|--------|-----------------------|
| Disconnect league (LC-11) | Modal dialog — title: "Disconnect [League Name]?" — body explains credential deletion + 30-day cache retention — two buttons: [Keep League] (secondary) + [Disconnect League] (danger) |

### Toasts

| Trigger | Type | Duration | Copy |
|---------|------|----------|------|
| Import success | Info | 4s auto-dismiss | "League imported successfully." |
| Refresh success | Info | 4s auto-dismiss | "League data refreshed." |
| Refresh timeout | Error | Sticky | "Sync timed out. Sleeper may be slow — try again in a moment." |
| Disconnect success | Info | 4s auto-dismiss | "[League Name] disconnected." |

Toast position: top-right. Toast style: `bg-surface border border-border rounded-lg px-4 py-3 shadow-lg text-sm text-text`. Error variant adds `border-danger/40`.

---

## 8. Loading States

Source: DECISION-007.

| Action | Loading pattern |
|--------|----------------|
| Page initial load | Skeleton: same shape as the content (connections list → 2 skeleton cards with `animate-pulse bg-raised rounded-xl h-24`) |
| Fetching leagues (Sleeper lookup) | Typing indicator (3 dots) inside the chat app bubble. Duration unknown — dots animate indefinitely until response. |
| Import in progress | Slim progress bar inside success bubble, 0→100% over estimated 10s. Pulsing if duration unknown. |
| Refresh ("Refresh now") | Button text replaced with "Refreshing…" in `text-muted`. Slim `h-1 bg-accent` bar at card top after 3s. |
| Auth form submit | Button text "Please wait…", button `disabled opacity-50`. No spinner. |
| Disconnect (after confirm) | Modal closes; card shows "Disconnecting…" for up to 2s, then removes. |

**No full-page spinners.** No blank loading screens. Every loading state must be scoped to the element being loaded.

---

## 9. Component Inventory

Components needed for Phase 1. Built from Radix primitives + Tailwind. No new npm packages beyond what is already in `package.json`.

| Component | Source | Notes |
|-----------|--------|-------|
| `<Button>` | Custom (Tailwind) | Variants: primary (`bg-accent text-white`), secondary (`bg-raised border border-border text-text`), ghost (`text-accent hover:underline`), danger (`bg-danger text-white`) |
| `<Input>` | Custom (Tailwind) | `bg-raised border border-border rounded-lg px-3 py-3 text-sm focus:border-accent min-h-[44px]` + error state `border-danger` |
| `<ChatBubble>` | Custom | App variant (`bg-surface border border-border`) + user variant (`bg-accent text-white`) |
| `<OptionPill>` | Custom | `bg-raised border border-border rounded-full px-4 py-2 text-sm font-semibold`; selected: `bg-accent border-accent text-white`; disabled: `opacity-40` |
| `<LeagueCard>` (inside chat) | Custom | Checkable card: default/checked/hover states per Section 5B |
| `<ConnectionCard>` | Custom | My Connections page card per Section 5C |
| `<Modal>` | `@radix-ui/react-dialog` | Already in package.json. Disconnect confirmation only. |
| `<Toast>` | `@radix-ui/react-toast` | Already in package.json. 4 states: info, error, sticky-error. |
| `<SkeletonCard>` | Custom | `animate-pulse bg-raised rounded-xl` — used for connections page initial load |
| `<TypingIndicator>` | Custom | 3 dots, `bg-muted`, bounce animation (already defined in `index.css` via keyframes) |
| `<ProgressBar>` | Custom | `h-1 bg-accent rounded-full` animated or pulsing |
| `<HealthDot>` | Custom | 6px circle, `rounded-full`, color per health status |
| `<FormatBadge>` | Custom | Dynasty/Redraft/Keeper badge per Section 5B color mapping |
| `<BottomNav>` | Exists (`Layout.tsx`) | Extend with disabled state handling |
| `<PageHeader>` | Custom | heading + subtext + right-side action link |

---

## 10. Animation and Motion

**Principle:** Fast, purposeful, not decorative. Reduced-motion media query must be respected everywhere (make animations instant via `@media (prefers-reduced-motion: reduce)`).

| Animation | Duration | Easing | Purpose |
|-----------|----------|--------|---------|
| Chat bubble fade-in | 150ms | `ease-out` | New messages entering (`fade-in` keyframe already in `tailwind.config.ts`) |
| Typing indicator dots | 1.2s loop | ease | Communicates "thinking" during API calls |
| Option pill active state | 150ms | `ease-out` | `transition-all` on border-color, background, color |
| Card hover border | 150ms | `ease-out` | `transition-colors` on `border-color` |
| Button hover | 150ms | `ease-out` | `transition-colors` on `background` |
| Modal open/close | 150ms | `ease-out` | Radix Dialog default animation |
| Skeleton pulse | 1.5s loop | ease | `animate-pulse` Tailwind default |
| App bubble appear delay | 400ms delay | — | Next app message waits before appearing (not a CSS animation — controlled by `setTimeout`) |
| Progress bar fill | ~10s linear | linear | Import progress estimate |

---

## 11. Accessibility Baseline

Source: DECISION-007. WCAG 2.1 AA required.

- All text combinations meet 4.5:1 contrast ratio minimum. `text-text` (#E8ECF1) on `bg-bg` (#0B0E14) = 14.5:1. `text-muted` (#9AA3B2) on `bg-surface` (#141822) = approximately 5.2:1.
- Every interactive element is keyboard-reachable: tab order follows visual order; no `tabindex > 0`.
- ARIA labels on icon-only buttons (send button: `aria-label="Send message"`, nav tabs with icon only: `aria-label="[Tab name]"`).
- Disconnect modal: focus trap via Radix Dialog. ESC dismisses.
- Form inputs have associated `<label>` elements via `htmlFor` / `id` pairs, not just placeholder text.
- Error messages are associated with their inputs via `aria-describedby`.
- League checklist items use `role="checkbox"` with `aria-checked` state.
- `@media (prefers-reduced-motion: reduce)` suppresses all CSS animations (bounce dots become static, fade-in skips, progress bar skips to full).
- Minimum touch target 44×44px on all interactive elements.
- `lang="en"` on `<html>` — already set in `index.html`.

---

## 12. Responsive Behavior

Phase 1 targets mobile-first. Desktop is a graceful scale-up, not a redesigned layout.

| Breakpoint | Behavior |
|------------|----------|
| < 640px (phone) | Full-width, `px-4`, bottom nav visible, chat column `max-w-full` |
| 640–1024px (tablet) | Same layout, chat column `max-w-[600px] mx-auto` |
| > 1024px (desktop) | Chat column `max-w-[600px] mx-auto`; connections list `max-w-2xl mx-auto`; bottom nav stays (left rail deferred to Phase 8) |

---

## 13. Out of Scope for Phase 1

The following visual/interaction elements are explicitly deferred:

- Light mode / theme toggle (dark only in Phase 1)
- Left rail navigation (Phase 8)
- Desktop-specific layout optimizations (Phase 8)
- Yahoo OAuth connect flow UI (Phase 3)
- ESPN cookie paste flow UI (Phase 3)
- Push notification opt-in prompt (Phase 8)
- PWA install prompt (Phase 8)
- Scoring rules table view (LC-04 — data is stored but display UI is Phase 2+)
- Roster shape visualization (LC-05 — captured in data; display deferred)
- "Skip setup" anonymous demo path — open question (logged in STATE.md), not blocked

---

*UI-SPEC status: draft — ready for checker validation*
*Written: 2026-06-22*
*Revised: 2026-06-22 — checker blocking issues resolved (BLOCK 1, BLOCK 2A, BLOCK 2B, BLOCK 3) + focal point statements added (5B, 5C)*
*Revised: 2026-06-22 (revision 2) — checker blocking issues resolved (BLOCK 1: consolidated type scale to 4 sizes, removed 17px, Section/card heading = 16px text-base; BLOCK 2: removed font-medium everywhere, meta/badge/nav = font-semibold only; BLOCK 3: input height = min-h-[44px], removed py-2.5; BLOCK 4: OptionPill px-4 py-2) + recommendations applied (FLAG Dim2: focal point added to 5A; FLAG Dim1: danger button = "Disconnect League" in 5C and Section 7)*
