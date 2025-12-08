# Workbench: Slash Command Methodology Improvement

**Date:** 2025-12-08
**Author:** Claude
**Status:** In Progress

---

## Purpose

Improve slash command methodology to catch bugs before production by:
1. Creating one-command local dev setup (`scripts/dev.sh`)
2. Adding pattern scan step to `/analyze-feature`
3. Adding technical POC step to `/plan-implementation`
4. Making browser smoke test MANDATORY in `/verify-feature`
5. Adding cross-feature impact check to `/close-feature`

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- N/A - No entity changes

**VALIDATION_RULES.md:**
- N/A - No validation rule changes

### Level 2: Derived
**ROADMAP.md:**
- N/A - This is methodology improvement, not a feature phase

**README.md:**
- [x] Update Quick Start section to use `./scripts/dev.sh`

### Level 3: Operational
**ARCHITECTURE.md:**
- N/A - No new backend patterns

**FRONTEND.md:**
- N/A - No new UI components

**TESTING.md:**
- N/A - No new test patterns

---

## Slash Command Updates

| Command | Change |
|---------|--------|
| `/analyze-feature.md` | Add Step 1.4.5: Pattern Scan |
| `/plan-implementation.md` | Add Step 3.5: Technical Risk POC |
| `/verify-feature.md` | Update Step 3: Browser Smoke Test (MANDATORY) |
| `/close-feature.md` | Add Step 1.5: Cross-Feature Impact Check |

---

## Verification

**Grep checks performed:**
```bash
grep -r "Pattern Scan" .claude/commands/
grep -r "Technical POC" .claude/commands/
grep -r "Browser Smoke Test" .claude/commands/
grep -r "Cross-Feature Impact" .claude/commands/
```

**Results:**
- ✅ "Pattern Scan" found in: analyze-feature.md
- ✅ "Technical POC" found in: plan-implementation.md
- ✅ "Browser Smoke Test" found in: verify-feature.md
- ✅ "Cross-Feature Impact" found in: close-feature.md
- ✅ All new sections added to correct files
- ✅ Quality gates updated in all 4 commands

---

## Files Modified

**New Files:**
- scripts/dev.sh - One-command local dev setup (executable)

**Documentation:**
- README.md - Updated Quick Start section to use ./scripts/dev.sh
- .claude/commands/analyze-feature.md - Added Step 1.4.5: Pattern Scan + Quality Gate
- .claude/commands/plan-implementation.md - Added Step 3.5: Technical Risk POC + Quality Gate
- .claude/commands/verify-feature.md - Added Step 3: Browser Smoke Test (MANDATORY) + Quality Gate
- .claude/commands/close-feature.md - Added Step 1.5: Cross-Feature Impact Check + Quality Gate

---

## Notes

- `scripts/dev.sh` leverages existing `seed_db.py` for test account creation
- Cross-platform sed handling for macOS vs Linux in dev.sh
- All changes are documentation/tooling only - no runtime code changes
- No tests required for this feature (methodology changes only)
