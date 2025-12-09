# Feature Specification: Test-to-Requirement Traceability

**Date:** 2025-12-09
**Status:** Awaiting User Validation

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Current State Analysis](#3-current-state-analysis)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Implementation Recommendations](#5-implementation-recommendations)
6. [Appendix: Reference Material](#6-appendix-reference-material)

---

## 1. Problem Statement

Tests might validate wrong functional behavior or scope creep because there's no explicit link between test assertions and documented requirements. When a test fails, it's not clear whether the failure indicates a bug in implementation OR an undocumented/incorrect requirement that needs clarification.

---

## 2. Executive Summary

### Scope
Analysis of the current methodology to identify gaps in ensuring tests validate correct functional behavior vs scope creep.

### What Works ✅

| Aspect | Status | Evidence |
|--------|--------|----------|
| BDD Gherkin scenarios in `/analyze-feature` | Good | Clear Given/When/Then format in feature specs |
| Integration tests over mocked tests | Enforced | TESTING.md §Service Integration Tests (PRIMARY) |
| Test coverage tracking | Good | Coverage targets defined (≥90% overall) |
| Documentation-first approach | Enforced | `/implement-feature` requires docs before code |
| Quality gates at each phase | Good | Blocking checklists in all slash commands |

### What's Missing 🚨

| Gap | Type | Impact |
|-----|------|--------|
| No explicit link from test to requirement | PROCESS GAP | Tests can pass but validate wrong behavior |
| No requirement reference in test code | PROCESS GAP | Hard to trace why a test exists |
| No "is this requirement correct?" question prompt | PROCESS GAP | Claude might implement without validating |
| No test review against requirements | PROCESS GAP | Tests never compared to BDD scenarios |
| Manual test checklist not linked to Gherkin | PROCESS GAP | Parallel validation systems |

### Key Gap Identified

**The current workflow:**
```
/analyze-feature → Gherkin scenarios (feature-spec.md)
/plan-implementation → Technical plan (implementation-plan.md)
/implement-feature → Write code + tests
/verify-feature → Run tests, manual testing
/close-feature → Archive everything
```

**Missing step:** At no point does the methodology require:
1. Tests to reference specific Gherkin scenarios
2. Claude to question "wait, is this test validating the right thing?"
3. Test assertions to be compared against acceptance criteria

---

## 3. Current State Analysis

### 3.1 What `/analyze-feature` Does Well

The command creates BDD scenarios with explicit acceptance criteria:

```gherkin
Scenario: Filter battles by encoding status
  Given I am on the battles list page
  And there are 50 battles in various states
  When I click the "Pending Encoding" filter
  Then I see only battles with status COMPLETED that have no outcome encoded
  And the battle count shows "12 pending encoding"
  And the list is sorted by completion time (oldest first)
```

**This is the source of truth for functional requirements.**

### 3.2 What `/implement-feature` Does

From `implement-feature.md:679-762`:
- "Write tests AS YOU IMPLEMENT, not after"
- Service integration tests pattern documented
- BUT: No instruction to reference Gherkin scenarios in tests
- BUT: No instruction to verify test validates requirement

### 3.3 What `/verify-feature` Does

From `verify-feature.md:117-167`:
- Manual testing checklist exists
- BUT: Checklist is generic, not tied to feature-spec Gherkin scenarios
- No comparison: "Does test X validate Gherkin scenario Y?"

### 3.4 The Risk Scenario

**What could go wrong:**

1. **Scope Creep in Tests:**
   - Claude writes test: `test_filter_returns_battles_sorted_by_name()`
   - But Gherkin says: "sorted by completion time (oldest first)"
   - Test passes, but validates WRONG behavior

2. **Missing Requirement:**
   - Claude implements filter without count indicator
   - No test for "battle count shows '12 pending encoding'"
   - Feature ships incomplete

3. **Incorrect Understanding:**
   - Claude interprets "pending encoding" as `status=PENDING`
   - But Gherkin says: "status COMPLETED that have no outcome encoded"
   - Test validates wrong logic

### 3.5 Evidence from TESTING.md

From `TESTING.md:139-156`:
```
Service integration tests verify that services work correctly with REAL repositories...
Unlike mocked unit tests, integration tests catch bugs like:
- Invalid enum references
- Repository method signature mismatches
- Lazy loading and relationship issues
```

**This catches TECHNICAL bugs, but not FUNCTIONAL specification bugs.**

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Rule: Test-to-Requirement Traceability

**Business Rule BR-TEST-001: Every Test Must Reference a Requirement**
> Tests should include a reference to the Gherkin scenario or acceptance criterion they validate, so that when a test fails, we know whether it's a bug (implementation wrong) or a requirement gap (spec needs clarification).

**Acceptance Criteria:**
```gherkin
Feature: Test-to-Requirement Traceability
  As a developer (Claude)
  I want to trace tests back to documented requirements
  So that failing tests prompt the right question: "Is implementation wrong OR is requirement unclear?"

Scenario: Test includes requirement reference
  Given I am writing a test for a feature
  When I create the test function
  Then the docstring includes which Gherkin scenario it validates
  And the docstring includes the requirement ID or feature-spec location

Scenario: Test failure triggers requirement check
  Given a test is failing
  When I investigate the failure
  Then I first check if the test correctly reflects the requirement
  And I ask "Is this testing the right thing?" before assuming code is wrong
  And I escalate to user if requirement seems ambiguous or incorrect

Scenario: Verify-feature checks test-requirement alignment
  Given I am running /verify-feature
  When I review test results
  Then I verify each test maps to a Gherkin scenario from feature-spec
  And I flag any tests that don't have clear requirement mapping
```

### 4.2 Rule: Requirement Validation Before Implementation

**Business Rule BR-TEST-002: Validate Requirements Before Testing**
> Before writing tests, Claude should verify that the requirements being tested are correctly understood and documented, asking for clarification if ambiguous.

**Acceptance Criteria:**
```gherkin
Scenario: Claude questions ambiguous requirements
  Given I am about to write a test
  When the Gherkin scenario has ambiguous outcomes
  Then I use AskUserQuestion to clarify before proceeding
  And I do NOT assume an interpretation

Scenario: Test reveals undocumented requirement
  Given I am writing a test
  When I realize there's behavior not covered by Gherkin
  Then I flag this as a potential scope creep
  And I ask user: "Should I add this requirement or is it out of scope?"
```

### 4.3 Rule: Cross-Reference at Verification

**Business Rule BR-TEST-003: Verify Tests Against Requirements**
> During `/verify-feature`, explicitly compare test coverage to Gherkin scenarios to ensure all requirements are tested and no extra behavior is tested.

**Acceptance Criteria:**
```gherkin
Scenario: Verify-feature includes requirement coverage check
  Given I am running /verify-feature
  When I complete automated testing
  Then I create a mapping table: Gherkin Scenario → Test(s) that validate it
  And I flag scenarios without corresponding tests
  And I flag tests without corresponding scenarios
```

---

## 5. Implementation Recommendations

### 5.1 Critical (Before Next Feature)

1. **Add Test Docstring Standard to `/implement-feature`**

   Location: `.claude/commands/implement-feature.md`

   Add to Step 13 (Write Tests):
   ```markdown
   **13.0 Test Docstring Standard (REQUIRED)**

   Every test function MUST include:
   - Which Gherkin scenario it validates (from feature-spec.md)
   - What requirement it tests

   Example:
   ```python
   @pytest.mark.asyncio
   async def test_filter_battles_by_pending_encoding(async_session_maker):
       """Test filter battles by encoding status returns only unencoded battles.

       Validates: feature-spec.md Scenario "Filter battles by encoding status"
       Requirement: "Then I see only battles with status COMPLETED that have no outcome encoded"
       """
       # Test implementation...
   ```

2. **Add Requirement Validation Check to `/verify-feature`**

   Location: `.claude/commands/verify-feature.md`

   Add new Step 2.5 after running tests:
   ```markdown
   ### Step 2.5: Test-to-Requirement Mapping

   **Create mapping table comparing tests to requirements:**

   | Gherkin Scenario (feature-spec.md) | Test(s) That Validate It | Status |
   |-------------------------------------|--------------------------|--------|
   | Filter battles by encoding status | test_filter_battles_by_pending | ✅ Covered |
   | See visual status indicators | test_status_badges_display | ✅ Covered |
   | Quick access to encoding form | [NONE] | ⚠️ Missing test |

   **Flag issues:**
   - Missing tests for documented requirements
   - Tests that don't map to any documented requirement (scope creep?)

   **If discrepancy found:**
   - Use AskUserQuestion: "Test X doesn't map to any Gherkin scenario. Should I add requirement or remove test?"
   ```

3. **Add "Question the Requirement" Prompt**

   Location: `.claude/commands/implement-feature.md`

   Add to Step 13 before writing tests:
   ```markdown
   **Before writing each test, ask yourself:**
   1. Which Gherkin scenario does this test validate?
   2. Is the expected outcome clear in the requirement?
   3. Am I adding behavior not in the spec? (If yes, STOP and ask user)

   **If a test feels "made up" (not from Gherkin), use AskUserQuestion:**
   - "I'm about to write test X, but I don't see this in the Gherkin scenarios. Should I add this requirement or is it out of scope?"
   ```

### 5.2 Recommended (Improve Process)

1. **Add Requirement ID System**

   In feature-spec.md Gherkin scenarios, add IDs:
   ```gherkin
   Scenario: REQ-BATTLE-001 - Filter battles by encoding status
     Given...
   ```

   Then reference in tests:
   ```python
   """Validates: REQ-BATTLE-001"""
   ```

2. **Add Test Coverage Report to `/close-feature`**

   Location: `.claude/commands/close-feature.md`

   In closure summary, add:
   ```markdown
   ## Requirement Coverage

   | Requirement | Test | Status |
   |-------------|------|--------|
   | REQ-BATTLE-001 | test_filter_battles | ✅ |
   | REQ-BATTLE-002 | test_status_badges | ✅ |
   | [All accounted for] | | |
   ```

### 5.3 Nice-to-Have (Future)

1. **Automated Gherkin-to-Test Parsing**
   - Parse feature-spec.md for Gherkin scenarios
   - Parse test docstrings for "Validates:" references
   - Auto-generate coverage report

2. **Pre-commit Hook for Test Docstrings**
   - Warn if test function lacks "Validates:" in docstring

---

## 6. Appendix: Reference Material

### 6.1 Open Questions for User

- **Q:** Do you want a formal requirement ID system (REQ-XXX-NNN) or is referencing the scenario name sufficient?
- **Q:** Should the test-to-requirement mapping be BLOCKING (must fix before close) or WARNING (document and decide)?
- **Q:** How strict should "no test without requirement" be? Some tests (edge cases, error handling) may not have explicit Gherkin scenarios.

### 6.2 Files That Would Be Modified

1. `.claude/commands/implement-feature.md` - Add test docstring standard
2. `.claude/commands/verify-feature.md` - Add test-to-requirement mapping step
3. `.claude/README.md` - Add methodology section on traceability
4. `TESTING.md` - Add "Test Docstring Standard" section

### 6.3 User Confirmation Needed

- [ ] User confirms problem statement is accurate
- [ ] User validates acceptance criteria match their vision
- [ ] User approves recommended changes
- [ ] User answers open questions

---

**Summary:** The methodology is solid for technical quality but lacks explicit traceability from tests to requirements. Adding three changes (test docstring standard, verification mapping step, and "question the requirement" prompt) would ensure Claude asks "Is this test validating the right thing?" rather than assuming implementation is wrong when tests fail.
