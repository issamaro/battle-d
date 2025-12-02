# Change: Phase 4 Projection Interface Documentation

**Created:** 2025-11-30
**Status:** In Progress
**Author:** AI Agent

## What's Changing
- Adding projection interface documentation to DOMAIN_MODEL.md
- Revising UI_MOCKUPS.md Section 13 (remove judges/rounds/avatars, add empty states)
- Creating GLOSSARY.md entries for projection terms (or creating file if doesn't exist)
- Updating ROADMAP.md Phase 4 scope with finalized requirements

## Why
- Phase 4 lacks functional specification
- UI mockups assume judges (Phase 6 feature) - creates implementation blocker
- Terminology unclear ("standing", "bracket") - user doesn't understand
- Empty states not specified - will cause incomplete implementation
- Implementation blocked without clear specs

## Affected Files

### Files to Update (from grep results):

**Level 1 (Source of Truth):**
- [ ] DOMAIN_MODEL.md (line 462, 629) - Add projection section, finals structure
- [ ] VALIDATION_RULES.md - (if needed for projection validation)

**Level 2 (Derived):**
- [ ] UI_MOCKUPS.md (Section 13, line 5213+) - Major revision needed:
  - Lines 5244, 5248: Remove round indicators (● ● ● ○ ○, "ROUND 4 OF 5")
  - Lines 5251, 5320-5323, 5429, 5436: Remove judge status (Judge #1 ✓, etc.)
  - Lines 4596, 4748, 4965, 5463: Remove judge/round references
  - Add empty states for all 4 subsections
- [ ] ROADMAP.md (lines 716, 881, 968) - Update Phase 4 scope
- [ ] GLOSSARY.md (line 66) - Update "bracket" → new term, add projection vocabulary

**Level 3 (Operational):**
- [ ] ARCHITECTURE.md (lines 426, 463-480, 592-610, 678-694, 887, 898, 963, 973, 1253, 1262) - Reference to "bracket" and "standings" but may not need updates (operational detail)

**Level 0 (Meta):**
- [ ] CHANGELOG.md - Add entry for all changes
- [ ] DOCUMENTATION_INDEX.md (line 154) - Check cross-references

**Supporting Files (Created During Planning - For Reference):**
- PHASE_4_DOCUMENTATION_PLAN.md - Contains detailed planning (numerous projection references)

## Progress
- [x] Step 1: Create workbench file
- [x] Step 2: Identify scope with grep
- [ ] Step 3: Answer user questions with code exploration
- [ ] Step 4: Update Level 1 docs (DOMAIN_MODEL, VALIDATION_RULES)
- [ ] Step 5: Update Level 2 docs (UI_MOCKUPS, ROADMAP, GLOSSARY)
- [ ] Step 6: Verify consistency with grep
- [ ] Step 7: Update CHANGELOG.md
- [ ] Step 8: Archive workbench

## User Questions to Answer
- [x] 1. **Battle states:** "There should be Sth like 'to come' -> Active -> Completed"
  - **ANSWER:** YES! From `app/models/battle.py` lines 40-45:
    - `PENDING` = "to come" (battle not started yet)
    - `ACTIVE` = battle in progress
    - `COMPLETED` = battle finished

- [x] 2. **Tournament status:** "Do we actually have that enum value for status?"
  - **ANSWER:** YES! From `app/models/tournament.py` lines 12-23:
    - `TournamentStatus`: CREATED, ACTIVE, COMPLETED
    - `TournamentPhase`: REGISTRATION, PRESELECTION, POOLS, FINALS, COMPLETED
  - Note: Phase `REGISTRATION` exists, not a status

- [ ] 3. **Terminology:** "What is a standing?" / "What's a bracket?"
  - **ANSWER (from grep):**
    - "standing" = pool rankings table showing W-D-L records and points (ARCHITECTURE.md lines 592-610)
    - "bracket" = single-elimination finals structure (GLOSSARY.md line 66, ARCHITECTURE.md lines 463-480)
  - **USER NEEDS:** Rename "bracket" to clearer term (user doesn't understand it)

- [ ] 4. **Multi-category:** "Don't understand cycling through categories"
  - **CLARIFICATION NEEDED:** Tournaments can have multiple categories (Hip Hop 1v1, Krump 2v2, etc.)
  - Question: Should projection show one category at a time? Or all? Or cycle through them?
  - **ACTION:** Present options to user in UX flow documentation

- [ ] 5. **Empty states:** "What displays when no active battles?"
  - **ACTION:** Define 8 empty state scenarios in UI_MOCKUPS updates:
    1. No active tournament
    2. Tournament in REGISTRATION phase
    3. No battles created yet
    4. No active battle (all PENDING or COMPLETED)
    5. Battle queue empty
    6. No standings data
    7. Finals not started
    8. Tournament COMPLETED

## User Decisions (from response.md)
- ✅ Simplified V1 battle display (no rounds, no judges)
- ✅ URL: `/projection` (auto-select active tournament)
- ✅ Remove scope creep: judges, rounds, avatars, sponsors
- ✅ Rename "bracket" term (user doesn't understand it)

## Notes
[Decisions and rationale as we proceed]
