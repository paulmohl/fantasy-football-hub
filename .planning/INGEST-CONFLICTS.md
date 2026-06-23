# Conflict Detection Report

Ingest run: new project (MODE: new)
Docs consumed: 5 (1 ADR, 2 PRD, 1 SPEC, 1 DOC)
Precedence order applied: ADR > SPEC > PRD > DOC

---

### BLOCKERS (0)

No blocking conflicts detected. No LOCKED-vs-LOCKED ADR contradictions found in this ingest set. No UNKNOWN-confidence-low documents. No reference cycles in the cross-ref graph.

---

### WARNINGS (0)

No competing acceptance variants detected. Both PRD documents (PHASES.md and USER_STORIES.md) address distinct aspects of requirements — PHASES.md defines effort sizing, tier, and phase assignment; USER_STORIES.md defines Gherkin acceptance criteria per story ID. Where both address the same story, they are complementary, not contradictory.

---

### INFO (3)

[INFO] Auto-resolved: ADR (LOCKED) > PRD on Draft Room layout direction
  Source A: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md (ADR, locked: true)
    — Screen 3 (Draft Room) design decision is LOCKED as Option B (Bloomberg Terminal high-density layout)
  Source B: /c/Users/paul_/git/fantasy-football-hub/PHASES.md (PRD, task 4.4)
    — "Broadcast aesthetic CSS pass (Option A or C from DESIGN_CONCEPTS.md)"
  Resolution: DESIGN_CONCEPTS.md (ADR, locked) wins. The locked decision selects Option B.
    Task 4.4 in PHASES.md should be read as "Bloomberg Terminal aesthetic CSS pass (Option B from DESIGN_CONCEPTS.md)".
    The "Option A or C" language in PHASES.md reflects the pre-vote state of the document and is now stale.
  Action: Update task 4.4 wording in PHASES.md before routing to implementation.

[INFO] Auto-resolved: ADR (LOCKED) > PRD on Trade Evaluator primary layout
  Source A: /c/Users/paul_/git/fantasy-football-hub/DESIGN_CONCEPTS.md (ADR, locked: true)
    — Screen 4 (Trade Evaluator) design decision is LOCKED as Option C (Decision-tree impact analysis)
  Source B: /c/Users/paul_/git/fantasy-football-hub/PHASES.md (PRD, task 7.3)
    — "Side-by-side value totals (Option A from DESIGN_CONCEPTS.md)"
  Resolution: DESIGN_CONCEPTS.md (ADR, locked) wins. The locked decision selects Option C.
    Task 7.3 in PHASES.md should be read as implementing the decision-tree impact view (Option C), not the side-by-side mirror (Option A).
    Note: the user story REQ-te-value-totals requires showing value totals for both sides — this is compatible with Option C (the impact tree shows per-side totals within the tree nodes). No requirement is lost; only the primary layout framing changes.
    The DESIGN_CONCEPTS.md source notes "Option A (Side-by-side) for MVP" as its recommendation before the vote; the recorded locked decision overrides that recommendation with Option C.
  Action: Update task 7.3 wording in PHASES.md before routing to implementation. Confirm that the decision-tree view satisfies TE-010 acceptance criteria.

[INFO] Open architecture question — LLM provider for trade AI summary not yet resolved
  Source: /c/Users/paul_/git/fantasy-football-hub/ARCHITECTURE.md (section 11, open question 1)
    — "Claude (Anthropic) vs GPT-4o (OpenAI). Probably Claude given Paul's familiarity, but cost-per-trade and JSON-mode reliability are worth measuring."
  This is not a conflict. It is an unresolved design-vote item that becomes a dependency blocker before Phase 7 begins.
  Current state: synthesized intel records "Claude API" as the provisional implementation direction (per PHASES.md task 7.6 description and the ARCHITECTURE.md lean) but this has not been formally voted and locked.
  Action: Open a design-vote issue before Phase 7 starts. Candidates: Claude (Anthropic), GPT-4o (OpenAI). Blocking: task 7.6 (AI natural-language trade summary).
