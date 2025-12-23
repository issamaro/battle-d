# Feature Specification: Inline Styles Cleanup (Frontend Rebuild Phase 2)

**Date:** 2025-12-23
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Pattern Scan Results](#3-pattern-scan-results)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

18 templates still contain inline `style=""` attributes after the initial frontend rebuild (Phase 1). This creates:
- **Inconsistent visual design** - Colors/spacing don't match the new design system
- **Maintenance burden** - Styles scattered across templates instead of centralized SCSS
- **PicoCSS remnants** - Some inline styles reference `var(--pico-*)` CSS variables that no longer exist

---

## 2. Executive Summary

### Scope
Complete the frontend rebuild by migrating all remaining inline styles to the SCSS design system.

### What Works ✅
| Feature | Status |
|---------|--------|
| SCSS architecture (34 files) | Production Ready |
| Base templates (base.html, event_base.html) | Production Ready |
| High-traffic pages (list views, dashboard) | Production Ready |
| Core components (flash, modal, empty state) | Production Ready |
| Form templates (create/edit dancers, users, tournaments) | Production Ready |

### What's Broken 🚨
| Issue | Type | Files Affected |
|-------|------|----------------|
| Inline styles with hardcoded colors | TECH DEBT | 18 templates |
| PicoCSS variable references (`--pico-*`) | BUG | 8 templates |
| Inconsistent spacing (px instead of design tokens) | TECH DEBT | 15 templates |
| Missing semantic CSS classes | GAP | All 18 templates |

### Key Business Rules Defined
- **BR-CSS-001:** No inline `style=""` attributes in production templates
- **BR-CSS-002:** All colors must use SCSS design tokens
- **BR-CSS-003:** All spacing must use SCSS spacing scale ($space-*)
- **BR-CSS-004:** PicoCSS references must be removed

---

## 3. Pattern Scan Results

**Pattern searched:** `style="` attribute in HTML templates

**Search command:**
```bash
grep -rn 'style="' app/templates/
```

**Results by Category:**

### 3.1 Error Pages (5 files, ~25 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `errors/401.html` | 5 | Centered layout, large heading, monospace text |
| `errors/403.html` | 5 | Same pattern as 401 |
| `errors/404.html` | 4 | Same pattern as 401 |
| `errors/500.html` | 5 | Same pattern as 401 |
| `errors/tournament_config_error.html` | 5 | Same pattern as 401 |

**Common inline styles:**
- `max-width: 600px; text-align: center; padding: 3rem 1rem;`
- `font-size: 6rem; margin: 0; color: var(--pico-color-*);`
- `margin-left: 1rem;`

### 3.2 Battle Pages (3 files, ~25 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `battles/detail.html` | 10 | Card layout, grid, winner highlight |
| `battles/encode_pool.html` | 8 | Form with radio card selection |
| `battles/encode_tiebreak.html` | 8 | Same pattern as encode_pool |

**Common inline styles:**
- `border: 1px solid var(--pico-muted-border-color); border-radius: 8px; padding: 24px;`
- `display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;`
- `color: #28a745;` (success green)

### 3.3 Dancer Profile (1 file, ~20 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `dancers/profile.html` | 20 | Definition table, info box |

**Common inline styles:**
- Table rows with `border-bottom: 1px solid #dee2e6;`
- `padding: 10px; font-weight: bold;`
- Blue button: `background-color: #007bff; color: white;`

### 3.4 Tournament Add Category (1 file, ~15 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `tournaments/add_category.html` | 15 | Form with info boxes, dynamic calculator |

**Common inline styles:**
- Warning box: `background-color: #fff3cd; border-left: 4px solid #ffc107;`
- Info box: `background-color: #d1ecf1; border-left: 3px solid #0c5460;`
- Form inputs: `width: 100%; padding: 8px;`

### 3.5 Admin Fix Tournaments (1 file, ~15 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `admin/fix_active_tournaments.html` | 15 | Warning section, table with badges |

**Common inline styles:**
- Warning section: `background-color: #fff3cd; border: 2px solid #ffc107;`
- Inline badges: `padding: 4px 8px; background-color: #007bff; color: white; border-radius: 4px;`

### 3.6 Pools Overview (1 file, ~8 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `pools/overview.html` | 8 | Card, standings table with winner highlight |

**Common inline styles:**
- Winner row: `background-color: rgba(40, 167, 69, 0.1); font-weight: bold;`
- Status text: `color: #28a745;` / `color: #dc3545;`

### 3.7 Registration (2 files, ~8 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `registration/register.html` | 2 | Loading indicator, duo summary |
| `registration/_dancer_search.html` | 6 | Legacy table with inline buttons |

### 3.8 Minor Remaining (4 files, ~6 inline styles)
| File | Line Count | Pattern |
|------|------------|---------|
| `dancers/edit.html` | 1 | Gray background card |
| `tournaments/create.html` | 2 | Info box |
| `tournaments/list.html` | 1 | Warning card header |
| `admin/edit_user.html` | 1 | Gray background card |

**Decision:**
- [x] Fix all in this feature (systematic cleanup)

---

## 4. Business Rules & Acceptance Criteria

### 4.1 No Inline Styles in Templates

**Business Rule BR-CSS-001: No Inline Style Attributes**
> All visual styling must be defined in SCSS files. No `style=""` attributes allowed in production HTML templates.

**Acceptance Criteria:**
```gherkin
Feature: Inline styles removed from all templates
  As a developer
  I want all styles in SCSS files
  So that the design system is consistent and maintainable

  Scenario: No inline styles in templates
    Given the application templates
    When I search for style="" attributes
    Then I should find 0 matches
    And all styling should be defined in SCSS classes

  Scenario: Templates use semantic CSS classes
    Given a template with visual elements
    When I view the HTML source
    Then elements should have descriptive class names
    And classes should map to SCSS component definitions
```

### 4.2 Error Pages Use Design System

**Business Rule BR-CSS-002: Error Pages Match Design System**
> Error pages (401, 403, 404, 500) must use the Battle-D design system colors, typography, and spacing.

**Acceptance Criteria:**
```gherkin
Feature: Error pages styled with design system
  Scenario: 404 page displays correctly
    Given I navigate to a non-existent URL
    When the 404 error page loads
    Then the error code should be displayed in a large heading
    And the page should be centered with proper spacing
    And colors should match the design system danger palette
    And buttons should use .btn and .btn-secondary classes
```

### 4.3 Battle Encode Forms Use Card Component

**Business Rule BR-CSS-003: Forms Use Standard Components**
> Battle encoding forms must use the standard card and form components from the design system.

**Acceptance Criteria:**
```gherkin
Feature: Battle encode forms use design system
  Scenario: Encode pool battle results
    Given I am on the encode pool battle page
    When the page loads
    Then the form should be wrapped in a .card component
    And performer selection should use .form-check radio styling
    And submit buttons should use .btn classes
    And spacing should use design system tokens
```

### 4.4 Profile Pages Use Definition List Styling

**Business Rule BR-CSS-004: Profile Data Uses Consistent Layout**
> Dancer profile pages must display data in a clean, consistent table format using the design system.

**Acceptance Criteria:**
```gherkin
Feature: Dancer profile uses design system
  Scenario: View dancer profile
    Given I navigate to a dancer's profile page
    When the page loads
    Then dancer details should be in a styled table
    And labels should be visually distinct from values
    And the edit button should use .btn-primary class
```

---

## 5. Current State Analysis

### 5.1 Error Pages
**Business Rule:** Error pages should provide clear feedback with consistent styling
**Implementation Status:** ⚠️ Functional but inconsistent
**Evidence:** All 5 error templates use:
- `var(--pico-color-*)` CSS variables (PicoCSS remnants - won't render)
- Hardcoded spacing (`3rem 1rem`)
- Inline font-size (`6rem`)
**Test Coverage:** No visual regression tests

### 5.2 Battle Encode Pages
**Business Rule:** Staff can efficiently encode battle results
**Implementation Status:** ⚠️ Functional but inconsistent
**Evidence:**
- Uses `var(--pico-muted-border-color)` (won't render)
- Grid layout is inline instead of utility class
- Radio cards have custom inline styling
**Test Coverage:** Functional tests exist, no visual tests

### 5.3 Dancer Profile
**Business Rule:** Staff can view dancer information
**Implementation Status:** ⚠️ Functional but inconsistent
**Evidence:**
- Uses Bootstrap-like colors (#007bff, #dee2e6)
- Table styling is all inline
- Button uses non-standard color
**Test Coverage:** No visual tests

### 5.4 Tournament Add Category
**Business Rule:** Staff can configure category parameters
**Implementation Status:** ⚠️ Functional but inconsistent
**Evidence:**
- Warning/info boxes use Bootstrap colors
- Form inputs have inline width/padding
- Calculator display uses inline font-size
**Test Coverage:** Functional tests exist

### 5.5 Admin Fix Tournaments
**Business Rule:** Admin can resolve tournament conflicts
**Implementation Status:** ⚠️ Functional but inconsistent
**Evidence:**
- Warning section uses Bootstrap warning colors
- Inline badges don't match design system
- Table alignment uses inline styles
**Test Coverage:** Limited

### 5.6 Pools Overview
**Business Rule:** Staff can view pool standings
**Implementation Status:** ⚠️ Functional but inconsistent
**Evidence:**
- Winner highlight uses inline rgba color
- Status text uses hardcoded colors
- Card uses PicoCSS border variable
**Test Coverage:** Limited

---

## 6. Implementation Recommendations

### 6.1 Critical (Required for Consistency)

1. **Create error page SCSS partial** (`_error-pages.scss`)
   - `.error-page` container class
   - `.error-code` for large heading
   - `.error-message` for description
   - `.error-actions` for button group

2. **Create battle encode SCSS partial** (`_battles.scss`)
   - `.battle-card` wrapper
   - `.performer-selection` grid
   - `.performer-option` radio card
   - `.winner-badge` highlight

3. **Create profile page SCSS partial** (`_profile.scss`)
   - `.profile-table` definition list/table
   - `.profile-label` for field names
   - `.profile-value` for field values
   - `.profile-actions` for edit button

4. **Create info/warning box component** (`_alerts.scss`)
   - `.alert` base class
   - `.alert-warning` yellow box
   - `.alert-info` blue box
   - `.alert-danger` red box

5. **Update all 18 templates** to use new classes

### 6.2 Recommended

1. **Add `.table-definition`** for key-value data display
2. **Add `.text-success` / `.text-danger`** utility classes
3. **Add `.row-highlight`** for table winner highlighting
4. **Update registration/_dancer_search.html** to use design system completely

### 6.3 Nice-to-Have (Future)

1. Create reusable Jinja components for:
   - `components/alert.html` - Info/warning/danger boxes
   - `components/profile_table.html` - Key-value display
2. Add visual regression tests for error pages
3. Document new components in FRONTEND.md

---

## 7. Appendix: Reference Material

### 7.1 Inline Style Count by File

| File | Inline Styles | Priority |
|------|---------------|----------|
| `dancers/profile.html` | 20 | High |
| `tournaments/add_category.html` | 15 | High |
| `admin/fix_active_tournaments.html` | 15 | Medium |
| `battles/detail.html` | 10 | High |
| `battles/encode_pool.html` | 8 | High |
| `battles/encode_tiebreak.html` | 8 | High |
| `pools/overview.html` | 8 | Medium |
| `registration/_dancer_search.html` | 6 | Low |
| `errors/401.html` | 5 | Medium |
| `errors/403.html` | 5 | Medium |
| `errors/404.html` | 4 | Medium |
| `errors/500.html` | 5 | Medium |
| `errors/tournament_config_error.html` | 5 | Medium |
| `registration/register.html` | 2 | Low |
| `tournaments/create.html` | 2 | Low |
| `tournaments/list.html` | 1 | Low |
| `dancers/edit.html` | 1 | Low |
| `admin/edit_user.html` | 1 | Low |
| **TOTAL** | **~121** | |

### 7.2 Color Mapping (Bootstrap → Design System)

| Bootstrap Color | Hex | Design System Token |
|-----------------|-----|---------------------|
| Primary blue | #007bff | $color-primary (#F97316) - Use orange instead |
| Success green | #28a745 | $color-success (#22C55E) |
| Danger red | #dc3545 | $color-danger (#EF4444) |
| Warning yellow | #ffc107 | $color-warning (#F59E0B) |
| Info cyan | #17a2b8 | $color-primary-light (#FED7AA) |
| Light gray | #f8f9fa | $color-neutral-light (#F3F4F6) |
| Border gray | #dee2e6 | $color-border (#E5E7EB) |
| Muted text | #6c757d | $color-text-muted (#6B7280) |
| Dark text | #495057 | $color-text-secondary (#4B5563) |

### 7.3 Spacing Mapping (px → Design Tokens)

| Pixel Value | Design Token |
|-------------|--------------|
| 4px | $space-1 |
| 8px | $space-2 |
| 10px | $space-2 (round down) or $space-3 |
| 12px | $space-3 |
| 15px | $space-4 (round up) |
| 16px | $space-4 |
| 20px | $space-5 |
| 24px | $space-6 |
| 32px | $space-8 |

### 7.4 User Confirmation
- [ ] User confirmed problem statement
- [ ] User validated scenarios
- [ ] User approved requirements
