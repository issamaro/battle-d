# Workbench: Test-to-Requirement Traceability

**Date:** 2025-12-09
**Author:** Claude
**Status:** Complete

---

## Purpose

Add test-to-requirement traceability to the methodology to ensure tests validate correct functional behavior (not scope creep or incorrect implementations).

When an E2E test fails, the developer should be able to determine:
1. Is the test correctly reflecting the Gherkin requirement?
2. Is the requirement clear, or does it need user clarification?
3. Is the failure a code bug or a requirement gap?

---

## Documentation Changes

### Level 1: Source of Truth
**DOMAIN_MODEL.md:**
- No changes (not domain rules)

**VALIDATION_RULES.md:**
- No changes (not validation rules)

### Level 2: Derived
**ROADMAP.md:**
- No changes (methodology improvement, not feature)

### Level 3: Operational

**.claude/commands/implement-feature.md:**
- [x] Added "13.0 Requirement Validation" section before writing tests
- [x] Added "13.4 E2E Tests - MUST Reference Gherkin" section (BLOCKING)
- [x] Added "When E2E test fails, Claude MUST ask" guidance

**.claude/commands/verify-feature.md:**
- [x] Added "Step 2.5: Test-to-Requirement Mapping" section
- [x] Added test-requirement mapping table template
- [x] Added Quality Gate checkbox for traceability

**.claude/README.md:**
- [x] Added "PART 6: TEST-TO-REQUIREMENT TRACEABILITY" to Table of Contents
- [x] Added complete "Test-to-Requirement Traceability" section

**TESTING.md:**
- [x] Added "E2E Test Docstring Standard (BLOCKING)" section
- [x] Updated example test to show required docstring format
- [x] Added "When E2E test fails, Claude MUST ask" guidance

---

## Verification

**Changes verified in:**
- `.claude/commands/implement-feature.md` - Lines 679-835 (new sections added)
- `.claude/commands/verify-feature.md` - Lines 68-143, 674-679 (new step and quality gate)
- `.claude/README.md` - Lines 51-52, 2992-3095 (new section)
- `TESTING.md` - Lines 583-629 (new standard)

---

## Files Modified

**Methodology:**
- .claude/commands/implement-feature.md
- .claude/commands/verify-feature.md
- .claude/README.md
- TESTING.md

**Feature Spec:**
- workbench/FEATURE_SPEC_2025-12-09_TEST-REQUIREMENT-TRACEABILITY.md

---

## Summary of Changes

### 1. Requirement Validation Before Writing Tests (implement-feature.md)
Before writing any test, Claude must ask:
- Which Gherkin scenario does this validate?
- Is the expected outcome clear?
- Am I adding behavior not in the spec?

### 2. E2E Test Docstring Standard (implement-feature.md, TESTING.md)
All E2E tests MUST include:
```python
"""Test description.

Validates: feature-spec.md Scenario "Scenario Name"
Gherkin:
    Given [context]
    When [action]
    Then [expected outcome]
"""
```

### 3. Test-to-Requirement Mapping (verify-feature.md)
During verification, create mapping table:
- Match each Gherkin scenario to its E2E test(s)
- Flag missing tests (⚠️)
- Flag tests without scenarios (🚨 scope creep)

### 4. When Test Fails Protocol (all files)
When E2E test fails, ask IN ORDER:
1. Does test correctly reflect Gherkin? (if not → fix test)
2. Is requirement clear? (if not → AskUserQuestion)
3. Is it code bug or requirement gap? (fix accordingly)

---

## Strictness Levels

| Test Type | Gherkin Reference | Enforcement |
|-----------|-------------------|-------------|
| E2E tests (`tests/e2e/`) | REQUIRED | BLOCKING |
| Integration tests | RECOMMENDED | Guideline |
| Unit tests | OPTIONAL | Guideline |
