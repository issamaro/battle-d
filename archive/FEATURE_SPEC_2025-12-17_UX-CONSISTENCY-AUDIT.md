# Feature Specification: UX Consistency Audit & Automated Testing

**Date:** 2025-12-17
**Status:** Awaiting User Approval

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [User Flow Diagram](#3-user-flow-diagram)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

Since Phase 3.3 (UX Navigation Redesign), the Battle-D application has accumulated UX inconsistencies where new UI patterns were added alongside legacy patterns instead of replacing them. This "Frankenstein" effect includes orphaned templates, inconsistent styling patterns, and no automated testing to catch UX regressions.

**Three interconnected problems:**

1. **Orphaned Legacy Code:** Templates like `overview.html` (root level) exist but are no longer used, causing confusion during development.

2. **Inconsistent Visual Patterns:** Mixed use of PicoCSS classes vs inline styles, inconsistent button styling, and varying permission display formats (`Yes/No` vs `checkmark/x`).

3. **No UX Regression Testing:** Current E2E tests verify routes return 200 OK but don't verify:
   - All buttons link to functional endpoints
   - Templates follow FRONTEND.md patterns
   - Orphaned code doesn't accumulate

---

## 2. Executive Summary

### Scope

Full audit of all HTML templates against FRONTEND.md patterns, cleanup of orphaned code, and creation of automated E2E tests to prevent future UX regressions.

### What Works

| Feature | Status | Notes |
|---------|--------|-------|
| Dashboard (3-state) | Production Ready | Correctly uses `dashboard/index.html` |
| Event Mode | Production Ready | Full-screen command center works |
| Registration (2-panel) | Production Ready | HTMX updates working |
| Navigation context | Production Ready | Active tournament auto-populated |
| Template organization | Good | 51/52 templates actively used |

### What's Broken

| Issue | Type | Location |
|-------|------|----------|
| `overview.html` (root) orphaned | DEAD CODE | `app/templates/overview.html` |
| `pools/overview.html` orphaned | DEAD CODE | `app/templates/pools/overview.html` |
| Inline styles in tournament detail | INCONSISTENCY | `tournaments/detail.html:14-47` |
| Inline button styles in dancers list | INCONSISTENCY | `dancers/list.html:32` |
| Permission display varies (Yes/No vs checkmark) | INCONSISTENCY | Multiple files |
| No automated UX consistency tests | GAP | `tests/e2e/` lacks coverage |

### Key Business Rules Defined

- **BR-UX-001:** All templates must follow FRONTEND.md patterns (no inline styles)
- **BR-UX-002:** All href/action attributes must point to existing routes
- **BR-UX-003:** No orphaned templates should exist in codebase
- **BR-UX-004:** Permissions display must use consistent format

---

## 3. User Flow Diagram

This feature is primarily about code quality and testing, not user workflows. However, the consistency improvements affect ALL user journeys by ensuring visual coherence.

```
============================================================================
 CURRENT STATE: INCONSISTENT VISUAL PATTERNS
============================================================================

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  TOURNAMENT DETAIL PAGE (tournaments/detail.html)                       │
  │  ─────────────────────────────────────────────────────────────────────  │
  │                                                                         │
  │  ISSUE: Heavy inline styles instead of PicoCSS classes                  │
  │                                                                         │
  │  EXAMPLE:                                                               │
  │  ❌ style="padding: 15px; background-color: #f8f9fa; border-left: 3px"  │
  │  ✅ class="card" (use PicoCSS <article>)                                │
  │                                                                         │
  │  ❌ style="padding: 4px 8px; background-color: #28a745; color: white"   │
  │  ✅ class="badge badge-active" (use FRONTEND.md badge pattern)          │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  PERMISSION DISPLAY (multiple templates)                                │
  │  ─────────────────────────────────────────────────────────────────────  │
  │                                                                         │
  │  INCONSISTENCY:                                                         │
  │                                                                         │
  │  overview.html (orphaned):                                              │
  │    Admin: ✓ / ✗                                                         │
  │                                                                         │
  │  dashboard/index.html (active):                                         │
  │    Admin: Yes / No                                                      │
  │                                                                         │
  │  DECISION NEEDED: Pick one format and apply everywhere                  │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  BUTTON STYLING (multiple templates)                                    │
  │  ─────────────────────────────────────────────────────────────────────  │
  │                                                                         │
  │  Pattern 1 (CORRECT - PicoCSS):                                         │
  │    <a href="/path" role="button">Action</a>                             │
  │    <a href="/path" role="button" class="secondary">Cancel</a>           │
  │                                                                         │
  │  Pattern 2 (INCONSISTENT - inline styles):                              │
  │    <a href="/path" style="padding: 8px 16px; background: #28a745;">     │
  │                                                                         │
  │  Pattern 3 (INCONSISTENT - mixed):                                      │
  │    <a href="/path" role="button" style="margin-left: 10px;">            │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

============================================================================
 DESIRED STATE: CONSISTENT VISUAL PATTERNS
============================================================================

  ALL TEMPLATES FOLLOW FRONTEND.md PATTERNS:

  ✅ No inline styles (use PicoCSS classes)
  ✅ Consistent badge classes for status indicators
  ✅ Consistent button patterns (role="button", class="secondary")
  ✅ Consistent permission display format
  ✅ No orphaned templates
  ✅ Automated tests catch future regressions
```

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Template Consistency

**Business Rule BR-UX-001: No Inline Styles**
> All HTML templates must use PicoCSS classes or FRONTEND.md-defined CSS classes. Inline `style=""` attributes are prohibited except for truly one-off layout adjustments that don't fit any pattern.

**Acceptance Criteria:**
```gherkin
Feature: Template styling consistency
  As a developer
  I want all templates to use consistent styling patterns
  So that the UI is visually coherent and maintainable

Scenario: No inline styles in templates
  Given I scan all HTML templates in app/templates/
  When I count style="" attributes
  Then the count should be less than 5 (tolerable exceptions)
  And none of them should be defining colors or padding

Scenario: Badge patterns follow FRONTEND.md
  Given a page displays a status badge
  When the badge is rendered
  Then it uses class="badge badge-{status}"
  And not inline background-color styles
```

### 4.2 Link Integrity

**Business Rule BR-UX-002: All Links Must Work**
> Every `href` and `action` attribute in templates must point to a route that exists in the application. No 404 links allowed.

**Acceptance Criteria:**
```gherkin
Feature: Link integrity
  As a user
  I want all buttons and links to lead to functional pages
  So that I never encounter unexpected 404 errors

Scenario: All template links have routes
  Given I extract all href values from HTML templates
  When I compare against defined routes in app/routers/
  Then every href should match a defined route pattern

Scenario: No orphaned template links
  Given I click a button on any page
  When the button has an href attribute
  Then the target page loads successfully (not 404)
```

### 4.3 No Orphaned Code

**Business Rule BR-UX-003: No Orphaned Templates**
> Every HTML template file must be either:
> 1. Rendered by a TemplateResponse in a router
> 2. Included by another template via {% include %}
> 3. Extended by another template via {% extends %}

**Acceptance Criteria:**
```gherkin
Feature: No orphaned templates
  As a developer
  I want to know all template files are actively used
  So that dead code doesn't accumulate

Scenario: All templates are referenced
  Given I list all HTML files in app/templates/
  When I trace references in Python code and other templates
  Then every template should have at least one reference

Scenario: Orphaned templates are removed
  Given overview.html exists as orphaned file
  When I delete it
  Then no functionality is broken
  And tests continue to pass
```

### 4.4 Consistent UI Patterns

**Business Rule BR-UX-004: Consistent Permission Display**
> User permission/role displays must use a consistent format across all templates. **User preference: Checkmark symbols (check/X).**

**Acceptance Criteria:**
```gherkin
Feature: Consistent permission display
  As a user viewing my permissions
  I want the display format to be consistent across pages
  So that I understand my access level clearly

Scenario: Permissions use checkmark symbol format
  Given I view my permissions on any page
  When the permission table is rendered
  Then each permission shows a checkmark symbol for granted access
  And an X symbol for denied access
  And not "Yes/No" text variants
```

---

## 5. Current State Analysis

### 5.1 Orphaned Templates

**Business Rule:** No unused templates should exist
**Implementation Status:** BROKEN

**Orphaned Files Found:**

| File | Evidence | Recommendation |
|------|----------|----------------|
| `app/templates/overview.html` | No Python route references `"overview.html"` (grep confirms) | DELETE - replaced by `dashboard/index.html` |
| `app/templates/pools/overview.html` | No Python route references `"pools/overview.html"` | KEEP - planned for future pool viewing |

### 5.2 Inline Style Analysis

**Business Rule:** Use PicoCSS classes, not inline styles
**Implementation Status:** PARTIALLY BROKEN

**Files with Significant Inline Styles:**

| File | Line Count | Issue Description |
|------|------------|-------------------|
| `tournaments/detail.html` | 25+ inline style attributes | Layout, colors, padding all inline |
| `dancers/list.html` | 3 inline style attributes | Button styling |
| `tournaments/list.html` | 5 inline style attributes | Link and button styling |
| `admin/users.html` | 3 inline style attributes | Button styling |
| `dancers/_table.html` | 2 inline style attributes | Link styling |

### 5.3 Inconsistent Patterns

**Permissions Display:**
- `dashboard/index.html:34-51` uses `"Yes"` / `"No"`
- `overview.html:84-97` uses `"✓"` / `"✗"` (orphaned file, but shows pattern was changed)

**Button Styling:**
- CORRECT: `<a href="/path" role="button">Action</a>` (most templates)
- INCORRECT: `<a href="/path" style="padding: 8px 16px; background-color: #28a745;">` (tournaments/detail.html)

### 5.4 Testing Gap

**Current E2E Test Coverage:**
- Route functionality (200 OK responses)
- Authentication/authorization
- HTMX partial responses
- Gherkin-style docstrings

**Missing E2E Test Coverage:**
- Template consistency validation
- Link integrity checking
- Orphaned code detection
- Visual pattern verification

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production)

1. **Delete orphaned `overview.html`**
   - File: `app/templates/overview.html`
   - Verify no route uses it (already confirmed)
   - Delete file
   - Run all tests to confirm no breakage

2. **Remove inline styles from `tournaments/detail.html`**
   - Replace inline layout styles with PicoCSS `<article>` components
   - Replace inline badge styles with `.badge` classes
   - Replace inline button styles with `role="button"` pattern

### 6.2 Recommended

3. **Remove inline styles from remaining files**
   - `dancers/list.html`
   - `tournaments/list.html`
   - `admin/users.html`
   - `dancers/_table.html`

4. **Add E2E tests for UX consistency**

   **Test 1: Link Integrity Test**
   ```python
   def test_all_template_links_have_routes():
       """Verify all href attributes in templates point to existing routes."""
       # Extract all href values from templates
       # Compare against Flask/FastAPI route registry
       # Fail if any href doesn't match a route
   ```

   **Test 2: Orphan Detection Test**
   ```python
   def test_no_orphaned_templates():
       """Verify all templates are referenced by code or other templates."""
       # List all .html files in app/templates/
       # Trace references in Python code and templates
       # Fail if any template has zero references
   ```

   **Test 3: Inline Style Detection Test**
   ```python
   def test_minimal_inline_styles():
       """Verify templates don't use inline styles for common patterns."""
       # Scan templates for style="" attributes
       # Ignore acceptable exceptions (e.g., truly unique layouts)
       # Fail if count exceeds threshold
   ```

5. **Document `pools/overview.html` as future feature**
   - Add comment in file explaining it's prepared for future use
   - OR wire it to a `/pools/{category_id}` route if functionality exists

### 6.3 Nice-to-Have (Future)

6. **Pre-commit hook for template linting**
   - Fail commits that add inline styles
   - Warn about new templates without route references

7. **Visual regression testing with screenshots**
   - Playwright screenshot comparison
   - Catch unintended visual changes

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Should we pick `Yes/No` or `checkmark/x` for permission display?
  - **A:** Checkmark symbols (check/X) per user preference. Update `dashboard/index.html` to use symbols instead of "Yes/No".

- **Q:** What about `pools/overview.html` - delete or keep?
  - **A:** Keep for now - appears to be prepared for future pool standings feature. Add comment documenting its purpose.

- **Q:** How strict should the inline style test be?
  - **A:** TBD - Suggest threshold of 5 exceptions max, with explicit allowlist for truly necessary cases.

### 7.2 Files to Modify

**DELETE:**
- `app/templates/overview.html` (orphaned)

**REFACTOR (remove inline styles):**
- `app/templates/tournaments/detail.html`
- `app/templates/dancers/list.html`
- `app/templates/tournaments/list.html`
- `app/templates/admin/users.html`
- `app/templates/dancers/_table.html`

**CREATE:**
- `tests/e2e/test_ux_consistency.py` (new E2E test file)

### 7.3 Pattern Scan Results

**Pattern searched:** Orphaned templates (no Python references)

**Search commands:**
```bash
grep -rn "overview\.html" app/routers/  # Found phases/overview.html only
grep -rn "pools/overview\.html" app/routers/  # No matches
```

**Results:**

| File | Status | Decision |
|------|--------|----------|
| `app/templates/overview.html` | No route reference | Delete |
| `app/templates/pools/overview.html` | No route reference | Document as future feature |

**Decision:** Delete `overview.html`, keep `pools/overview.html` with documentation.

### 7.4 User Confirmation

- [x] User confirmed problem statement (UX inconsistencies, Frankenstein app)
- [x] User chose Full UX Audit scope
- [x] User chose "Investigate first" for legacy files (done - confirmed orphaned)
- [x] User chose Full UX E2E tests for testing level
- [x] User approved permission display format: Checkmark symbols (check/X)
- [ ] User to validate acceptance criteria
- [ ] User to approve final requirements

---

**Status:** Business Analysis and Requirements Definition complete. Awaiting user approval to proceed to Implementation Planning.
