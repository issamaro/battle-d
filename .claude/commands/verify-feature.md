# Verify Feature - Testing & Quality Assurance

**Phase:** 6 (Testing)

**Purpose:** Verify the implementation works correctly through comprehensive testing.

---

## Instructions for Claude

You are verifying the feature implementation. Follow these steps in order:

### Step 1: Run Existing Tests (Regression Check)

**CRITICAL:** Ensure no existing functionality broke.

```bash
pytest
```

**Expected:** All existing tests pass (no regressions)

**If tests fail:**
- Identify which tests failed
- Understand why they failed
- Determine if:
  - Test needs updating (behavior changed intentionally)
  - Code has bug (implementation error)
  - Test was already broken (pre-existing issue)
- Fix failures before proceeding

**Report to user:**
```
Test Results:
- Total: X tests
- Passed: Y tests
- Failed: Z tests
- Regressions: [list any tests that previously passed but now fail]
```

---

### Step 2: Verify New Tests Pass

**Run tests for new functionality:**

```bash
# Run service tests
pytest tests/test_*_service.py -v

# Run route tests
pytest tests/test_*_routes.py -v

# Run specific new tests
pytest tests/test_new_feature.py -v
```

**Expected:** All new tests pass

**If new tests fail:**
- Debug the implementation
- Fix bugs
- Re-run tests
- Don't proceed until all pass

---

### Step 2.5: Test-to-Requirement Mapping (BLOCKING for E2E Tests)

**Purpose:** Ensure tests validate the RIGHT behavior, not scope creep.

**2.5.1 Create Mapping Table**

Compare tests in `tests/e2e/` to Gherkin scenarios in `feature-spec.md`:

```markdown
## Test-to-Requirement Mapping

| Gherkin Scenario (feature-spec.md) | E2E Test(s) That Validate It | Status |
|-------------------------------------|------------------------------|--------|
| "View tournament command center" | test_command_center_shows_tournament | ✅ Covered |
| "Filter battles by encoding status" | test_filter_battles_by_pending | ✅ Covered |
| "See visual status indicators" | [NONE] | ⚠️ Missing test |
| [No scenario] | test_filter_sorted_by_name | 🚨 Scope creep? |
```

**2.5.2 Check for Issues**

**Missing Tests (⚠️):**
- Gherkin scenario exists but no E2E test validates it
- Action: Write the missing test OR ask user if test is needed

**Potential Scope Creep (🚨):**
- E2E test exists but doesn't map to any Gherkin scenario
- Action: Use **AskUserQuestion**:
  - "Test `test_X` doesn't map to any Gherkin scenario in feature-spec.md. Should I add this as a new requirement, or is this scope creep that should be removed?"

**2.5.3 Verify E2E Test Docstrings**

All E2E tests in `tests/e2e/` MUST have:
- `Validates:` line referencing the Gherkin scenario
- `Gherkin:` block with the actual Given/When/Then

**If docstring missing:**
- STOP and add the docstring
- If unclear which scenario the test validates, use **AskUserQuestion**

**2.5.4 When Test Fails - The Key Question**

When an E2E test fails, ask IN THIS ORDER:

1. **"Does this test correctly reflect the Gherkin scenario?"**
   - Read the test docstring
   - Compare to feature-spec.md Gherkin
   - If mismatch → test is wrong, fix the test

2. **"Is the requirement clear, or is it ambiguous?"**
   - If ambiguous → use **AskUserQuestion** to clarify with user
   - DO NOT assume an interpretation

3. **"Is this a bug in code OR a gap in requirements?"**
   - Only after confirming test is correct and requirement is clear
   - If code bug → fix the implementation
   - If requirement gap → update feature-spec.md first, then fix

**Document in test-results.md:**
```markdown
## Test-to-Requirement Mapping

**Mapping Status:** ✅ All scenarios covered / ⚠️ Issues found

| Scenario | Test | Status |
|----------|------|--------|
| View command center | test_command_center_shows_tournament | ✅ |
| Filter battles | test_filter_by_encoding_status | ✅ |

**Issues:**
- None / [List issues that needed resolution]

**Clarifications Asked:**
- None / [List any AskUserQuestion clarifications]
```

---

### Step 3: Browser Smoke Test (MANDATORY for UI changes)

**Skip condition:** ONLY skip if feature has ZERO UI changes (pure backend/tests/docs).

**Prerequisites:**
- Local dev running: `./scripts/dev.sh`
- Browser open at http://localhost:8000
- Logged in with test account (admin@battle-d.com)

**3.1 Feature Page Loads:**
- [ ] Navigate to the feature's primary page
- [ ] Verify page renders without errors
- [ ] Check: No 404, no 500, content displays correctly

**3.2 Primary Action Works:**
- [ ] Perform the main action (click button, submit form, etc.)
- [ ] Verify expected result occurs
- [ ] Check: Success message shows, data saved, redirect works

**3.3 Console Check:**
- [ ] Open browser DevTools (F12) > Console tab
- [ ] Verify: No red errors
- [ ] Note any warnings (optional to fix)

**3.4 Navigation Links (if templates modified):**
- [ ] Click all navigation links on the page
- [ ] Verify: No 404 errors
- [ ] Check: All links lead to correct pages

**Document in test-results.md:**
```markdown
## Browser Smoke Test

**Tested on:** localhost:8000
**Account used:** admin@battle-d.com

**Results:**
| Test | Status | Notes |
|------|--------|-------|
| Feature page loads | ✅ | Renders correctly |
| Primary action works | ✅ | Form submits, success message shows |
| Console errors | ✅ | No errors |
| Navigation links | ✅ | All sidebar links work |

**Issues found:** None / [describe if any]
```

---

### Step 3.5: Manual Testing Checklist (Methodology §6.6)

**Test happy path (everything works correctly):**
- [ ] Navigate to feature
- [ ] Perform primary action
- [ ] Verify expected outcome
- [ ] Check success message displays
- [ ] Verify data saved correctly

**Test error paths (validation errors, missing data):**
- [ ] Try invalid input
- [ ] Verify validation error displays
- [ ] Check error message is clear
- [ ] Verify form data preserved (not lost)
- [ ] Try missing required fields

**Test edge cases:**
- [ ] Empty states (no data in lists)
- [ ] Maximum values (large numbers, long text)
- [ ] Minimum values (zero, empty strings)
- [ ] Boundary conditions

**Test user workflow:**
- [ ] Complete full user journey
- [ ] Verify each step works
- [ ] Check navigation makes sense
- [ ] Verify user can complete task

**Document results:**
```markdown
## Manual Testing Results

### Happy Path: ✅ Pass
- [x] Action 1 worked as expected
- [x] Action 2 worked as expected
- [x] Success message displayed

### Error Paths: ✅ Pass
- [x] Invalid input rejected with clear error
- [x] Form data preserved on error
- [x] Required field validation works

### Edge Cases: ⚠️ Issues Found
- [x] Empty state displays correctly
- [ ] Issue: Maximum value causes overflow (needs fix)
- [x] Minimum value handled correctly

### User Workflow: ✅ Pass
- [x] Full journey completable
- [x] Navigation intuitive
```

---

### Step 4: Accessibility Testing (If UI Changes) (Methodology §6.3)

**ONLY if feature has UI changes. Skip if backend-only.**

**4.1 Keyboard Navigation**

Test with keyboard only (no mouse):
- [ ] Tab through all interactive elements
- [ ] Tab order is logical (follows visual order)
- [ ] Enter/Space activates buttons/links
- [ ] Escape closes modals/dialogs
- [ ] Arrow keys work in select/radio groups
- [ ] Focus visible on all elements
- [ ] No keyboard traps (can tab out of everything)

**Document issues:**
```markdown
### Keyboard Navigation: ⚠️ Issues Found
- [x] Tab order logical
- [ ] Issue: Modal close button not keyboard accessible
- [x] Focus indicators visible
```

**4.2 Screen Reader Testing**

Test with VoiceOver (macOS) or NVDA (Windows):
- [ ] All images have alt text
- [ ] Form fields have labels
- [ ] Error messages announced
- [ ] Status updates announced (aria-live)
- [ ] Headings logical hierarchy (h1, h2, h3)
- [ ] Links have descriptive text (not "click here")
- [ ] Buttons have clear labels

**Document issues:**
```markdown
### Screen Reader: ✅ Pass
- [x] All images have alt text
- [x] Form fields labeled correctly
- [x] Error messages announced
- [x] Status updates announced with aria-live
```

**4.3 ARIA Attributes**

Verify ARIA attributes correct:
- [ ] aria-label on icons/buttons without text
- [ ] aria-describedby links fields to error messages
- [ ] aria-invalid on fields with validation errors
- [ ] role="alert" on error messages
- [ ] aria-current on current page nav link
- [ ] aria-live on dynamic content updates

**Check with browser DevTools** → Accessibility tab

**4.4 Color Contrast**

Verify color contrast meets WCAG 2.1 AA:
- [ ] Text contrast ≥ 4.5:1
- [ ] UI component contrast ≥ 3:1
- [ ] Links distinguishable from text (not by color alone)

**Check with browser DevTools** → Accessibility → Contrast

**Document issues:**
```markdown
### Color Contrast: ⚠️ Issues Found
- [x] Body text meets 4.5:1 (passes)
- [ ] Issue: Orange badge only 3.2:1 (needs darker shade)
- [x] Button contrast meets 3:1
```

**4.5 Focus Indicators**

Verify focus visible:
- [ ] Focus ring visible on all interactive elements
- [ ] Focus not removed with CSS (outline: none without replacement)
- [ ] Focus ring high contrast
- [ ] Focus order matches visual order

---

### Step 5: Responsive Testing (If UI Changes) (Methodology §6.4)

**ONLY if feature has UI changes. Skip if backend-only.**

**Test on different viewport sizes:**

**5.1 Mobile (320px-768px)**

Use Chrome DevTools → Responsive Design Mode → 375px width

- [ ] Content stacks vertically
- [ ] Buttons full-width or properly sized
- [ ] Text readable (min 16px)
- [ ] Touch targets ≥ 44x44px
- [ ] Sidebar collapses or becomes top nav
- [ ] Tables scroll horizontally or transform
- [ ] Images scale appropriately
- [ ] No horizontal scrolling

**Document issues:**
```markdown
### Mobile (375px): ⚠️ Issues Found
- [x] Content stacks correctly
- [ ] Issue: Touch target for filter chips only 40px (needs 44px)
- [x] Text readable
- [x] No horizontal scroll
```

**5.2 Tablet (769px-1024px)**

Use Chrome DevTools → 768px width

- [ ] 2-column layouts work
- [ ] Sidebar visible or easily accessible
- [ ] Forms use optimal width (max 600px)
- [ ] Images and media scale correctly
- [ ] Touch targets adequate

**5.3 Desktop (1025px+)**

Use Chrome DevTools → 1440px width

- [ ] Multi-column layouts work
- [ ] Sidebar navigation visible
- [ ] Content doesn't stretch too wide (max-width used)
- [ ] Proper use of whitespace
- [ ] Images don't pixelate

**Document results:**
```markdown
### Responsive Testing: ✅ Pass
- [x] Mobile (375px): All criteria met
- [x] Tablet (768px): 2-column layout works
- [x] Desktop (1440px): Content max-width applied
```

---

### Step 6: HTMX Interaction Testing (If Using HTMX) (Methodology §6.6)

**ONLY if feature uses HTMX. Skip if not applicable.**

**6.1 Verify HTMX Patterns Work**

**Live search/filtering:**
- [ ] Debounce working (no request on every keystroke)
- [ ] Results update correctly
- [ ] hx-target updates correct element
- [ ] Loading indicator shows (if implemented)

**Form submission:**
- [ ] Partial update works (only target element changes)
- [ ] Error state handled (form stays visible with errors)
- [ ] Success state handled (flash message or redirect)
- [ ] Form data preserved on error

**Polling/auto-refresh:**
- [ ] Updates happen at correct interval
- [ ] No memory leaks (check browser DevTools → Memory)
- [ ] Stops when page not visible (if configured)

**URL state preservation:**
- [ ] URL updates with hx-push-url
- [ ] Browser back button works
- [ ] Shareable URLs work (can paste URL to get same state)

**6.2 Check Network Requests**

Open browser DevTools → Network tab:
- [ ] Correct endpoints called
- [ ] Request headers include HX-Request: true
- [ ] Response is partial HTML (not full page)
- [ ] No unnecessary requests (debouncing works)

**Document results:**
```markdown
### HTMX Testing: ✅ Pass
- [x] Live filtering debounces correctly (500ms)
- [x] Partial updates work (only #battle-list changes)
- [x] URL state preserved with hx-push-url
- [x] Network requests efficient (no duplicates)
```

---

### Step 7: Coverage Check (Methodology §6.7)

**Run coverage report:**

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

**Review coverage:**
- Overall coverage: X%
- New code coverage: Y%

**Coverage targets:**
- Overall: ≥ 90%
- Critical paths: 100% (authentication, validation, data integrity)
- New feature code: ≥ 95%

**Review uncovered lines:**
- Are they error handling that's hard to trigger?
- Are they truly unreachable code?
- Should we add tests to cover critical paths?

**Document results:**
```markdown
### Coverage Report:
- Overall: 92% (target ≥90%) ✅
- New feature code: 96% (target ≥95%) ✅
- Critical paths: 100% ✅

Uncovered lines:
- app/services/example.py:45 - Error handling for rare DB failure (acceptable)
```

---

### Step 8: Browser Console Check

**Open browser DevTools → Console:**

**Navigate through feature and check for:**
- [ ] No JavaScript errors
- [ ] No HTMX errors
- [ ] No 404s (missing assets)
- [ ] No CORS errors
- [ ] No deprecation warnings

**Document issues:**
```markdown
### Console Check: ⚠️ Issues Found
- [ ] Issue: 404 for /static/css/missing.css (needs fix)
- [x] No JavaScript errors
- [x] No HTMX errors
```

---

### Step 9: Create Testing Summary Document

Create: `workbench/TEST_RESULTS_YYYY-MM-DD_[FEATURE-NAME].md`

```markdown
# Test Results: [Feature Name]

**Date:** YYYY-MM-DD
**Tested By:** Claude
**Status:** ✅ Pass / ⚠️ Pass with Issues / ❌ Fail

---

## 1. Automated Tests

### Unit Tests
- Total: X tests
- Passed: Y tests
- Failed: Z tests
- Status: ✅ Pass

### Integration Tests
- Total: X tests
- Passed: Y tests
- Failed: Z tests
- Status: ✅ Pass

### Coverage
- Overall: X% (target ≥90%)
- New code: Y% (target ≥95%)
- Critical paths: 100%
- Status: ✅ Meets targets

---

## 2. Manual Testing

### Happy Path: ✅ Pass
- [x] Primary workflow works
- [x] Data saves correctly
- [x] Success messages display

### Error Paths: ✅ Pass
- [x] Validation errors clear
- [x] Form data preserved
- [x] Edge cases handled

---

## 3. Accessibility Testing

### Keyboard Navigation: ✅ Pass
- [x] Tab order logical
- [x] All interactive elements accessible
- [x] Focus indicators visible

### Screen Reader: ✅ Pass
- [x] Labels correct
- [x] Errors announced
- [x] Status updates announced

### ARIA Attributes: ✅ Pass
- [x] aria-label where needed
- [x] aria-invalid on errors
- [x] aria-live on updates

### Color Contrast: ⚠️ Issues Found
- [x] Text contrast ≥4.5:1
- [ ] **Issue:** Orange badge contrast 3.2:1 (needs ≥3:1)
- [x] UI components ≥3:1

---

## 4. Responsive Testing

### Mobile (375px): ✅ Pass
- [x] Content stacks correctly
- [x] Touch targets ≥44x44px
- [x] No horizontal scroll

### Tablet (768px): ✅ Pass
- [x] 2-column layout works
- [x] Navigation accessible

### Desktop (1440px): ✅ Pass
- [x] Multi-column layout
- [x] Content max-width applied

---

## 5. HTMX Testing

### Interactions: ✅ Pass
- [x] Live filtering works
- [x] Debouncing correct
- [x] Partial updates work
- [x] URL state preserved

### Network: ✅ Pass
- [x] Correct endpoints called
- [x] Partial HTML returned
- [x] No unnecessary requests

---

## 6. Browser Console

### Checks: ⚠️ Issues Found
- [x] No JavaScript errors
- [x] No HTMX errors
- [ ] **Issue:** 404 for /static/css/old-file.css
- [x] No CORS errors

---

## 7. Issues Found

### Critical (Must Fix Before Deploy):
None

### Important (Should Fix Soon):
1. **Orange badge contrast too low (3.2:1)**
   - Location: app/static/css/battles.css
   - Fix: Use darker orange (#e65100 instead of #ff9800)

2. **404 for removed CSS file**
   - Location: app/templates/base.html references old-file.css
   - Fix: Remove reference from template

### Minor (Can Fix Later):
None

---

## 8. Regression Testing

### Existing Features: ✅ No Regressions
- [x] All 171 existing tests still pass
- [x] No previously working features broken
- [x] No performance degradation observed

---

## 9. Overall Assessment

**Status:** ⚠️ Pass with Issues

**Summary:**
Feature works correctly and meets requirements. Found 2 important issues that should be fixed before deployment (color contrast, 404 error). No critical issues. No regressions detected.

**Recommendation:**
Fix the 2 important issues, then ready for deployment.

---

## 10. Next Steps

- [ ] Fix orange badge color contrast
- [ ] Remove 404 CSS reference
- [ ] Re-run affected tests
- [ ] User acceptance testing
- [ ] Ready for `/close-feature`
```

---

## Quality Gate (BLOCKING)

**Before marking this command complete, verify:**

**Automated Testing:**
- [ ] All existing tests pass (no regressions)
- [ ] All new tests pass
- [ ] Coverage meets targets (≥90% overall, ≥95% new code)

**Service Integration Testing (CRITICAL):**
- [ ] Service integration tests exist for new service methods
- [ ] Integration tests use REAL repositories (NOT mocks)
- [ ] Integration tests use REAL enum values (catches invalid references)
- [ ] Integration tests verify actual database state after operations
- [ ] No over-mocking that hides bugs (see TESTING.md for patterns)

**Test-to-Requirement Traceability (BLOCKING for E2E):**
- [ ] Test-to-requirement mapping table created
- [ ] All Gherkin scenarios from feature-spec.md have corresponding E2E tests
- [ ] All E2E tests have `Validates:` docstring referencing Gherkin scenario
- [ ] No E2E tests exist without corresponding Gherkin scenario (scope creep check)
- [ ] Any discrepancies resolved via AskUserQuestion

**Browser Verification (MANDATORY for UI changes):**
- [ ] Local dev running (`./scripts/dev.sh`)
- [ ] Feature page loads without errors
- [ ] Primary action works correctly
- [ ] No console errors in browser DevTools
- [ ] Navigation links work (if templates modified)
- [ ] Results documented in test-results.md
- [ ] (Skip if: pure backend/tests/docs with ZERO UI changes)

**Manual Testing:**
- [ ] Happy path tested and works
- [ ] Error paths tested and work
- [ ] Edge cases tested
- [ ] User workflow completable

**Accessibility (if UI changes):**
- [ ] Keyboard navigation works
- [ ] Screen reader tested
- [ ] ARIA attributes correct
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] Focus indicators visible

**Responsive (if UI changes):**
- [ ] Mobile tested (320px-768px)
- [ ] Tablet tested (769px-1024px)
- [ ] Desktop tested (1025px+)

**HTMX (if applicable):**
- [ ] HTMX interactions work
- [ ] Network requests correct
- [ ] No errors in console

**Quality Checks:**
- [ ] No console errors
- [ ] No 404s for assets
- [ ] No regressions detected

**Documentation:**
- [ ] Test results document created
- [ ] Issues documented with severity
- [ ] Recommendations provided

**If any critical issues found, STOP and fix before proceeding.**

---

## Next Steps

After this command completes:
1. User reviews test results
2. User performs acceptance testing
3. Fix any issues found
4. Re-run tests if fixes made
5. When all tests pass and user approves, run `/close-feature`

---

**Remember:** Testing is about finding issues, not proving code works. Document everything. Be thorough. Fix critical issues before deployment.
