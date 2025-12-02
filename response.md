 Critical Ambiguities Requiring Resolution

 1. Battle Progress Display Without Judges

 Problem: UI mockup shows live judge scoring progress, but V1 has no judges.

 Option A: Simplified Battle Display (Recommended for V1)
 Show ACTIVE battles with minimal info:
 - Performer names
 - Battle status: "Battle in Progress"
 - No score/round indicators (battle ongoing)
 - When COMPLETED: Show final outcome

 2. Tournament Selection for Projection

 UI Mockup URLs: /projection/battle/current (no tournament_id)
 ROADMAP Spec: /projection/{tournament_id} (explicit tournament_id)

 Options:

 Option A: Active Tournament Auto-Select
 /projection → Shows ACTIVE tournament automatically
 - Simpler for single-tournament events
 - Assumes only one ACTIVE at a time (enforced by DB constraint)
 - Issue: What if no ACTIVE tournament? -> Handling page (sth like "not available yet")

 3. Round Indicators Source

 Mockup shows: ● ● ● ○ ○ (5 rounds with 3 won)

 Problem: Current Battle.outcome structure doesn't store round-by-round data.

 Current Outcome Structures (from DOMAIN_MODEL.md):
 - Preselection: {"performer_id": 7.83} - Single final score
 - Pool: {"winner_id": "uuid", "is_draw": false} - Binary win/draw/loss
 - Finals: {"winner_id": "uuid"} - Binary win/loss

 Missing: Round-level granularity.

 Resolution Needed:
 Don't implement, correct the UI, which is totally wrong.

 4. Empty State Handling

 Scenarios not specified in mockups:
 - No active tournament
 - Tournament in REGISTRATION phase (no battles yet) -> Do we actually have that enum value for status?
 - Battle queue empty (all battles complete) -> What could possibly go wrong?
 - No standings available (preselection not started) -> What is a standing?

 Need: Empty state UI specs for each display component.

 5. Multi-Category Display Logic

 Tournament can have multiple categories (e.g., Hip Hop 1v1, Krump Duo 2v2).

 Ambiguous:
 - Does projection show ALL categories or specific category? -> Since we still don't know what /projection displays, it's a question to ask later.
 - How to cycle through categories if multiple? Don't understand.
 - Should standings show combined or per-category? What's a standing?

 UI_MOCKUPS line 5725: "Multiple Pools: Cycles through pools every 60 seconds"
 But not specified: Multiple categories handling. -> Don't understand

 ---
 Scope Creep Risks Identified

 1. Real-Time Judge Scoring Interface (HIGH RISK)

 Trigger: Implementing UI_MOCKUPS Section 13.1 as-is
 Scope Expansion:
 - Judge entity creation (database model, migrations)
 - Judge authentication and role management
 - Judge scoring interface (forms, validation)
 - Real-time score submission endpoints
 - Battle state management (rounds, judge progress)
 - This is essentially Phase 6 work pulled into Phase 4

 Mitigation: Explicitly defer judge features to Phase 6, simplify Phase 4 battle display. -> YES

 2. Round-by-Round Battle Tracking (MEDIUM RISK)

 Trigger: Trying to display round indicators without data
 Scope Expansion:
 - Modify Battle.outcome schema to store rounds
 - Update encoding forms to capture per-round data
 - Migration to convert existing battle data
 - Additional validation logic

 Mitigation: Use simplified battle display without rounds for V1. -> YES, remove every mention of the round data, it's definitelyt a scrope creep.

 3. Intelligent Display Mode Carousel (MEDIUM RISK)

 Trigger: User said "One projection URL, intelligent"
 Scope Expansion:
 - State machine to determine current display mode
 - Auto-transition logic based on tournament events
 - Configurable timing per display mode
 - Admin interface to control display remotely

 Mitigation: Start with simple static display selection, add intelligence in Phase 5. -> Needs to be explored for phase 4.

 4. Avatar Image Management (LOW RISK)

 Trigger: Mockups show performer avatars
 Scope Expansion:
 - Image upload functionality for dancers
 - Image storage (S3 or local filesystem)
 - Image resizing/optimization
 - Dancer profile enhancement

 Mitigation: Use placeholder avatars (initials or generic icon) in Phase 4. -> No icon/avatar at all. Remove it from everywhere.

 5. Bracket Generation Algorithm (LOW RISK)

 Trigger: Section 13.4 Bracket Visualization
 Scope Expansion:
 - Graph algorithm to build bracket from flat battle records
 - Support for various bracket sizes (4, 8, 16 performers)
 - Dynamic bracket layout rendering
 - This might be non-trivial

 Mitigation: Phase 4 focuses on 2-pool scenario (2 finals battles max), defer complex brackets. -> YES. But a bracket is a term I don't know, in the future use another word.

 ---
 What's Missing from Functional Specs

 1. Projection URL Structure (Critical)

 - Full path not specified in functional docs
 - Need to define before implementation starts
 response: /projection

 2. Public Access Security Model (Critical)

 - How to safely expose read-only tournament data?
 - Token-based? Session-less? IP whitelisting?
 - Rate limiting to prevent scraping?
 response: I don't know, will depend on what's displayed. Question for later.

 3. Battle State Granularity (Critical)

 - V1 has binary states: ACTIVE vs COMPLETED
 - Mockups imply intermediate states (round progress, judge status)
 - Need to reconcile
response: There should be Sth like "to come" -> Active -> Completed. Check documentation.
 4. Display Mode Selection Logic (Important)

 - User said "intelligent" but what does that mean?
 - Which display shows when?
 - Auto-transition timing?
 response: I don't know, let's explore from a UX perspective.

 5. Empty State UI Specifications (Important)

 - What displays when no active battles?
 - Tournament not started yet?
 - All battles complete?
response: idk, let's explore

 6. Performance Requirements (Nice-to-Have)

 - Max concurrent viewers?
 - Database query optimization needs?
 - Caching strategy?
 response: the screen will be displayed on a projection screen, so one user, maybe 5 max.

 7. Testing Strategy (Important)

 - How to test public endpoints?
 - Mock tournament data for projection testing?
 - Accessibility requirements (minimal per mockup but should confirm)?
 response: I don't know. PRovide possibilities.

 ---
 Proposed Pre-Requisite: Phase 3.5

 Phase 3.5: Battle Display Foundation

 Duration: 2-3 days
 Purpose: Align V1 battle encoding with projection display requirements

 Deliverables

 1. Battle State Clarification
 - Document V1 battle lifecycle (PENDING → ACTIVE → COMPLETED)
 - Specify what data is available during ACTIVE state
 - Define projection display for ACTIVE battles without judge data

 2. UI_MOCKUPS Section 13.1 Revision
 - Create V1-compatible battle display mockup
 - Remove judge status indicators
 - Simplify to: performer names, battle status, final outcome when complete
 - Optional: Add round tracking if feasible

 4. URL Structure Definition
 - Document full projection URL paths
 - Specify tournament selection logic (active vs explicit ID)
 - Define public access pattern (token? session-less?)

 5. Empty State Specifications
 - Define UI for each empty scenario
 - Add to UI_MOCKUPS.md Section 13

 6. Display Mode Logic
 - Specify "intelligent display" algorithm
 - Document auto-transition rules
 - Clarify multi-category handling

 Success Criteria

 - UI_MOCKUPS Section 13 fully aligned with V1 implementation
 - All URLs and routes documented
 - Battle display works without judges
 - Phase 4 can proceed without ambiguity

 ---
 Recommendations Before Proceeding

 Immediate Actions

 1. User Decision Required: Battle Display Approach
 - A) Simplified V1 battle display (no rounds/judges)

 2. User Decision Required: URL Structure
 - /projection (auto-select active)

 3. Create Phase 3.5 Plan
 If battle display needs changes:
 - Scope Phase 3.5 work
 - Update ROADMAP.md
 - Revise UI_MOCKUPS.md Section 13.1
 response: I don't understand the question.

 4. Document Exclusions
 Explicitly mark out-of-scope for Phase 4:
 - Judge entities and scoring interface (Phase 6)
 - Sponsor slides (removed from roadmap)
 - Avatar uploads (use placeholders) -> NO, see earlier response.
 - Complex bracket algorithms (MVP: 2-pool only)

 Phase 4 Scope Definition (Post Phase 3.5)

 IN SCOPE:
 - Public projection routes (no auth required)
 - HTMX auto-refresh (3s/10s/30s intervals)
 - Standings leaderboard (Section 13.2)
 - Battle queue display (Section 13.3)
 - Bracket visualization (Section 13.4, 2-pool MVP)
 - Battle display (Section 13.1, V1-compatible version)
 - Empty state handling
 - Basic styling (full-screen, large fonts, high contrast)

 OUT OF SCOPE:
 - Judge entities and scoring interface
 - Round-by-round tracking (unless added in Phase 3.5)
 - Sponsor slides
 - Avatar image uploads
 - Remote display control interface
 - Advanced bracket algorithms (>2 pools)
 - WebSocket/SSE (using HTMX polling only)
---