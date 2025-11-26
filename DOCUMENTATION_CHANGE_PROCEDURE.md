# Documentation Change Procedure
**Level 3: Operational** | Last Updated: 2025-11-24

**Purpose:** Standard procedure for modifying project documentation, designed for both human contributors and AI agents.

---

## Overview

This procedure ensures documentation changes are:
- **Consistent** across all documents
- **Traceable** through workbench files
- **Verified** before completion
- **Archived** for historical reference

---

## Step 1: Create Workbench File

**Before ANY documentation change, create a workbench file:**

```bash
# Create workbench directory if it doesn't exist
mkdir -p workbench

# Create workbench file with date and topic
# Format: workbench/CHANGE_YYYY-MM-DD_TOPIC.md
```

**Workbench File Template:**

```markdown
# Change: [Brief Description]

**Created:** YYYY-MM-DD
**Status:** In Progress
**Author:** [Name or "AI Agent"]

## What's Changing
- [List changes to be made]

## Why
- [Reason for changes]

## Affected Files
- [ ] file1.md (line X-Y)
- [ ] file2.md (line X-Y)

## Progress
- [ ] Step 1: ...
- [ ] Step 2: ...

## Verification
- [ ] Grep check passed
- [ ] Cross-references updated

## Notes
[Any relevant notes or decisions]
```

---

## Step 2: Identify Scope

**Find all occurrences of the concept being changed:**

```bash
# Search all markdown files for the term
grep -rn "term_to_change" *.md

# Search with case insensitive
grep -rni "term" *.md

# Search for related patterns
grep -rn "related_pattern\|another_pattern" *.md
```

**Document all affected files in the workbench file.**

---

## Step 3: Update in Order

**Follow the document hierarchy:**

### Order of Updates:

1. **Level 1 First (Source of Truth)**
   - DOMAIN_MODEL.md
   - VALIDATION_RULES.md

2. **Level 2 Second (Derived)**
   - UI_MOCKUPS.md
   - ROADMAP.md
   - README.md

3. **Level 3 Last (Operational)**
   - ARCHITECTURE.md
   - TESTING.md
   - DEPLOYMENT.md

4. **Level 0 (Meta) - If Needed**
   - GLOSSARY.md (if new terms)
   - DOCUMENTATION_INDEX.md (if new cross-references)
   - CHANGELOG.md (always, after changes)

### Why This Order?

- Level 1 docs define the "truth"
- Level 2 docs reference Level 1
- Updating Level 1 first ensures derived docs reference correct info

---

## Step 4: Make Changes

**For each file:**

1. Read the relevant section first
2. Make the edit
3. Check surrounding context for consistency
4. Update "Last Updated" timestamp if present
5. Mark as complete in workbench file

**Best Practices:**

- Change one concept at a time
- Keep edits atomic (easy to review)
- Maintain consistent formatting
- Update cross-references if links change

---

## Step 5: Verify Consistency

**Run verification checks:**

```bash
# Verify no old values remain
grep -rn "old_value" *.md

# Should return: No matches found

# Verify new value is in expected locations
grep -rn "new_value" *.md

# Should show all expected files
```

**Document verification results in workbench file.**

---

## Step 6: Update CHANGELOG.md

**Add entry for the change:**

```markdown
## [YYYY-MM-DD] - Phase X.X: Brief Description

### Changed
- DOMAIN_MODEL.md: Description of change
- VALIDATION_RULES.md: Description of change

### Added
- New section in FILE.md

### Removed
- Removed deprecated section from FILE.md

### Fixed
- Corrected inconsistency in FILE.md
```

---

## Step 7: Archive Workbench File

**After changes are verified and approved:**

1. Update workbench file status to "Complete"
2. Move to archive folder:

```bash
mv workbench/CHANGE_2025-11-22_topic.md archive/
```

3. Delete workbench file only if archived

**Archive Naming Convention:**
- Keep original filename
- Archive preserves full change history

---

## Quick Reference Checklist

```markdown
## Pre-Change
- [ ] Created workbench file
- [ ] Ran grep to find all occurrences
- [ ] Listed all affected files

## During Change
- [ ] Updated Level 1 docs first
- [ ] Updated Level 2 docs second
- [ ] Updated Level 3 docs last
- [ ] Updated cross-references

## Post-Change
- [ ] Verified no old values remain (grep)
- [ ] Verified new values in expected places
- [ ] Updated CHANGELOG.md
- [ ] Marked workbench as complete
- [ ] Archived workbench file
```

---

## For AI Agents

**Special Instructions:**

1. **Always create workbench file first** - This ensures the plan is preserved even if the session is interrupted

2. **Use TodoWrite tool** - Track progress in todos as you complete each step

3. **Report verification results** - Show grep output to confirm consistency

4. **Ask for approval** - Before archiving, confirm changes are acceptable

5. **Handle interruptions** - If session ends mid-change, workbench file preserves state for next session

---

## Common Scenarios

### Scenario: Changing a Validation Rule

1. Update VALIDATION_RULES.md (source of truth)
2. Update DOMAIN_MODEL.md if business rule affected
3. Update UI_MOCKUPS.md validation messages
4. Verify with grep
5. Update CHANGELOG.md

### Scenario: Adding New Entity Field

1. Update DOMAIN_MODEL.md (add field to entity)
2. Update VALIDATION_RULES.md (add constraints)
3. Update UI_MOCKUPS.md (add to forms/displays)
4. Verify with grep
5. Update CHANGELOG.md

### Scenario: Fixing Inconsistency

1. Identify correct value (usually in Level 1 docs)
2. Update all locations with incorrect value
3. Verify no incorrect values remain
4. Update CHANGELOG.md

---

## Related Documents

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Document hierarchy and cross-references
- [GLOSSARY.md](GLOSSARY.md) - Term definitions
- [CHANGELOG.md](CHANGELOG.md) - Change history
