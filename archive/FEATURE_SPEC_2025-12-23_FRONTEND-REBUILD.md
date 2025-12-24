# Feature Specification: Complete Frontend Rebuild

**Date:** 2025-12-23
**Status:** Awaiting Technical Design

---

## Table of Contents
1. [Problem Statement](#1-problem-statement)
2. [Executive Summary](#2-executive-summary)
3. [Design System Analysis (Figma vs Current)](#3-design-system-analysis-figma-vs-current)
4. [Business Rules & Acceptance Criteria](#4-business-rules--acceptance-criteria)
5. [Current State Analysis](#5-current-state-analysis)
6. [Implementation Recommendations](#6-implementation-recommendations)
7. [Appendix: Reference Material](#7-appendix-reference-material)

---

## 1. Problem Statement

The current Battle-D frontend has evolved organically, resulting in inconsistent styling, scattered inline styles, and a "Frankenstein app" effect where new patterns coexist with legacy patterns. The Figma mockups define a cohesive, modern design system that should be implemented across all ~50 templates to provide a professional, unified user experience.

---

## 2. Executive Summary

### Scope
Complete frontend rebuild applying the Figma design system to all existing templates. This includes:
- New layout structure (sidebar with logo, profile header)
- Modal-based forms (replacing full-page forms)
- Card-based tournament display
- Consistent typography, colors, and spacing
- Tab-based navigation patterns

### User Decisions Confirmed
- **Scope:** Full app rebuild (all ~50 templates)
- **Profile header:** Show full name + role badge (no avatar)
- **Forms:** Convert to modal dialogs
- **Data model:** Visual changes only (no location fields)

### What Works in Current Design
| Feature | Status |
|---------|--------|
| PicoCSS base framework | Production Ready |
| HTMX integration | Production Ready |
| Responsive grid layout | Production Ready |
| Badge system (.badge-*) | Production Ready |
| Empty state component | Production Ready |
| Flash message system | Production Ready |
| Delete modal component | Production Ready |
| Accessibility (WCAG 2.1 AA) | Production Ready |

### What Needs Redesign
| Issue | Type | Impact |
|-------|------|--------|
| Sidebar lacks logo/branding | GAP | Visual identity missing |
| Header shows email instead of name | GAP | Unprofessional appearance |
| Forms are full pages, not modals | GAP | UX inconsistency with mockups |
| Tournament list uses table, not cards | GAP | Modern card layout needed |
| No tabs component | GAP | Missing UI pattern |
| Inline styles scattered across 15+ templates | TECH DEBT | Maintenance burden |
| Inconsistent button styling | TECH DEBT | Visual inconsistency |
| No "Create" button with orange outline style | GAP | Missing primary action pattern |

### Key Design Elements from Figma
- **Primary Color (Orange):** #F97316 (sidebar active, buttons, badges)
- **Sidebar:** White background, Battle-D logo at top, orange active state
- **Profile Header:** Full name (large), role badge below
- **Cards:** White with subtle border, hover shadow, 3-dot menu
- **Modals:** Clean white dialog, orange primary button, gray cancel
- **Empty States:** Large icon, centered text, orange CTA button
- **Tabs:** Underlined active state with count badge

---

## 3. Design System Analysis (Figma vs Current)

### 3.1 Layout Structure

**Figma Design:**
```
+------------------------------------------------------------------+
| +-------------+ +----------------------------------------------+ |
| | BATTLE-D    | |  Profile: Name (large)                      | |
| | [Logo]      | |           Role badge                        | |
| +-------------+ +----------------------------------------------+ |
| |             | |                                              | |
| | Tournaments | |  Page Title         [+ Create Button]       | |
| | Dancers     | |  Subtitle                                   | |
| |             | |                                              | |
| |             | |  [Tabs: Upcoming | Completed]               | |
| |             | |                                              | |
| |             | |  [Card Grid / Table / Empty State]          | |
| |             | |                                              | |
| +-------------+ |                                              | |
| | Notifications| |                                              | |
| | Settings    | |                                              | |
| +-------------+ +----------------------------------------------+ |
+------------------------------------------------------------------+
```

**Current Implementation:**
```
+------------------------------------------------------------------+
| +-------------+ +----------------------------------------------+ |
| | Battle-D    | |  Battle-D (h1)                               | |
| | (text only) | |  email@example.com - role                   | |
| +-------------+ +----------------------------------------------+ |
| | Dashboard   | |                                              | |
| | Dancers     | |  Page Title (h2)                            | |
| | Tournaments | |                                              | |
| | Users       | |  [Back to Overview link]                    | |
| | ----------  | |                                              | |
| | Tournament  | |  [Table / Empty State]                      | |
| | Details     | |                                              | |
| | Event Mode  | |                                              | |
| | ----------  | |                                              | |
| | Logout      | |                                              | |
| +-------------+ +----------------------------------------------+ |
+------------------------------------------------------------------+
```

### 3.2 Color Palette Comparison

| Element | Figma | Current | Action |
|---------|-------|---------|--------|
| Primary/Accent | #F97316 (orange) | #007bff (blue) | Change to orange |
| Sidebar Active | Orange background | No distinct style | Add orange bg |
| Create Button | Orange outline + text | Green background #28a745 | Change to outline |
| Success/Completed | Green | Green #28a745 | Keep |
| Warning/Cancelled | Red | Red #dc3545 | Keep |
| Pending/Neutral | Gray | Gray #6c757d | Keep |
| Phase Badge | Orange | Orange #ff9800 | Harmonize |

### 3.3 Component Mapping

| Figma Component | Current Equivalent | Gap |
|-----------------|-------------------|-----|
| Logo in sidebar | Text "Battle-D" | Need logo image/SVG |
| Profile header w/ name | Email + role text | Need name display |
| Navigation icons | Text-only links | Need icon set |
| Tournament cards | Table rows | Need card component |
| Tab navigation | None | Need tabs component |
| Create modal | Full page form | Need modal conversion |
| 3-dot menu on cards | Action links | Need dropdown menu |
| Empty state with trophy | Emoji-based | Use SVG icon |
| Phone input with country | Basic text input | Country dropdown |

### 3.4 Typography Comparison

| Element | Figma | Current |
|---------|-------|---------|
| Page title | Bold, ~24px | h2 default |
| Subtitle | Gray, ~14px | Paragraph muted |
| Card title | Semi-bold, ~18px | Not defined |
| Badge text | Uppercase, small | Uppercase, 0.875rem |
| Nav items | Regular, ~14px | Default link style |
| Profile name | Bold, ~20px | Not present |
| Profile role | Small badge | Plain text |

---

## 4. Business Rules & Acceptance Criteria

### 4.1 Sidebar Navigation

**Business Rule BR-UI-001: Sidebar Branding**
> The sidebar must display the Battle-D logo at the top to establish brand identity.

**Acceptance Criteria:**
```gherkin
Feature: Sidebar branding
  Scenario: Logo display
    Given a logged-in user
    When they view any page
    Then the Battle-D logo is visible at the top of the sidebar
    And the logo links to the dashboard

  Scenario: Active navigation state
    Given a user on the Tournaments page
    When they look at the sidebar
    Then the "Tournaments" link has an orange background (#F97316)
    And other links have no background
```

### 4.2 Profile Header

**Business Rule BR-UI-002: User Profile Display**
> The header must show the user's full name prominently with their role as a badge.

**Acceptance Criteria:**
```gherkin
Feature: Profile header
  Scenario: Name and role display
    Given a user "Ryan TIMMERMANS" with role "Admin"
    When they view any authenticated page
    Then they see "Ryan TIMMERMANS" in large text
    And they see "Admin" as a role badge below

  Scenario: Name fallback
    Given a user with only email "user@example.com"
    When they view any authenticated page
    Then they see the email as fallback display name
```

### 4.3 Tournament Cards

**Business Rule BR-UI-003: Tournament Card Display**
> Tournaments must display as cards with essential info (name, date, status) and actions.

**Acceptance Criteria:**
```gherkin
Feature: Tournament cards
  Scenario: Card content
    Given a tournament "Battle Championship 2025" in "Registration" phase
    When viewing the tournaments list
    Then a card displays with:
      | Element | Value |
      | Title | Battle Championship 2025 |
      | Date icon + date | Calendar icon + date |
      | Status badge | "Registration Phase" |
      | Actions menu | 3-dot vertical menu |

  Scenario: Empty state
    Given no tournaments exist
    When viewing the tournaments list
    Then a centered empty state shows:
      | Element | Content |
      | Icon | Trophy SVG |
      | Title | "Create a tournament" |
      | Message | "You haven't created any tournaments yet" |
      | Button | Orange "Create a new tournament" |
```

### 4.4 Tab Navigation

**Business Rule BR-UI-004: Tab-Based Filtering**
> List pages with multiple states must use tabs with count badges.

**Acceptance Criteria:**
```gherkin
Feature: Tab navigation
  Scenario: Tournament tabs
    Given 2 upcoming and 0 completed tournaments
    When viewing tournaments list
    Then tabs display:
      | Tab | Count |
      | Upcoming tournaments | 02 |
      | Completed tournaments | 00 |
    And "Upcoming tournaments" tab is active (underlined)

  Scenario: Tab switching
    When user clicks "Completed tournaments" tab
    Then content filters to show only completed tournaments
    And "Completed tournaments" tab becomes active
```

### 4.5 Modal Forms

**Business Rule BR-UI-005: Modal-Based Creation**
> Create and edit forms must appear as modal dialogs, not separate pages.

**Acceptance Criteria:**
```gherkin
Feature: Modal forms
  Scenario: Create tournament modal
    Given user clicks "+ Create a tournament" button
    When the modal opens
    Then it displays:
      | Field | Type |
      | Tournament name | Text input |
      | Tournament date | Date picker |
      | Country | Dropdown |
      | City | Text input |
    And footer has "Cancel" (gray) and "Save" (orange) buttons

  Scenario: Modal accessibility
    Given the create modal is open
    When user presses ESC key
    Then modal closes without saving
    And focus returns to trigger button

  Scenario: Create dancer modal
    Given user clicks "+ Create a dancer" button
    When the modal opens
    Then it displays two-column form:
      | Row | Left Field | Right Field |
      | 1 | First name | Last name |
      | 2 | Stage name | Date of birth |
      | 3 | Phone number (with country) | Email |
      | 4 | Country (optional) | City (optional) |
```

### 4.6 Create Button Style

**Business Rule BR-UI-006: Primary Action Button**
> The primary "Create" action must use orange outline style with + icon.

**Acceptance Criteria:**
```gherkin
Feature: Create button styling
  Scenario: Button appearance
    Given any list page (Tournaments, Dancers)
    Then the create button has:
      | Property | Value |
      | Border | 1px solid #F97316 |
      | Background | transparent (white) |
      | Text color | #F97316 |
      | Icon | Plus sign before text |
      | Border radius | Rounded (8px) |

  Scenario: Button hover
    When user hovers over create button
    Then background changes to light orange
    And text remains orange
```

### 4.7 Responsive Design

**Business Rule BR-UI-007: Mobile Responsiveness**
> All pages must remain functional and readable on mobile devices (320px+).

**Acceptance Criteria:**
```gherkin
Feature: Mobile layout
  Scenario: Sidebar collapse on mobile
    Given viewport width < 768px
    When viewing any page
    Then sidebar collapses or becomes hamburger menu
    And main content takes full width

  Scenario: Card grid on mobile
    Given viewport width < 768px
    When viewing tournament cards
    Then cards stack vertically (1 column)
    And remain fully readable

  Scenario: Modal on mobile
    Given viewport width < 768px
    When opening a create modal
    Then modal takes ~95% viewport width
    And remains scrollable if content overflows
```

### 4.8 Accessibility

**Business Rule BR-UI-008: WCAG 2.1 AA Compliance**
> All UI changes must maintain WCAG 2.1 AA accessibility compliance.

**Acceptance Criteria:**
```gherkin
Feature: Accessibility compliance
  Scenario: Color contrast
    Given any text element
    Then contrast ratio with background >= 4.5:1 (normal text)
    And contrast ratio >= 3:1 (large text, UI components)

  Scenario: Keyboard navigation
    Given user navigating with keyboard only
    When tabbing through page
    Then all interactive elements are focusable
    And focus order is logical
    And focus indicators are visible

  Scenario: Screen reader support
    Given user with screen reader
    When navigating modals
    Then modal has aria-labelledby pointing to title
    And aria-describedby for content
    And focus is trapped within modal when open
```

---

## 5. Current State Analysis

### 5.1 Template Inventory

**Templates requiring updates (~50 files):**

| Category | Files | Complexity |
|----------|-------|------------|
| Base layout | base.html, event_base.html | High - affects all pages |
| Components | 6 files (flash, empty, loading, modal, error) | Medium |
| Auth | login.html | Low |
| Dashboard | index.html, 3 partials | Medium |
| Tournaments | list.html, create.html, detail.html, add_category.html | High |
| Dancers | list.html, create.html, edit.html, profile.html, _table.html | High |
| Admin | users.html, create_user.html, edit_user.html, fix_active.html | Medium |
| Registration | register.html, 5 partials | Medium |
| Battles | detail.html, encode_*.html (4), _battle_queue.html | Medium |
| Pools | overview.html | Low |
| Event | command_center.html, 5 partials | Medium |
| Errors | 4 error pages | Low |

### 5.2 Files with Inline Styles (Priority Cleanup)

Based on codebase analysis, these templates contain inline styles that must be extracted to CSS:

1. `dancers/create.html` - 13 inline style attributes
2. `tournaments/create.html` - 8 inline style attributes
3. `dancers/edit.html` - Similar to create
4. `admin/create_user.html` - Form styling
5. `battles/detail.html` - Various inline styles
6. `battles/encode_pool.html` - Form styling

### 5.3 Missing Components

| Component | Usage | Priority |
|-----------|-------|----------|
| Tabs component | Tournament list, future lists | High |
| Card component | Tournament display | High |
| Dropdown menu | Card actions (3-dot) | Medium |
| Phone input | Dancer form | Medium |
| Country select | Tournament/Dancer forms | Medium |
| Icon system | Navigation, cards | High |

### 5.4 CSS Architecture

**Current files:**
- `error-handling.css` - Flash, modals, empty states (321 lines)
- `battles.css` - Battle grid, badges, forms (536 lines)
- `registration.css` - Two-panel layout (estimated ~400 lines)
- `event.css` - Event mode specific (estimated ~400 lines)

**Needed additions:**
- `design-system.css` - Variables, typography, colors
- `components.css` - Tabs, cards, buttons, icons
- `modals.css` - Form modal styling
- `sidebar.css` - Navigation styling

---

## 6. Implementation Recommendations

### 6.1 Critical (Before Production Use)

1. **Create design system CSS variables**
   - Define orange primary color (#F97316)
   - Define spacing scale
   - Define typography scale
   - Define shadow/elevation scale

2. **Rebuild base.html layout**
   - Add logo placeholder in sidebar
   - Restructure header for profile display
   - Add navigation icon placeholders
   - Implement orange active state

3. **Create modal form component**
   - Generic modal wrapper
   - Form layout utilities
   - Button styling (orange primary, gray secondary)
   - Keyboard/accessibility support

4. **Convert create forms to modals**
   - tournaments/create.html -> modal
   - dancers/create.html -> modal

5. **Remove all inline styles**
   - Extract to CSS classes
   - 15+ templates affected

### 6.2 Recommended

1. **Create tabs component**
   - Tab bar with counts
   - Active state styling
   - HTMX integration for content switching

2. **Create tournament card component**
   - Card layout with header/body
   - Date + location display
   - Status badge
   - 3-dot action menu

3. **Add icon system**
   - Choose icon library (Lucide, Heroicons, or custom SVG)
   - Calendar, location, user, trophy icons
   - Navigation icons

4. **Update empty states**
   - Use SVG trophy icon (not emoji)
   - Match Figma typography

5. **Update button styles**
   - Orange outline for primary actions
   - Consistent border-radius
   - Hover states

### 6.3 Nice-to-Have (Future Iterations)

1. **Phone input with country code**
   - International phone number library
   - Country flag dropdown

2. **Animated transitions**
   - Modal open/close
   - Tab switching
   - Card hover effects

3. **Dark mode theming**
   - Already partially supported
   - Define orange tints for dark mode

4. **Notification badge**
   - Sidebar notification indicator
   - Future feature preparation

---

## 7. Appendix: Reference Material

### 7.1 Open Questions & Answers

- **Q:** Should the logo be an image file or inline SVG?
  - **A:** TBD - Recommend inline SVG for styling flexibility

- **Q:** Which icon library to use?
  - **A:** TBD - Recommend Lucide (Feather successor) or Heroicons

- **Q:** Should we use CSS-only tabs or HTMX-powered?
  - **A:** HTMX preferred for consistency with existing patterns

### 7.2 Figma Design Elements Extracted

**Color tokens:**
```css
--color-primary: #F97316;        /* Orange - main accent */
--color-primary-light: #FED7AA;  /* Light orange - hover states */
--color-success: #22C55E;        /* Green - completed */
--color-warning: #EF4444;        /* Red - cancelled */
--color-neutral: #6B7280;        /* Gray - pending */
--color-background: #FFFFFF;     /* White - page background */
--color-surface: #FFFFFF;        /* White - card background */
--color-border: #E5E7EB;         /* Light gray - borders */
--color-text: #111827;           /* Dark - primary text */
--color-text-muted: #6B7280;     /* Gray - secondary text */
```

**Spacing scale:**
```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.25rem;  /* 20px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-10: 2.5rem;  /* 40px */
--space-12: 3rem;    /* 48px */
```

**Border radius:**
```css
--radius-sm: 0.25rem;  /* 4px - small elements */
--radius-md: 0.5rem;   /* 8px - buttons, inputs */
--radius-lg: 0.75rem;  /* 12px - cards */
--radius-full: 9999px; /* Pills, avatars */
```

### 7.3 User Confirmation

- [x] User confirmed problem statement (inconsistent frontend)
- [x] User validated scope: Full app rebuild
- [x] User confirmed: Profile header with name, no avatar
- [x] User confirmed: Convert forms to modals
- [x] User confirmed: Visual changes only (no data model changes for location)

---

## Next Steps

1. Review and approve this specification
2. Run `/plan-implementation FEATURE_SPEC_2025-12-23_FRONTEND-REBUILD.md`
3. Technical design will detail:
   - CSS architecture decisions
   - Component implementation order
   - Template migration sequence
   - Testing strategy
