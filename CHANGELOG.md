# Battle-D Documentation Changelog

**Purpose:** Track all significant documentation changes for historical reference

---

## [2025-11-22] - Phase 1.2: Documentation Consolidation

### Added
- **DOCUMENTATION_INDEX.md**: Central navigation hub with document hierarchy, decision tree, cross-reference map
- **DOCUMENTATION_CHANGE_PROCEDURE.md**: Standard procedure for modifying documentation (for humans and AI agents)
- **GLOSSARY.md**: Definitions of key terms (tournament, phase, blaze, tiebreak, etc.)
- **CHANGELOG.md**: This file for tracking documentation changes
- **DOMAIN_MODEL.md**: Added "Deletion Rules" section (§8) with cross-reference to VALIDATION_RULES.md
- **DOMAIN_MODEL.md**: Added Tournament `description` and `tournament_date` fields
- **DOMAIN_MODEL.md**: Added Tournament "Status Lifecycle" section explaining CREATED/ACTIVE/COMPLETED transitions
- **IMPLEMENTATION_PLAN.md**: Added Phase 1.2 roadmap items for future clarifications
- **UI_MOCKUPS.md**: Added validation reference note pointing to VALIDATION_RULES.md as source of truth

### Changed
- **VALIDATION_RULES.md**: Changed final phase name from `ARCHIVED` to `COMPLETED` (3 occurrences)
- **ARCHITECTURE.md**: Fixed minimum performer formula from `+2` to `+1` (2 occurrences)
- **DOMAIN_MODEL.md**: Updated Tournament status enum to include `created` state
- **UI_MOCKUPS.md**: Version bumped to 2.1, timestamp updated to 2025-11-22

### Fixed
- Resolved phase name inconsistency (ARCHIVED vs COMPLETED) across documents
- Resolved formula inconsistency (+2 vs +1) in ARCHITECTURE.md examples

### Archived
- `temporary_plan_and_progress.md` → `archive/UI_CORRECTIONS_2025-11-22.md`
- `UI_MOCKUP_UPDATE_PROGRESS.md` → `archive/UI_MOCKUP_UPDATE_2025-11-20.md`

---

## [2025-11-22] - UI_MOCKUPS.md Corrections (Prior to Phase 1.2)

### Changed
- Removed made-up features: judge-to-pool assignments, pool imbalance errors, sponsor slides
- Corrected validation values: tournament name ≥1 char, blaze ≥1 char, pools min 2/max 10
- Fixed magic link settings: 5 min expiry, 30s cooldown, 5/15min rate limit
- Fixed delete behavior: prevent if active registrations (not cascade)
- Replaced pagination with infinite scroll (10 initial, scroll for more)

### Added
- V1 Battle Result Encoding Interface (Section 21)
- V1/V2 markers on Judge-related sections

### Removed
- Sponsor Slides section (moved to roadmap)
- Dancer win rate/battle history display
- Battle timeline tracking
- User Active/Inactive status toggle

---

## [2025-11-20] - UI_MOCKUPS.md Enhancement Complete

### Added
- 47 wireframes across 28 pages
- Mobile and desktop layouts for all pages
- HTMX interaction patterns
- Accessibility annotations (WCAG 2.1 AA)
- Validation states for all forms

### Statistics
- Document grew from 1,290 to 7,539 lines (+6,249 lines)
- 156% of original target achieved

---

## [2025-11-19] - Minimum Performer Formula Change

### Changed
- **VALIDATION_RULES.md**: Updated formula from `(groups_ideal × 2) + 2` to `(groups_ideal × 2) + 1`
- **DOMAIN_MODEL.md**: Updated formula references

### Reason
- Original formula was overly restrictive
- New formula still ensures at least 1 performer is eliminated in preselection

---

## Format Guide

When adding new entries:

```markdown
## [YYYY-MM-DD] - Phase X.X: Brief Description

### Added
- **FILE.md**: Description of what was added

### Changed
- **FILE.md**: Description of what changed

### Fixed
- **FILE.md**: Description of what was fixed

### Removed
- **FILE.md**: Description of what was removed

### Archived
- `source_file.md` → `archive/destination.md`
```

---

## Related Documents

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Document navigation
- [DOCUMENTATION_CHANGE_PROCEDURE.md](DOCUMENTATION_CHANGE_PROCEDURE.md) - How to make changes
