# Feature Specification: User Management Actions Column Layout Fix

**Date:** 2025-12-17
**Status:** Awaiting User Validation

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [User Flow Diagram](#2-user-flow-diagram)
3. [Business Rules & Acceptance Criteria](#3-business-rules--acceptance-criteria)
4. [Current State Analysis](#4-current-state-analysis)
5. [Pattern Scan Results](#5-pattern-scan-results)
6. [Implementation Recommendations](#6-implementation-recommendations)

---

## 1. Problem Statement

The User Management page (`/admin/users`) displays action buttons (Edit, Resend Magic Link, Delete) in a broken vertical layout with inconsistent styling, making it difficult for admins to quickly identify and perform actions on users.

**User Impact:** Poor visual hierarchy and inefficient use of table space. Actions that should be compact and horizontally aligned are stacking vertically, creating overly tall table rows.

---

## 2. User Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════════
 CURRENT STATE (BROKEN)                    DESIRED STATE
═══════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────┐          ┌─────────────────────────────┐
  │ Actions Column              │          │ Actions Column              │
  ├─────────────────────────────┤          ├─────────────────────────────┤
  │                             │          │                             │
  │  Edit (link)                │          │  [Edit] [Resend] [Delete]   │
  │                             │          │                             │
  │  ┌─────────────────────┐    │          │  • Compact horizontal row   │
  │  │ Resend Magic Link   │    │          │  • Consistent button style  │
  │  └─────────────────────┘    │          │  • Proper spacing           │
  │                             │          │                             │
  │  ┌─────────────────────┐    │          └─────────────────────────────┘
  │  │      Delete         │    │
  │  └─────────────────────┘    │
  │                             │
  └─────────────────────────────┘

  🚨 ISSUES:
  • Vertical stacking (no flex container)
  • "Edit" is a plain link, not styled as button
  • "Resend Magic Link" has outline style (large)
  • "Delete" has contrast outline style (dark)
  • Form element creates block-level stacking
```

---

## 3. Business Rules & Acceptance Criteria

### 3.1 Action Button Layout

**Business Rule BR-UI-001: Table Action Buttons**
> Action buttons in data tables should be displayed horizontally in a compact row with consistent styling and appropriate spacing.

**Acceptance Criteria:**
```gherkin
Feature: User Management Action Buttons
  As an admin
  I want action buttons displayed in a compact horizontal row
  So that I can quickly identify and perform user actions

  Scenario: Actions display in horizontal layout
    Given I am on the User Management page
    When I view the Actions column for any user
    Then I should see Edit, Resend Magic Link, and Delete buttons
    And they should be arranged horizontally with consistent spacing
    And the row height should be reasonable (not overly tall)

  Scenario: Action buttons have consistent styling
    Given I am viewing user action buttons
    Then Edit should be styled as a secondary/outline button (navigation)
    And Resend Magic Link should be styled as a secondary/outline button (action)
    And Delete should be styled as a contrast/danger button (destructive)
    And all buttons should have consistent padding and font size

  Scenario: Actions are accessible
    Given I am using keyboard navigation
    When I tab through the Actions column
    Then I should be able to focus each action in sequence
    And each action should have visible focus indicators
```

---

## 4. Current State Analysis

### 4.1 Template Analysis
**File:** `app/templates/admin/users.html:53-67`

**Current Implementation:**
```html
<td>
    <a href="/admin/users/{{ user.id }}/edit">Edit</a>

    <form method="post" action="..." class="inline-form">
        <button type="submit" class="secondary outline">
            Resend Magic Link
        </button>
    </form>

    <button type="button" onclick="openDeleteModal(...)" class="contrast outline">
        Delete
    </button>
</td>
```

**Issues Identified:**
1. **No container** - Actions are siblings with no flex/grid wrapper
2. **Mixed element types** - `<a>`, `<form>`, `<button>` behave differently
3. **Form is block-level** - Even with `inline-form` class, PicoCSS forms may override
4. **Edit is unstyled link** - No button styling, visually inconsistent
5. **Buttons too wide** - `outline` class creates full-width appearance

### 4.2 CSS Analysis
**File:** `app/static/css/battles.css:442-450`

**Existing `.inline-form` class:**
```css
.inline-form {
    display: inline;
    margin: 0;
}

.inline-form button {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}
```

**Assessment:** The class exists but:
- Only sets `display: inline` (not `inline-block` or `inline-flex`)
- No wrapper for horizontal grouping
- Button styling is minimal

### 4.3 FRONTEND.md Patterns

**Relevant guidance (FRONTEND.md:299-322):**
- Primary action: `<button type="submit">`
- Secondary action: `<a role="button" class="secondary">`
- Destructive action: `<button class="contrast">`

**Missing:** No documented pattern for "horizontal action button group in tables"

---

## 5. Pattern Scan Results

**Pattern searched:** Table action buttons with mixed elements

**Search commands:**
```bash
grep -rn "class=\"inline-form\"" app/templates/
grep -rn "<td>.*<a.*Edit.*</a>" app/templates/
```

**Results:**

| File | Line | Description | Status |
|------|------|-------------|--------|
| `admin/users.html` | 53-67 | User actions (Edit, Resend, Delete) | BROKEN - vertical layout |

**Other tables checked:**
- `dancers/list.html` - Uses different pattern (links only)
- `tournaments/list.html` - Uses different pattern (links only)

**Decision:**
- [x] Fix reported bug only (User Management page)
- [ ] This pattern should be documented in FRONTEND.md for future use

---

## 6. Implementation Recommendations

### 6.1 Critical (Immediate Fix)

1. **Add action button group wrapper**
   - Wrap all actions in `<div class="action-group">` or similar
   - Apply flexbox: `display: flex; gap: 0.5rem; align-items: center;`

2. **Style Edit as button**
   - Change from `<a>Edit</a>` to `<a role="button" class="secondary outline">Edit</a>`
   - Or use the smaller button styling

3. **Use compact button classes**
   - Add `.btn-sm` or similar for smaller buttons in tables
   - Ensure consistent sizing across all three actions

### 6.2 Recommended

1. **Document pattern in FRONTEND.md**
   - Add "Table Action Button Group" pattern
   - Include accessibility requirements
   - Show responsive behavior (mobile: stack, desktop: inline)

2. **Create reusable CSS class**
   - `.action-group` or `.table-actions` in base CSS
   - Ensures consistency across all tables

### 6.3 Nice-to-Have (Future)

1. **Icon-only buttons on mobile**
   - Show text labels on desktop
   - Show icons only on mobile for space efficiency

2. **Dropdown menu for 3+ actions**
   - Consider "More" dropdown if actions grow

---

## 7. Appendix: Reference Material

### 7.1 Open Questions

- **Q:** Should the button styling be PicoCSS native or custom classes?
  - **A:** Prefer PicoCSS native (`secondary`, `contrast`) with size adjustments

- **Q:** Should this fix apply to other tables (dancers, tournaments)?
  - **A:** Pending user input - currently those tables only use links

### 7.2 User Confirmation Checklist

- [ ] User confirmed problem statement
- [ ] User validated acceptance criteria
- [ ] User approved implementation approach

---

**Next Steps:** After user approval, run `/plan-implementation` to create technical implementation plan.
