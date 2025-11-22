# UI_MOCKUPS.md Corrections Plan & Progress

**Created:** 2025-11-22
**Status:** ✅ COMPLETE
**Purpose:** Track corrections to UI_MOCKUPS.md based on stakeholder feedback

---

## Background

After completing the UI_MOCKUPS.md enhancement (47 wireframes, 7,539 lines), a thorough review identified **73 arbitrary functional decisions** that needed stakeholder validation. The user provided feedback in `updates.txt`, and investigation revealed additional issues with V1/V2 feature separation.

---

## Key Findings from Investigation

### 1. Judge Feature is V2 Only
- **DOMAIN_MODEL.md line 221**: "Judge (V2 Only) - Represents a judge account for direct scoring (not in Phase 0/V1)"
- **V1 Flow**: Admin/Staff manually encodes battle results
- **V2 Flow**: Judges score via their own interface
- **Action**: Remove judge UI from V1, mark as V2 Only

### 2. Judges Assigned to Tournaments, NOT Pools
- **DOMAIN_MODEL.md line 228**: Judge entity has `tournament_id` FK, no `pool_id`
- **Action**: Remove all "Judge #3 missing from Pool B" type errors

### 3. Pools Are Always Evenly Distributed
- **VALIDATION_RULES.md line 242**: "Pool sizes must differ by at most 1"
- **Action**: Remove "imbalanced pools" errors (impossible with auto-distribution)
- **Action**: Change "4 per pool (avg)" to exact distribution display

---

## User Decisions from updates.txt

### REMOVE from UI_MOCKUPS.md:
- [ ] Judge assignment warnings (made up)
- [ ] Judge assignment to pools (judges → tournaments)
- [ ] Pool imbalance detection (impossible)
- [ ] Battle timeline tracking (not needed)
- [ ] Dancer win rate display (future feature)
- [ ] Sponsor slides Section 13.4 (add to roadmap)
- [ ] User Active/Inactive status (future soft delete)

### CORRECT in UI_MOCKUPS.md:
- [ ] Tournament name: ≥3 chars → **≥1 char**
- [ ] Blaze name: ≥2 chars → **≥1 char**
- [ ] Min pools: 1 → **2** (need finals)
- [ ] Max pools: warning → **hard max 10**
- [ ] Magic link cooldown: → **30 seconds**
- [ ] Magic link max: → **5 per 15 minutes, per-email**
- [ ] Magic link expiration: 15 min → **5 minutes**
- [ ] Pool display: "avg" → **exact distribution**
- [ ] Delete behavior: cascade warning → **prevent if active**
- [ ] Search limit: 100 → **10 initial, infinite scroll**

### ADD to UI_MOCKUPS.md:
- [ ] V1 Battle Encoding Interface (Admin/Staff encodes)
- [ ] Infinite scroll pattern (replace pagination)
- [ ] V2 Only markers on judge features

### ADD to IMPLEMENTATION_PLAN.md roadmap:
- [ ] Configurable HTMX polling intervals (admin parameters)
- [ ] Security documentation
- [ ] Deletion policy documentation
- [ ] Sponsor management feature
- [ ] Dancer analytics/win rate

### ADD to other docs:
- [ ] VALIDATION_RULES.md: Field lengths, pool limits
- [ ] DOMAIN_MODEL.md: Tournament.description, Tournament.date

---

## Execution Progress

### Phase 1: Setup & Preparation
- [x] Create temporary_plan_and_progress.md
- [x] Remove PHASE_1_PROGRESS.md

### Phase 2: Remove Made-Up/Deferred Features
- [x] Remove judge-to-pool assignment errors
- [x] Remove pool imbalance errors
- [x] Mark Judge Scoring Interface as V2 Only
- [x] Add V1 Battle Encoding Interface (Section 21)
- [x] Remove Sponsor Slides (Section 13.4)
- [x] Remove Dancer win rate/battle history
- [x] Remove Battle timeline tracking
- [x] Remove User Active/Inactive status

### Phase 3: Correct Validation Values
- [x] Field lengths (Tournament ≥1, Blaze ≥1)
- [x] Pool limits (Min 2, Max 10)
- [x] Rate limiting (30s, 5/15min, per-email)
- [x] Magic link expiration (5 min)
- [x] Pool display (exact, not average)
- [x] Delete behavior (prevent, not cascade)

### Phase 4: Update UI Patterns
- [x] Replace pagination with infinite scroll (Dancers list)
- [x] Update phase advancement display (pool sizes exact)

### Phase 5: Consistency Review
- [x] Review entire document for consistency
- [x] Verify V1/V2 markings
- [x] Check all validation messages

### Phase 6: Update Related Documentation
- [x] VALIDATION_RULES.md (added UI Field Validation section with field lengths, pool limits, magic link settings, deletion rules)
- [x] DOMAIN_MODEL.md (no changes needed - already correct)
- [x] IMPLEMENTATION_PLAN.md (added roadmap items for: polling config, security docs, deletion policy, sponsor feature, dancer analytics)

### Phase 7: Final Cleanup
- [x] Update temporary_plan_and_progress.md
- [x] Delete updates.txt (to be done)
- [x] Final consistency check

---

## Changes Log

| Date | Phase | Changes Made |
|------|-------|--------------|
| 2025-11-22 | Setup | Created this plan document |
| 2025-11-22 | Phase 1 | Removed PHASE_1_PROGRESS.md |
| 2025-11-22 | Phase 2 | Removed judge-to-pool errors, pool imbalance errors, sponsor slides (13.4→removed), battle history, win rate, user active status. Added V1 Battle Encoding Interface (Section 21). Marked Judge Scoring as V2 Only (Section 21.1). |
| 2025-11-22 | Phase 3 | Fixed validation: tournament name ≥1, blaze ≥1, pools min 2/max 10, magic link 5min expiry + 30s cooldown + 5/15min rate limit, delete prevention for active registrations |
| 2025-11-22 | Phase 4 | Replaced pagination with infinite scroll (10 initial, scroll for more). Fixed pool display to exact distribution. |
| 2025-11-22 | Phase 5 | Fixed Battle Detail V1/V2 notes, removed Battle Timeline, added V1 Encode Winner action, marked Judge Scores as V2 Only, fixed judge assignment to tournaments (not pools) |
| 2025-11-22 | Phase 6 | Updated VALIDATION_RULES.md (new UI Field Validation section), IMPLEMENTATION_PLAN.md (roadmap items) |
| 2025-11-22 | Phase 7 | Final cleanup and progress update |

---

## Notes

- Use Context7 MCP only if needed for HTMX/PicoCSS pattern reference
- Update UI_MOCKUP_UPDATE_PROGRESS.md after significant milestones
- Maintain consistency throughout all wireframes
