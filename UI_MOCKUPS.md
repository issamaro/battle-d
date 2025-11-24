# Battle-D UI/UX Design System
**Level 2: Derived** | Last Updated: 2025-11-24

**Version:** 2.1
**Design Philosophy:** Minimalism • Accessibility • Progressive Enhancement

> **Note:** For all validation constraints (field lengths, limits, formulas), refer to [VALIDATION_RULES.md](VALIDATION_RULES.md) as the source of truth.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Technology Stack](#technology-stack)
3. [Layout Architecture](#layout-architecture)
4. [Component Library](#component-library)
5. [User Flows](#user-flows)
6. [Page Designs](#page-designs)
7. [Accessibility Guidelines](#accessibility-guidelines)
8. [Responsive Design](#responsive-design)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Design Principles

### 1. Minimalism

**Philosophy:** Remove every element that doesn't serve a clear purpose.

- **Clean Visual Hierarchy:** Use whitespace, not borders, to separate content
- **Typography-First:** Let content breathe without heavy decoration
- **Color as Signal:** Color indicates status and actions, not decoration
- **Progressive Disclosure:** Show users what they need when they need it

**Anti-Patterns to Avoid:**
- ❌ Dense information tables without breathing room
- ❌ Excessive borders and dividers
- ❌ Decorative icons that don't aid understanding
- ❌ Complex multi-column layouts on small screens

### 2. Accessibility

**WCAG 2.1 Level AA Compliance:**

- **Keyboard Navigation:** All interactions accessible without a mouse
- **Screen Readers:** Semantic HTML with proper ARIA labels
- **Color Contrast:** Minimum 4.5:1 for text, 3:1 for UI components
- **Focus Indicators:** Clear, visible focus states for all interactive elements
- **Error Messages:** Associated with form fields via `aria-describedby`

**Assistive Technology Support:**
- VoiceOver (iOS/macOS)
- NVDA (Windows)
- JAWS (Windows)
- TalkBack (Android)

### 3. Mobile-First Design

**Approach:** Design for smallest screen first, enhance for larger screens.

**Breakpoints:**
- **Mobile:** 320px - 768px (primary design target)
- **Tablet:** 769px - 1024px
- **Desktop:** 1025px+

**Mobile Optimizations:**
- Touch targets minimum 44x44px
- Stack all layouts vertically
- Full-width buttons for primary actions
- Simplified navigation (hamburger or bottom nav)

### 4. Progressive Enhancement

**Core Experience:** Works without JavaScript (except HTMX-dependent features).

**Enhancement Layers:**
1. **HTML:** Semantic, accessible structure
2. **CSS:** Visual presentation and responsive layout
3. **HTMX:** Dynamic updates without full page reload
4. **JavaScript:** Complex interactions (duo selection, live calculations)

---

## Technology Stack

### Frontend Framework

**PicoCSS 2.x** - Minimal, semantic CSS framework

**Why PicoCSS:**
- ✅ Class-less design (works with semantic HTML)
- ✅ Accessibility built-in (ARIA, keyboard nav)
- ✅ Dark mode support (automatic via `prefers-color-scheme`)
- ✅ Minimal footprint (~10KB gzipped)
- ✅ Responsive by default

**Custom CSS:** Only for layout (CSS Grid for sidebar navigation).

### Dynamic Interactions

**HTMX 2.0.4** - HTML-driven AJAX, WebSockets, Server-Sent Events

**Use Cases:**
- Dancer search (live results without page reload)
- Battle list auto-refresh (every 10s during active tournament)
- Form submissions with inline validation
- Partial page updates (category list after creation)

**Why HTMX:**
- ✅ Reduces JavaScript complexity
- ✅ Server-side rendering friendly
- ✅ Progressive enhancement friendly
- ✅ Accessibility-friendly (updates DOM, screen readers see changes)

### Templating

**Jinja2** - Server-side templating with FastAPI

**Patterns:**
- Template inheritance (`base.html` → page templates)
- Partial templates for HTMX responses (`_table.html`, `_dancer_search.html`)
- Context-aware navigation (role-based menu items)

---

## Layout Architecture

### Base Template Structure

All pages extend `base.html` which provides:

1. **Vertical Sidebar Navigation** (logged-in users only)
2. **Page Header** (title, user info)
3. **Main Content Area** (page-specific content)
4. **Footer** (system info)

**Layout Grid:**
```
┌────────────┬──────────────────────────┐
│            │  Header                  │
│  Sidebar   ├──────────────────────────┤
│  (250px)   │                          │
│            │  Main Content            │
│  - Logo    │                          │
│  - Nav     │  (fluid width)           │
│  - User    │                          │
│  - Logout  │                          │
│            ├──────────────────────────┤
│            │  Footer                  │
└────────────┴──────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌──────────────────────────┐
│  Header                  │
├──────────────────────────┤
│  Sidebar (collapsed)     │
├──────────────────────────┤
│                          │
│  Main Content            │
│                          │
├──────────────────────────┤
│  Footer                  │
└──────────────────────────┘
```

### CSS Grid Implementation

```css
body {
  display: grid;
  grid-template-columns: 250px 1fr;
  grid-template-rows: auto 1fr auto;
  grid-template-areas:
    "sidebar header"
    "sidebar main"
    "sidebar footer";
  min-height: 100vh;
}

aside { grid-area: sidebar; }
header { grid-area: header; }
main { grid-area: main; }
footer { grid-area: footer; }

@media (max-width: 768px) {
  body {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "sidebar"
      "main"
      "footer";
  }
}
```

---

## Component Library

### 1. Navigation

#### Vertical Sidebar (Desktop)

**Location:** Left side, sticky position
**Width:** 250px
**Contents:**
- App logo/title
- Primary navigation links (role-based)
- Horizontal separator
- Logout link (secondary style)

**HTML Structure:**
```html
<aside>
  <h2>Battle-D</h2>
  <nav>
    <ul>
      <li><a href="/overview">Overview</a></li>
      <li><a href="/phases">Phases</a></li>
      {% if current_user.is_staff %}
      <li><a href="/dancers">Dancers</a></li>
      <li><a href="/tournaments">Tournaments</a></li>
      {% endif %}
      {% if current_user.is_admin %}
      <li><a href="/admin/users">Users</a></li>
      {% endif %}
      <li><hr></li>
      <li><a href="/auth/logout" class="secondary">Logout</a></li>
    </ul>
  </nav>
</aside>
```

**Accessibility:**
- `<nav>` landmark for screen readers
- `<ul>` list structure announces item count
- Current page indicated via `aria-current="page"` (future enhancement)

#### Mobile Navigation

**Strategy:** Collapse to top, stack vertically
**Trigger:** Automatic at 768px breakpoint
**Enhancement (Phase 4):** Hamburger menu with slide-out drawer

### 2. Forms

#### Standard Form Pattern

**Layout:**
- Max-width: 600px (comfortable reading width)
- Single column (mobile-first)
- Labels above inputs
- Required fields marked with asterisk
- Error messages below fields

**HTML Structure (PicoCSS):**
```html
<form method="post" action="/endpoint">
  <label for="email">
    Email <abbr title="required">*</abbr>
  </label>
  <input
    type="email"
    id="email"
    name="email"
    required
    aria-describedby="email-error"
  >
  {% if errors.email %}
  <small id="email-error" role="alert">{{ errors.email }}</small>
  {% endif %}

  <button type="submit">Submit</button>
  <a href="/cancel" role="button" class="secondary">Cancel</a>
</form>
```

**Validation States:**
- **Invalid:** `aria-invalid="true"` + red border (PicoCSS)
- **Valid:** Green checkmark (optional, Phase 4)
- **Error Message:** Associated via `aria-describedby`

#### Form Button Patterns

**Primary Action (Submit):**
```html
<button type="submit">Create Tournament</button>
```
- Full-width on mobile
- Auto-width on desktop (grouped with cancel)

**Secondary Action (Cancel):**
```html
<a href="/back" role="button" class="secondary">Cancel</a>
```
- Links styled as buttons for consistency
- Secondary variant (gray/muted color)

**Destructive Action (Delete):**
```html
<button type="submit" class="contrast">Delete User</button>
```
- Contrast variant (PicoCSS high-contrast button)
- Should have confirmation dialog (Phase 4)

### 3. Tables

#### Responsive Data Table

**Desktop Layout:** Traditional table with columns
**Mobile Layout:** Stack rows as cards (CSS transformation)

**HTML Structure:**
```html
<table role="table">
  <thead>
    <tr>
      <th scope="col">Tournament</th>
      <th scope="col">Phase</th>
      <th scope="col">Status</th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td data-label="Tournament">Summer Battle 2024</td>
      <td data-label="Phase">Registration</td>
      <td data-label="Status"><span class="badge">Created</span></td>
      <td data-label="Actions">
        <a href="/tournaments/123">View</a>
      </td>
    </tr>
  </tbody>
</table>
```

**Mobile Transformation (< 768px):**
```css
@media (max-width: 768px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }
  thead { display: none; }
  td::before {
    content: attr(data-label) ": ";
    font-weight: bold;
  }
}
```

**Accessibility:**
- `scope="col"` on header cells
- `data-label` for mobile presentation
- Action links use descriptive text (not just "View")

### 4. Cards

#### Tournament/Dancer Card

**Use Case:** Grid layouts, featured content

**HTML Structure:**
```html
<article>
  <header>
    <strong>Summer Battle 2024</strong>
    <small>Phase: Registration</small>
  </header>
  <p>Categories: 3 • Registered: 45 dancers</p>
  <footer>
    <a href="/tournaments/123">View Details</a>
    {% if current_user.is_admin %}
    <a href="/tournaments/123/edit" role="button" class="secondary">Edit</a>
    {% endif %}
  </footer>
</article>
```

**PicoCSS Benefits:**
- `<article>` auto-styled with padding, border
- `<header>` and `<footer>` within article get proper spacing
- Responsive by default

### 5. Status Badges

#### Badge Component

**Use Case:** Tournament status, dancer availability, battle outcomes

**HTML Structure:**
```html
<span class="badge badge-created">Created</span>
<span class="badge badge-active">Active</span>
<span class="badge badge-completed">Completed</span>
```

**CSS Implementation:**
```css
.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.25rem;
  text-transform: uppercase;
}

.badge-created {
  background: var(--pico-muted-color);
  color: white;
}

.badge-active {
  background: var(--pico-primary-background);
  color: white;
}

.badge-completed {
  background: var(--pico-secondary-background);
  color: white;
}
```

### 6. Info Boxes

#### Informational Message Component

**Types:**
- **Info:** General information (blue)
- **Warning:** Important notices (yellow)
- **Error:** Validation errors (red)
- **Success:** Confirmation messages (green)

**HTML Structure:**
```html
<aside role="status" aria-live="polite">
  ℹ️ Tournament must have at least 5 registered performers to advance.
</aside>
```

**PicoCSS Styling:**
- `<aside>` within `<main>` gets info-box styling
- `role="status"` announces to screen readers
- `aria-live="polite"` for dynamic messages

---

## User Flows

### Flow 1: Tournament Creation & Management

**Goal:** Admin creates a new tournament, adds categories, monitors registration

**Steps:**

1. **Create Tournament**
   - Navigate: Overview → Tournaments → Create
   - Input: Tournament name
   - Action: Submit → Redirects to tournament detail
   - Status: Tournament created in CREATED status

2. **Add Categories**
   - Location: Tournament detail page
   - Action: Click "Add Category"
   - Input: Category name, is_duo, groups_ideal
   - Live Calculation: Shows minimum performers needed
   - Action: Submit → Category added to tournament

3. **Monitor Registration**
   - Location: Tournament detail page
   - View: Category list with registration counts
   - Status Indicator: "Ready" (green) or "Insufficient" (red)

4. **Advance to Preselection**
   - Prerequisite: All categories have minimum performers
   - Location: Phase navigation or tournament detail
   - Action: Click "Advance Phase"
   - Validation: Backend checks all rules
   - Result: Tournament auto-activates (CREATED → ACTIVE)

**Wireframe:**
```
┌─────────────────────────────────────────┐
│ Tournament Detail: Summer Battle 2024   │
├─────────────────────────────────────────┤
│ Status: [Created]  Phase: [Registration]│
│                                          │
│ Categories                               │
│ ┌──────────────────────────────────────┐│
│ │ Hip Hop 1v1                          ││
│ │ Registered: 8 / 5 minimum [Ready ✓] ││
│ │ [View] [Edit]                        ││
│ └──────────────────────────────────────┘│
│ ┌──────────────────────────────────────┐│
│ │ Krump Duo                            ││
│ │ Registered: 3 / 5 minimum [⚠️]       ││
│ │ [View] [Edit]                        ││
│ └──────────────────────────────────────┘│
│                                          │
│ [+ Add Category]                         │
│                                          │
│ ─────────────────────────────────────── │
│                                          │
│ ❌ Cannot advance: 1 category has        │
│    insufficient performers               │
│                                          │
│ [Advance Phase] (disabled)               │
└─────────────────────────────────────────┘
```

### Flow 2: Dancer Registration

**Goal:** Staff registers dancers for tournament categories

**Steps:**

1. **Access Registration**
   - Navigate: Overview → Tournaments → [Tournament] → Register
   - Or: Dancers → [Dancer] → Register for Tournament

2. **Search Dancer** (HTMX)
   - Input: Search by name, blaze, or email
   - Live Results: Show matching dancers as user types
   - Action: Select dancer from results

3. **Select Category**
   - Prerequisite: Dancer not already registered in this tournament
   - View: Available categories with current registration counts
   - Action: Select category → Submit

4. **Confirmation**
   - Result: Dancer added to category performers
   - Redirect: Back to registration page or dancer profile
   - Message: "Dancer registered successfully"

**Wireframe (Mobile-First):**
```
┌────────────────────────────┐
│ Register Dancer            │
├────────────────────────────┤
│ Search Dancer:             │
│ [________________] 🔍      │
│                            │
│ Results:                   │
│ ┌────────────────────────┐ │
│ │ B-Boy Storm            │ │
│ │ storm@example.com      │ │
│ │ [Select]               │ │
│ └────────────────────────┘ │
│ ┌────────────────────────┐ │
│ │ Crazy Legs             │ │
│ │ legs@example.com       │ │
│ │ [Select]               │ │
│ └────────────────────────┘ │
│                            │
│ Select Category:           │
│ ○ Hip Hop 1v1 (8/5) ✓     │
│ ○ Krump Duo (3/5) ⚠️       │
│                            │
│ [Register Dancer]          │
│ [Cancel]                   │
└────────────────────────────┘
```

### Flow 3: Battle Judging (Phase 2)

**Goal:** Judge scores battles in real-time during tournament

**Steps:**

1. **Access Battle List**
   - Navigate: Overview → Battles (MC/Judge only)
   - View: Current pool battles, auto-refresh every 10s (HTMX)
   - Filter: By status (Ready, In Progress, Completed)

2. **Start Battle** (MC)
   - Prerequisite: Battle status = Ready
   - Action: Click "Start Battle"
   - Result: Status → In Progress, notifies judges

3. **Score Battle** (Judge)
   - View: Performer names, blaze, crew
   - Input: Score per performer (1-100 scale or preference vote)
   - Action: Submit scores
   - Result: Scores saved, battle status → Completed

4. **View Results** (All)
   - View: Aggregated scores, winner declared
   - Update: Pool standings recalculated
   - Next: Advance to next battle

**Wireframe (Judge Interface):**
```
┌────────────────────────────┐
│ Battle: Pool A - Battle 1  │
├────────────────────────────┤
│ Status: [In Progress]      │
│                            │
│ Performer 1:               │
│ ┌────────────────────────┐ │
│ │ B-Boy Storm            │ │
│ │ Blaze: Storm           │ │
│ │ Crew: Soul Assassins   │ │
│ │                        │ │
│ │ Your Score:            │ │
│ │ [_____] / 100          │ │
│ └────────────────────────┘ │
│                            │
│ Performer 2:               │
│ ┌────────────────────────┐ │
│ │ Crazy Legs             │ │
│ │ Blaze: Crazy Legs      │ │
│ │ Crew: Rock Steady      │ │
│ │                        │ │
│ │ Your Score:            │ │
│ │ [_____] / 100          │ │
│ └────────────────────────┘ │
│                            │
│ [Submit Scores]            │
│                            │
│ Other Judges: 2/3 scored   │
└────────────────────────────┘
```

### Flow 4: Phase Advancement

**Goal:** Admin advances tournament through phases with validation

**Steps:**

1. **View Current Phase**
   - Location: Tournament detail or dedicated phase page
   - View: Current phase status, requirements for advancement
   - Validation Indicators: Green (ready) or red (blocked)

2. **Check Validation**
   - Automatic: System validates all rules
   - Display: List of passing/failing checks
   - Example: "✓ All categories have minimum performers"

3. **Advance Phase**
   - Prerequisite: All validation checks pass
   - Action: Click "Advance Phase" button
   - Confirmation: Modal dialog (Phase 4 enhancement)
   - Result: Phase updated, tournament activated if from Registration

4. **Handle Validation Errors**
   - Scenario: Validation fails
   - Display: Detailed error messages
   - Action Required: Fix issues before retrying
   - Example: "Pool A has only 4 performers (minimum 5)"

**Wireframe (Validation View):**
```
┌────────────────────────────────────────┐
│ Phase Advancement: Summer Battle 2024  │
├────────────────────────────────────────┤
│ Current Phase: [Preselection]          │
│ Next Phase: [Pools]                    │
│                                        │
│ Validation Checks:                     │
│                                        │
│ ✓ All categories advanced to pools    │
│ ✓ Pools created for all categories    │
│ ✓ Performers distributed evenly       │
│ ❌ Pool A has insufficient performers  │
│    (4/5 minimum)                       │
│                                        │
│ ─────────────────────────────────────  │
│                                        │
│ ❌ Cannot advance: Fix errors above    │
│                                        │
│ [Advance to Pools] (disabled)          │
│ [Cancel]                               │
└────────────────────────────────────────┘
```

---

## Page Designs

### 1. Overview Page

**Route:** `/overview`
**Permission:** All authenticated users
**Purpose:** Central hub showing active tournament and role-specific actions

**Components:**
- Welcome message (user email, role)
- Active tournament card (name, phase, status)
- Role-specific action section
- Quick links to common tasks

**Layout (Desktop):**
```
┌────────┬──────────────────────────────────────┐
│        │ Overview                             │
│ Side   ├──────────────────────────────────────┤
│ bar    │ Welcome, admin@battle-d.com!         │
│        │ Role: Admin                          │
│ Nav    │                                      │
│        │ ┌──────────────────────────────────┐ │
│ - Over │ │ 🏆 Active Tournament             │ │
│ - Phase│ │                                  │ │
│ - Dance│ │ Summer Battle 2024               │ │
│ - Tourn│ │ Phase: Pools                     │ │
│ - Users│ │                                  │ │
│ ─────  │ │ [View Details] [Manage Phases]   │ │
│ Logout │ └──────────────────────────────────┘ │
│        │                                      │
│        │ Admin Actions                        │
│        │ ┌──────────────┬──────────────────┐ │
│        │ │ Manage Users │ View Tournaments │ │
│        │ └──────────────┴──────────────────┘ │
└────────┴──────────────────────────────────────┘
```

**Mobile Layout:**
```
┌────────────────────────────┐
│ Overview                   │
├────────────────────────────┤
│ Welcome, admin@...!        │
│ Role: Admin                │
│                            │
│ Active Tournament          │
│ ┌────────────────────────┐ │
│ │ Summer Battle 2024     │ │
│ │ Phase: Pools           │ │
│ │                        │ │
│ │ [View Details]         │ │
│ │ [Manage Phases]        │ │
│ └────────────────────────┘ │
│                            │
│ Admin Actions              │
│ [Manage Users]             │
│ [View Tournaments]         │
└────────────────────────────┘
```

**HTML Structure:**
```html
{% extends "base.html" %}
{% block header_title %}Overview{% endblock %}

{% block content %}
<article>
  <header>
    <h2>Welcome, {{ current_user.email }}!</h2>
    <p>Role: <strong>{{ current_user.role }}</strong></p>
  </header>

  <section>
    <h3>Active Tournament</h3>
    {% if active_tournament %}
    <article>
      <header>
        <strong>{{ active_tournament.name }}</strong>
        <small>Phase: {{ active_tournament.phase }}</small>
      </header>
      <footer>
        <a href="/tournaments/{{ active_tournament.id }}">View Details</a>
        {% if current_user.is_admin %}
        <a href="/phases" role="button">Manage Phases</a>
        {% endif %}
      </footer>
    </article>
    {% else %}
    <p>No active tournament.</p>
    {% if current_user.is_admin %}
    <a href="/tournaments/create" role="button">Create Tournament</a>
    {% endif %}
    {% endif %}
  </section>

  {% if current_user.is_admin %}
  <section>
    <h3>Admin Actions</h3>
    <div role="group">
      <a href="/admin/users" role="button">Manage Users</a>
      <a href="/tournaments" role="button" class="secondary">View Tournaments</a>
    </div>
  </section>
  {% endif %}
</article>
{% endblock %}
```

### 2. Tournament Detail Page

**Route:** `/tournaments/{id}`
**Permission:** Staff and above
**Purpose:** View tournament info, manage categories, advance phase

**Components:**
- Tournament header (name, status, phase)
- Category list with registration counts
- Add category button (if in registration phase)
- Phase advancement button (admin only)
- Validation status indicators

**User Interactions:**
1. View category details → Navigate to category performer list
2. Edit category → Navigate to category edit form
3. Add category (if registration phase) → Navigate to add category form
4. Advance phase (admin only) → Validate and advance if checks pass
5. View performers → Navigate to performer list for category

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────┐
│ Tournament: Summer Battle 2024         │
├────────────────────────────────────────┤
│ Status: [Active] Phase: [Registration]│
│ Created: 2024-06-01                    │
│                                        │
│ Categories (3)                         │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Hip Hop 1v1                        │ │
│ │ Type: Solo • Pools: 2 (ideal)      │ │
│ │ Registered: 8 / 5 minimum ✓        │ │
│ │ [View Performers] [Edit Category]  │ │
│ └────────────────────────────────────┘ │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Breaking Duo                       │ │
│ │ Type: Duo • Pools: 2 (ideal)       │ │
│ │ Registered: 4 / 5 minimum ⚠️        │ │
│ │ [View Performers] [Edit Category]  │ │
│ └────────────────────────────────────┘ │
│                                        │
│ [+ Add Category]                       │
│                                        │
│ ─────────────────────────────────────  │
│ Phase Advancement (Admin only)         │
│                                        │
│ ❌ Cannot advance: 1 category has      │
│    insufficient performers             │
│                                        │
│ [Advance to Preselection] (disabled)   │
└────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Tournament Detail          │
├────────────────────────────┤
│ Summer Battle 2024         │
│ [Active] [Registration]    │
│ Created: 2024-06-01        │
│                            │
│ Categories (3)             │
│                            │
│ ┌────────────────────────┐ │
│ │ Hip Hop 1v1            │ │
│ │                        │ │
│ │ Solo • 2 pools         │ │
│ │ Registered: 8/5 ✓      │ │
│ │                        │ │
│ │ [View Performers]      │ │
│ │ [Edit Category]        │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Breaking Duo           │ │
│ │                        │ │
│ │ Duo • 2 pools          │ │
│ │ Registered: 4/5 ⚠️      │ │
│ │                        │ │
│ │ [View Performers]      │ │
│ │ [Edit Category]        │ │
│ └────────────────────────┘ │
│                            │
│ [+ Add Category]           │
│                            │
│ ───────────────────────── │
│ Phase Advancement          │
│ (Admin only)               │
│                            │
│ ❌ Cannot advance          │
│ 1 category has             │
│ insufficient performers    │
│                            │
│ [Advance to Preselection]  │
│ (disabled)                 │
└────────────────────────────┘
```

**Accessibility:**
- **Keyboard Navigation:** Tab through category cards, buttons use Enter/Space
- **Screen Readers:** Each category card announced as article with status
- **ARIA Labels:**
  - Status badges have `aria-label="Active tournament"`
  - Phase badges have `aria-label="Current phase: Registration"`
  - Disabled button has `aria-disabled="true"` with error explanation
- **Focus Management:** Focus moves to validation error message when advancement fails

**Validation States:**
- **Ready:** All categories show green checkmarks, advance button enabled
- **Insufficient:** Categories with ⚠️ icon, advance button disabled, error message displayed
- **Loading:** "Checking validation..." message while backend validates

### 3. Dancer Registration Page

**Route:** `/tournaments/{id}/register`
**Permission:** Staff and above
**Purpose:** Register dancers for tournament categories via search

**Components:**
- Dancer search (HTMX live search)
- Search results (clickable cards)
- Category selection (radio buttons)
- Registration form

**HTMX Implementation:**
```html
<input
  type="search"
  name="q"
  placeholder="Search by name, blaze, or email..."
  hx-get="/dancers/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#search-results"
  autocomplete="off"
>

<div id="search-results">
  <!-- Results loaded here via HTMX -->
</div>
```

**Search Results Template (`_dancer_search.html`):**
```html
{% for dancer in dancers %}
<article>
  <header>
    <strong>{{ dancer.blaze }}</strong>
    <small>{{ dancer.first_name }} {{ dancer.last_name }}</small>
  </header>
  <p>{{ dancer.email }}</p>
  <footer>
    <a href="/dancers/{{ dancer.id }}/register?tournament={{ tournament_id }}"
       role="button">
      Select
    </a>
  </footer>
</article>
{% endfor %}
```

**User Interactions:**
1. Type in search field → Live search via HTMX (500ms delay)
2. Click dancer card → Pre-select dancer, show category selection
3. Select category → Enable register button
4. Click register → Submit form, redirect to tournament detail
5. Click cancel → Return to tournament detail

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Tournament      Register Dancer                  │
├────────────────────────────────────────────────────────────┤
│ Tournament: Summer Battle 2024                             │
│ Phase: Registration                                        │
│                                                            │
│ ┌────────────────────────────┬─────────────────────────┐  │
│ │ Search Dancer              │ Select Category         │  │
│ │                            │                         │  │
│ │ [Search by name, blaze...] │ ○ Hip Hop 1v1          │  │
│ │ 🔍                         │   Registered: 8/5 ✓    │  │
│ │                            │                         │  │
│ │ Results (Live Search):     │ ○ Breaking Duo         │  │
│ │                            │   Registered: 4/5 ⚠️    │  │
│ │ ┌────────────────────────┐ │                         │  │
│ │ │ 🎭 B-Boy Storm         │ │ ○ Krump 1v1            │  │
│ │ │ John Doe               │ │   Registered: 6/5 ✓    │  │
│ │ │ storm@example.com      │ │                         │  │
│ │ │ [Select]               │ │                         │  │
│ │ └────────────────────────┘ │                         │  │
│ │                            │                         │  │
│ │ ┌────────────────────────┐ │ ℹ️ Dancer can only     │  │
│ │ │ 🎭 Crazy Legs          │ │   register for one     │  │
│ │ │ Sarah Smith            │ │   category per         │  │
│ │ │ legs@example.com       │ │   tournament           │  │
│ │ │ [Select]               │ │                         │  │
│ │ └────────────────────────┘ │                         │  │
│ │                            │                         │  │
│ │ ┌────────────────────────┐ │                         │  │
│ │ │ 🎭 B-Girl Fierce       │ │                         │  │
│ │ │ Maria Garcia           │ │                         │  │
│ │ │ fierce@example.com     │ │                         │  │
│ │ │ [Select]               │ │                         │  │
│ │ └────────────────────────┘ │                         │  │
│ └────────────────────────────┴─────────────────────────┘  │
│                                                            │
│ [Register Dancer] (disabled until both selected)          │
│ [Cancel]                                                   │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Register Dancer            │
├────────────────────────────┤
│ Tournament:                │
│ Summer Battle 2024         │
│ Phase: Registration        │
│                            │
│ Step 1: Search Dancer      │
│ [Search by name, blaze...] │
│ 🔍                         │
│                            │
│ Results:                   │
│ ┌────────────────────────┐ │
│ │ 🎭 B-Boy Storm         │ │
│ │ John Doe               │ │
│ │ storm@example.com      │ │
│ │ [Select]               │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ 🎭 Crazy Legs          │ │
│ │ Sarah Smith            │ │
│ │ legs@example.com       │ │
│ │ [Select]               │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ 🎭 B-Girl Fierce       │ │
│ │ Maria Garcia           │ │
│ │ fierce@example.com     │ │
│ │ [Select]               │ │
│ └────────────────────────┘ │
│                            │
│ ───────────────────────── │
│ Step 2: Select Category    │
│                            │
│ ○ Hip Hop 1v1             │
│   Registered: 8/5 ✓       │
│                            │
│ ○ Breaking Duo            │
│   Registered: 4/5 ⚠️       │
│                            │
│ ○ Krump 1v1               │
│   Registered: 6/5 ✓       │
│                            │
│ ℹ️ Dancer can only         │
│   register for one         │
│   category per tournament  │
│                            │
│ [Register Dancer]          │
│ (disabled until complete)  │
│                            │
│ [Cancel]                   │
└────────────────────────────┘
```

**HTMX Interactions:**
- **Live Search:** `hx-get="/dancers/search"` with `hx-trigger="keyup changed delay:500ms"`
- **Search Results Target:** `hx-target="#search-results"` updates results div
- **Partial Template:** `_dancer_search.html` returns only result cards
- **No Full Page Reload:** Search happens without navigation

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through search field → result cards → category radios → buttons
  - Enter/Space to select dancer or category
- **Screen Reader Announcements:**
  - Search results announced with `aria-live="polite"`
  - Result count announced: "3 dancers found"
  - Selected dancer announced: "B-Boy Storm selected"
- **ARIA Labels:**
  - Search input: `aria-label="Search dancers by name, blaze, or email"`
  - Result cards: `aria-label="Dancer: B-Boy Storm, Email: storm@example.com"`
  - Category radios: `aria-describedby="category-info"` for status indicators
- **Focus Management:**
  - Focus stays in search field during typing
  - Focus moves to first result when Enter pressed
  - Focus moves to Register button when both selections made

**Validation States:**
- **Empty Search:** Show "Type to search dancers..." placeholder
- **Searching:** Show loading spinner in search field
- **No Results:** Show "No dancers found. Try different search terms."
- **Dancer Selected:** Highlight selected card with border, show checkmark
- **Category Selected:** Highlight selected radio button
- **Ready to Submit:** Enable Register button (green)
- **Error:** Show error message if registration fails (e.g., dancer already registered)

### 4. Category Creation Form

**Route:** `/tournaments/{id}/categories/create`
**Permission:** Admin only
**Purpose:** Add category to tournament with live minimum calculation

**Components:**
- Category name input
- Duo checkbox
- Groups ideal input (number)
- Live minimum calculation (JavaScript)
- Submit button

**JavaScript Live Calculation:**
```javascript
const groupsInput = document.getElementById('groups_ideal');
const minDisplay = document.getElementById('minimum-performers');

groupsInput.addEventListener('input', (e) => {
  const groups = parseInt(e.target.value) || 0;
  const minimum = (groups * 2) + 1;
  minDisplay.textContent = `Minimum performers: ${minimum}`;
});
```

**User Interactions:**
1. Enter category name → Required field validation
2. Check/uncheck duo checkbox → Affects pairing requirements
3. Enter number of pools → Live calculation updates minimum performers
4. Click create → Validate form, create category, redirect to tournament detail
5. Click cancel → Return to tournament detail

**Desktop Layout (> 768px):**
```
┌──────────────────────────────────────────────────────┐
│ ← Back to Tournament      Add Category               │
├──────────────────────────────────────────────────────┤
│ Tournament: Summer Battle 2024                       │
│ Phase: Registration                                  │
│                                                      │
│ Category Name: *                                     │
│ [_________________________________________]          │
│ Example: "Hip Hop 1v1", "Breaking Duo"               │
│                                                      │
│ ☐ Duo Category                                       │
│ Check if this is a 2v2 category (pairs of dancers)  │
│                                                      │
│ Ideal Number of Pools: *                             │
│ [____] (Typically 2-4 pools)                         │
│                                                      │
│ ┌──────────────────────────────────────────────────┐ │
│ │ 📊 Calculated Requirements                       │ │
│ │                                                  │ │
│ │ Minimum Performers: 5                            │ │
│ │ Formula: (pools × 2) + 1 = (2 × 2) + 1 = 5      │ │
│ │                                                  │ │
│ │ This ensures:                                    │ │
│ │ • At least 2 performers per pool                 │ │
│ │ • At least 1 elimination in preselection         │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [Create Category]  [Cancel]                         │
└──────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Add Category               │
├────────────────────────────┤
│ Tournament:                │
│ Summer Battle 2024         │
│ Phase: Registration        │
│                            │
│ Category Name: *           │
│ [__________________]       │
│ Ex: "Hip Hop 1v1"          │
│                            │
│ ☐ Duo Category             │
│ (2v2 pairs)                │
│                            │
│ Ideal Pools: *             │
│ [___]                      │
│ Typically 2-4              │
│                            │
│ ┌────────────────────────┐ │
│ │ 📊 Requirements        │ │
│ │                        │ │
│ │ Min Performers: 5      │ │
│ │                        │ │
│ │ Formula:               │ │
│ │ (pools × 2) + 1        │ │
│ │ (2 × 2) + 1 = 5        │ │
│ │                        │ │
│ │ Ensures:               │ │
│ │ • 2 per pool min       │ │
│ │ • 1 eliminated min     │ │
│ └────────────────────────┘ │
│                            │
│ [Create Category]          │
│                            │
│ [Cancel]                   │
└────────────────────────────┘
```

**Live Calculation Example:**
```
User types "3" in pools field:
→ Minimum updates to: 7
→ Formula shows: (3 × 2) + 1 = 7

User types "4" in pools field:
→ Minimum updates to: 9
→ Formula shows: (4 × 2) + 1 = 9
```

**Accessibility:**
- **Keyboard Navigation:** Tab through name → duo checkbox → pools → create → cancel
- **Screen Reader Announcements:**
  - Required fields announced: "Category name, required"
  - Checkbox state announced: "Duo category, checkbox, not checked"
  - Live calculation announced: "Minimum performers updated to 7"
- **ARIA Labels:**
  - Name input: `aria-label="Category name" aria-required="true"`
  - Pools input: `aria-label="Ideal number of pools" aria-required="true" aria-describedby="pools-help"`
  - Calculation box: `aria-live="polite"` announces changes
- **Focus Management:**
  - Focus on name field on page load
  - Invalid field shows error and gets focus
  - Success redirects with flash message

**Validation States:**
- **Empty Name:** "Category name is required" (red text below field)
- **Empty Pools:** "Number of pools is required"
- **Invalid Pools (0 or 1):** "Must be at least 2 pools (required for finals)"
- **Invalid Pools (too high):** "Maximum 10 pools allowed"
- **Valid:** Green checkmark next to field
- **Submitting:** "Creating category..." with spinner, button disabled
- **Success:** Redirect to tournament detail with "Category created successfully" message
- **Error:** "Failed to create category: [error message]" (red banner)

### 5. Battle List (Phase 2)

**Route:** `/battles`
**Permission:** MC, Judge
**Purpose:** View and manage battles during tournament

**Components:**
- Auto-refresh every 10s (HTMX polling)
- Battle cards (status, performers, actions)
- Filter by status (Ready, In Progress, Completed)
- Start battle button (MC only)
- Score battle button (Judge)

**User Interactions:**
1. View battle list → See all battles with real-time status updates
2. Filter battles → Select status filter (All, Ready, In Progress, Completed)
3. Start battle (MC only) → Change status from Ready to In Progress
4. Score battle (Judge only) → Navigate to judge scoring interface
5. View battle details → Navigate to battle detail page

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────────┐
│ ← Back                 Battles: Hip Hop 1v1 - Pool A           │
├────────────────────────────────────────────────────────────────┤
│ Filter: [All ▼] [Ready ▼] [In Progress ▼] [Completed ▼]       │
│ 🔄 Auto-refresh active (every 10s) • Last updated: 14:23:45    │
│                                                                │
│ ┌──────────────────────┬──────────────────────┬──────────────┐│
│ │ Battle 1             │ Battle 2             │ Battle 3     ││
│ │ [In Progress] 🔴     │ [Ready] ⏸️            │ [Completed] ✅││
│ │                      │                      │              ││
│ │ B-Boy Storm          │ B-Girl Fierce        │ The Kid      ││
│ │   vs                 │   vs                 │   vs         ││
│ │ Crazy Legs           │ Breakmaster          │ DJ Spin      ││
│ │                      │                      │              ││
│ │ Judges: 2/3 scored   │ Not started          │ Winner:      ││
│ │ ⚠️ Waiting for       │                      │ The Kid      ││
│ │   Judge #3           │ MC Actions:          │ Score: 3-2   ││
│ │                      │ [Start Battle]       │              ││
│ │ Judge Actions:       │ [Edit Matchup]       │ [View        ││
│ │ [Score Battle]       │                      │  Details]    ││
│ │ [View Details]       │                      │              ││
│ └──────────────────────┴──────────────────────┴──────────────┘│
│                                                                │
│ ┌──────────────────────┬──────────────────────┬──────────────┐│
│ │ Battle 4             │ Battle 5             │ Battle 6     ││
│ │ [Ready] ⏸️            │ [Ready] ⏸️            │ [Ready] ⏸️    ││
│ │                      │                      │              ││
│ │ Lady V               │ Phoenix              │ Thunder      ││
│ │   vs                 │   vs                 │   vs         ││
│ │ Storm Trooper        │ Blaze                │ Lightning    ││
│ │                      │                      │              ││
│ │ Not started          │ Not started          │ Not started  ││
│ │                      │                      │              ││
│ │ MC Actions:          │ MC Actions:          │ MC Actions:  ││
│ │ [Start Battle]       │ [Start Battle]       │ [Start Battle││
│ │ [Edit Matchup]       │ [Edit Matchup]       │ [Edit Matchup││
│ └──────────────────────┴──────────────────────┴──────────────┘│
└────────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Battles                    │
├────────────────────────────┤
│ Hip Hop 1v1 - Pool A       │
│                            │
│ Filter: [All ▼]            │
│ 🔄 Auto-refresh (10s)      │
│ Last updated: 14:23:45     │
│                            │
│ ┌────────────────────────┐ │
│ │ Battle 1               │ │
│ │ [In Progress] 🔴       │ │
│ │                        │ │
│ │ B-Boy Storm            │ │
│ │   vs                   │ │
│ │ Crazy Legs             │ │
│ │                        │ │
│ │ Judges: 2/3 scored     │ │
│ │ ⚠️ Waiting for Judge #3│ │
│ │                        │ │
│ │ [Score Battle]         │ │
│ │ [View Details]         │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Battle 2               │ │
│ │ [Ready] ⏸️              │ │
│ │                        │ │
│ │ B-Girl Fierce          │ │
│ │   vs                   │ │
│ │ Breakmaster            │ │
│ │                        │ │
│ │ Not started            │ │
│ │                        │ │
│ │ [Start Battle] (MC)    │ │
│ │ [Edit Matchup] (MC)    │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Battle 3               │ │
│ │ [Completed] ✅          │ │
│ │                        │ │
│ │ The Kid                │ │
│ │   vs                   │ │
│ │ DJ Spin                │ │
│ │                        │ │
│ │ Winner: The Kid        │ │
│ │ Score: 3-2             │ │
│ │                        │ │
│ │ [View Details]         │ │
│ └────────────────────────┘ │
│                            │
│ (More battles below...)    │
└────────────────────────────┘
```

**HTMX Auto-Refresh:**
```html
<!-- Main battle list container with auto-refresh -->
<div
  hx-get="/battles/list?pool_id=123"
  hx-trigger="every 10s"
  hx-swap="innerHTML"
  hx-indicator="#refresh-indicator"
>
  <!-- Battle list loaded here and auto-refreshes every 10 seconds -->
  <!-- Partial template returns only battle cards -->
</div>

<!-- Refresh indicator -->
<span id="refresh-indicator" class="htmx-indicator" aria-live="polite">
  Refreshing...
</span>

<!-- Filter dropdown triggers immediate refresh -->
<select
  name="status_filter"
  hx-get="/battles/list?pool_id=123"
  hx-trigger="change"
  hx-target="#battle-list"
  hx-swap="innerHTML"
>
  <option value="all">All</option>
  <option value="ready">Ready</option>
  <option value="in_progress">In Progress</option>
  <option value="completed">Completed</option>
</select>

<!-- Start battle button (MC only) -->
<button
  hx-post="/battles/123/start"
  hx-swap="outerHTML"
  hx-target="closest article"
  hx-confirm="Start this battle?"
>
  Start Battle
</button>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through filter dropdown → battle cards → action buttons
  - Enter/Space to activate buttons and select filter options
  - Focus remains on current card after HTMX refresh
- **Screen Reader Announcements:**
  - Auto-refresh announced with `aria-live="polite"`: "Refreshing battle list"
  - Battle status changes announced: "Battle 1 status changed to In Progress"
  - Judge count updates announced: "2 of 3 judges have scored"
  - New battles announced when added to list
- **ARIA Labels:**
  - Battle cards: `role="article"` with `aria-label="Battle 1: B-Boy Storm vs Crazy Legs"`
  - Status badges: `aria-label="Status: In Progress"` with visual icons
  - Action buttons: `aria-label="Start Battle 2: B-Girl Fierce vs Breakmaster"`
  - Filter dropdown: `aria-label="Filter battles by status"`
  - Auto-refresh indicator: `aria-live="polite"` for loading announcements
- **Focus Management:**
  - Focus preserved after HTMX partial swap
  - Focus moves to status message after battle started
  - Focus returns to button after modal confirmation

**Validation States:**
- **Ready:** Battle card shows ⏸️ icon, "Not started" status, "Start Battle" button enabled (MC)
- **In Progress:** Battle card shows 🔴 icon, judge scoring progress (2/3), "Score Battle" enabled (Judge)
- **Completed:** Battle card shows ✅ icon, winner name displayed, final score shown
- **Waiting for Judges:** Warning icon ⚠️ with message "Waiting for Judge #3"
- **All Judges Scored:** Green checkmark with "All judges scored, calculating winner..."
- **Auto-Refresh Active:** 🔄 icon with timestamp, subtle fade animation on update
- **Auto-Refresh Failed:** "Connection lost. Click to refresh manually" message
- **Empty State:** "No battles in this pool yet" when list is empty
- **Loading:** Skeleton cards shown while initial load, no skeleton on auto-refresh (seamless update)

---

## Section 6: Authentication Pages

### 6. Login Page

**Route:** `/auth/login`
**Permission:** Public (unauthenticated users)
**Purpose:** Magic link email authentication for staff, judges, and MCs

**Components:**
- Email input field with validation
- Submit button with loading state
- Success message with instructions
- Error handling for invalid emails
- No password field (passwordless authentication)

**User Interactions:**
1. Enter email address → Live validation checks format
2. Submit form → Send magic link email via backend
3. See success message → Check email for magic link
4. Click magic link in email → Redirect to app (authenticated)
5. Return if error → See error message, retry

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                    ┌──────────────────────┐               │
│                    │                      │               │
│                    │   Battle-D           │               │
│                    │   Tournament System  │               │
│                    │                      │               │
│                    │   🎭                 │               │
│                    │                      │               │
│                    │   Sign In            │               │
│                    │                      │               │
│                    │   Enter your email   │               │
│                    │   to receive a       │               │
│                    │   sign-in link       │               │
│                    │                      │               │
│                    │   Email Address: *   │               │
│                    │   [_______________]  │               │
│                    │                      │               │
│                    │   [Send Sign-In Link]│               │
│                    │                      │               │
│                    │   ───────────────    │               │
│                    │                      │               │
│                    │   ℹ️ No password     │               │
│                    │   required. We'll    │               │
│                    │   email you a        │               │
│                    │   secure link.       │               │
│                    │                      │               │
│                    └──────────────────────┘               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│                            │
│   Battle-D                 │
│   Tournament System        │
│                            │
│   🎭                       │
│                            │
│   Sign In                  │
│                            │
│   Enter your email to      │
│   receive a sign-in link   │
│                            │
│   Email Address: *         │
│   [____________________]   │
│                            │
│   [Send Sign-In Link]      │
│                            │
│   ──────────────────────   │
│                            │
│   ℹ️ No password required  │
│   We'll email you a        │
│   secure link to sign in.  │
│                            │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Login form with HTMX -->
<form
  hx-post="/auth/login"
  hx-target="#message-area"
  hx-swap="innerHTML"
  hx-indicator="#submit-btn"
>
  <label for="email">Email Address:</label>
  <input
    type="email"
    id="email"
    name="email"
    required
    aria-required="true"
    aria-describedby="email-help"
    placeholder="judge@example.com"
  >
  <small id="email-help">We'll send you a secure sign-in link</small>

  <button
    type="submit"
    id="submit-btn"
    data-loading-text="Sending..."
  >
    Send Sign-In Link
  </button>
</form>

<!-- Message area for success/error messages -->
<div id="message-area" role="status" aria-live="polite"></div>

<!-- Success response (partial template) -->
<div class="success-message">
  ✅ Sign-in link sent!
  <p>Check your email at <strong>judge@example.com</strong></p>
  <p>The link expires in 5 minutes.</p>
</div>

<!-- Error response (partial template) -->
<div class="error-message" role="alert">
  ❌ Error: Email not found in system
  <p>Contact your tournament administrator.</p>
</div>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab to email field → Tab to submit button
  - Enter to submit form from email field
  - Focus moves to success/error message after submission
- **Screen Reader Announcements:**
  - Form submission announced: "Sending sign-in link"
  - Success message announced with `aria-live="polite"`: "Sign-in link sent"
  - Error message announced with `role="alert"`: "Error: Email not found"
  - Loading state announced: "Sending..."
- **ARIA Labels:**
  - Email input: `aria-required="true"`, `aria-describedby="email-help"`
  - Submit button: `aria-busy="true"` during submission
  - Message area: `role="status"` for success, `role="alert"` for errors
  - Form: `aria-label="Sign in with email"`
- **Focus Management:**
  - Focus remains on form after error to allow retry
  - Focus moves to success message after successful submission
  - Email field shows red border for invalid format

**Validation States:**
- **Empty Email:** "Email address is required" (on blur or submit)
- **Invalid Email Format:** "Please enter a valid email address" (live validation on blur)
- **Valid Email:** Green checkmark icon next to field
- **Submitting:** Button shows spinner, text changes to "Sending...", button disabled
- **Success:** Green banner with checkmark, instructions to check email
- **Email Not Found:** Red banner with error icon, message to contact admin
- **Rate Limited:** "Too many attempts. Maximum 5 requests per 15 minutes per email."
- **Network Error:** "Connection failed. Check your internet and try again."
- **Email Sent Recently:** "Sign-in link already sent. Please wait 30 seconds before requesting another."

---

## Section 7: Admin Pages

### 7. Users List

**Route:** `/admin/users`
**Permission:** Admin only
**Purpose:** View all users, filter by role, create/edit users

**Components:**
- Users table with sortable columns
- Filter by role (Admin, Staff, MC, Judge)
- Search by email
- Create user button
- Edit/delete actions per user
- Pagination for large user lists

**User Interactions:**
1. View users list → See all users with role and status
2. Filter by role → Select role from dropdown, list updates
3. Search by email → Type in search field, list filters in real-time
4. Create user → Navigate to create user form
5. Edit user → Navigate to edit user form
6. Delete user → Confirm modal, then delete

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────────────┐
│ ← Back                    Users                                    │
├────────────────────────────────────────────────────────────────────┤
│ [+ Create User]                                                    │
│                                                                    │
│ Filter: [All Roles ▼]     Search: [____________] 🔍               │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐│
│ │ Email ▲▼        │ Role ▲▼    │ Status ▲▼  │ Created ▲▼  │ Actions││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ admin@battle.com│ Admin      │ Active     │ 2024-01-15  │ [Edit] ││
│ │                 │            │            │             │ [Delete││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ judge1@test.com │ Judge      │ Active     │ 2024-02-01  │ [Edit] ││
│ │                 │            │            │             │ [Delete││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ mc@event.com    │ MC         │ Active     │ 2024-02-10  │ [Edit] ││
│ │                 │            │            │             │ [Delete││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ staff@battle.com│ Staff      │ Inactive   │ 2024-01-20  │ [Edit] ││
│ │                 │            │            │             │ [Delete││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ judge2@test.com │ Judge      │ Active     │ 2024-03-01  │ [Edit] ││
│ │                 │            │            │             │ [Delete││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                    │
│ Showing 5 of 12 users                          [Previous] [Next]  │
└────────────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Users                      │
├────────────────────────────┤
│ [+ Create User]            │
│                            │
│ Filter: [All Roles ▼]      │
│ Search: [____________] 🔍  │
│                            │
│ ┌────────────────────────┐ │
│ │ admin@battle.com       │ │
│ │ Admin • Active         │ │
│ │ Created: 2024-01-15    │ │
│ │ [Edit] [Delete]        │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ judge1@test.com        │ │
│ │ Judge • Active         │ │
│ │ Created: 2024-02-01    │ │
│ │ [Edit] [Delete]        │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ mc@event.com           │ │
│ │ MC • Active            │ │
│ │ Created: 2024-02-10    │ │
│ │ [Edit] [Delete]        │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ staff@battle.com       │ │
│ │ Staff • Inactive       │ │
│ │ Created: 2024-01-20    │ │
│ │ [Edit] [Delete]        │ │
│ └────────────────────────┘ │
│                            │
│ 5 of 12 users              │
│ [Previous] [Next]          │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Search field with live filtering -->
<input
  type="search"
  name="search"
  placeholder="Search by email..."
  hx-get="/admin/users/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#users-table"
  hx-indicator="#search-spinner"
>
<span id="search-spinner" class="htmx-indicator">🔍</span>

<!-- Role filter dropdown -->
<select
  name="role"
  hx-get="/admin/users"
  hx-trigger="change"
  hx-target="#users-table"
>
  <option value="">All Roles</option>
  <option value="admin">Admin</option>
  <option value="staff">Staff</option>
  <option value="mc">MC</option>
  <option value="judge">Judge</option>
</select>

<!-- Users table with sortable columns -->
<table id="users-table">
  <thead>
    <tr>
      <th>
        <a
          href="#"
          hx-get="/admin/users?sort=email&order=asc"
          hx-target="#users-table"
          hx-swap="outerHTML"
        >
          Email ▲▼
        </a>
      </th>
      <!-- More sortable columns... -->
    </tr>
  </thead>
  <tbody>
    <!-- User rows... -->
  </tbody>
</table>

<!-- Delete button with confirmation -->
<button
  hx-delete="/admin/users/123"
  hx-confirm="Delete user admin@battle.com? This cannot be undone."
  hx-target="closest tr"
  hx-swap="outerHTML swap:500ms"
>
  Delete
</button>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through Create User button → Filter dropdown → Search field → Table rows → Edit/Delete buttons
  - Arrow keys to navigate table cells
  - Enter/Space to activate sort headers, buttons
- **Screen Reader Announcements:**
  - Table: `role="table"` with `aria-label="Users list"`
  - Row count announced: "Showing 5 of 12 users"
  - Filter changes announced: "Filtered to Judge role, 4 users found"
  - Search results announced: "2 users found for 'judge1'"
  - Delete confirmation announced as modal
- **ARIA Labels:**
  - Create button: `aria-label="Create new user"`
  - Filter dropdown: `aria-label="Filter users by role"`
  - Search input: `aria-label="Search users by email"`
  - Sort headers: `aria-sort="ascending"` or `aria-sort="descending"`
  - Edit button: `aria-label="Edit user admin@battle.com"`
  - Delete button: `aria-label="Delete user admin@battle.com"`
- **Focus Management:**
  - Focus moves to search results after filtering
  - Focus moves to deleted row's next row after deletion
  - Focus preserved on sort header after table update

**Validation States:**
- **Loading Initial List:** Skeleton rows shown (5 placeholder rows)
- **Empty Search:** "No users found for 'xyz'"
- **Empty Filter:** "No users with role 'Judge'"
- **Searching:** Spinner icon in search field
- **Filtering:** Brief loading indicator on table
- **Sorting:** Arrow icon changes (▲ for asc, ▼ for desc)
- **Delete Confirmation:** Modal overlay with "Delete user?" prompt
- **Deleting:** Row fades out with spinner
- **Delete Success:** Row removed with slide-up animation, count updates
- **Delete Error:** "Failed to delete user: [reason]" message, row remains

---

### 8. Create User Form

**Route:** `/admin/users/create`
**Permission:** Admin only
**Purpose:** Create new user account with email and role

**Components:**
- Email input with validation
- Role selection (Admin, Staff, MC, Judge)
- Optional name field
- Submit button with loading state
- Cancel button

**User Interactions:**
1. Enter email → Live validation checks format and uniqueness
2. Select role → Required field, one of 4 roles
3. Enter optional name → For display purposes
4. Submit form → Create user, send invitation email
5. Success → Redirect to users list with success message

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Users           Create User                      │
├────────────────────────────────────────────────────────────┤
│ Create a new user account                                  │
│                                                            │
│ Email Address: *                                           │
│ [_____________________________________]                    │
│ User will receive a sign-in link at this address          │
│                                                            │
│ Role: *                                                    │
│ ○ Admin     - Full system access                          │
│ ○ Staff     - Manage tournaments, dancers, registration   │
│ ○ MC        - Start battles, manage pools                 │
│ ○ Judge     - Score battles only                          │
│                                                            │
│ Name: (optional)                                           │
│ [_____________________________________]                    │
│ Display name for UI                                        │
│                                                            │
│ ───────────────────────────────────────                   │
│                                                            │
│ [Create User]  [Cancel]                                    │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Users            │
│ Create User                │
├────────────────────────────┤
│ Create a new user account  │
│                            │
│ Email Address: *           │
│ [____________________]     │
│ User will receive a        │
│ sign-in link here          │
│                            │
│ Role: *                    │
│ ○ Admin                    │
│   Full system access       │
│                            │
│ ○ Staff                    │
│   Manage tournaments,      │
│   dancers, registration    │
│                            │
│ ○ MC                       │
│   Start battles,           │
│   manage pools             │
│                            │
│ ○ Judge                    │
│   Score battles only       │
│                            │
│ Name: (optional)           │
│ [____________________]     │
│ Display name for UI        │
│                            │
│ ──────────────────────     │
│                            │
│ [Create User]              │
│ [Cancel]                   │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Create user form -->
<form
  hx-post="/admin/users"
  hx-target="#form-messages"
  hx-swap="innerHTML"
  hx-indicator="#submit-btn"
>
  <label for="email">Email Address: *</label>
  <input
    type="email"
    id="email"
    name="email"
    required
    hx-post="/admin/users/check-email"
    hx-trigger="blur"
    hx-target="#email-validation"
    hx-swap="innerHTML"
  >
  <div id="email-validation" role="status" aria-live="polite"></div>

  <fieldset>
    <legend>Role: *</legend>
    <label>
      <input type="radio" name="role" value="admin" required>
      Admin - Full system access
    </label>
    <label>
      <input type="radio" name="role" value="staff">
      Staff - Manage tournaments, dancers, registration
    </label>
    <label>
      <input type="radio" name="role" value="mc">
      MC - Start battles, manage pools
    </label>
    <label>
      <input type="radio" name="role" value="judge">
      Judge - Score battles only
    </label>
  </fieldset>

  <label for="name">Name: (optional)</label>
  <input type="text" id="name" name="name">

  <button type="submit" id="submit-btn">Create User</button>
  <a href="/admin/users" role="button" class="secondary">Cancel</a>
</form>

<div id="form-messages" role="status" aria-live="polite"></div>

<!-- Success response redirects to users list -->
<!-- Error response shows in #form-messages -->
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through email field → role radios → name field → Create button → Cancel button
  - Arrow keys to navigate radio buttons
  - Enter/Space to select radio buttons
- **Screen Reader Announcements:**
  - Email validation announced: "Email is available" or "Email already exists"
  - Role selection announced: "Admin role selected"
  - Form submission announced: "Creating user..."
  - Success announced: "User created successfully"
  - Error announced: "Error: [message]"
- **ARIA Labels:**
  - Email input: `aria-required="true"`, `aria-describedby="email-help"`
  - Email validation: `role="status"`, `aria-live="polite"`
  - Role fieldset: `<legend>` provides group label
  - Submit button: `aria-busy="true"` during submission
  - Form messages: `role="status"` for success, `role="alert"` for errors
- **Focus Management:**
  - Focus moves to first error field if validation fails
  - Focus moves to success message after creation
  - Focus returns to form if backend error occurs

**Validation States:**
- **Empty Email:** "Email address is required" (on submit)
- **Invalid Email Format:** "Please enter a valid email address" (on blur)
- **Email Already Exists:** "This email is already registered" (async check on blur)
- **Email Available:** Green checkmark icon, "Email is available"
- **No Role Selected:** "Please select a role" (on submit)
- **Role Selected:** Radio button checked, description visible
- **Submitting:** Button shows spinner, text changes to "Creating...", form disabled
- **Success:** Redirect to users list with flash message "User created: admin@battle.com"
- **Backend Error:** Red banner with error message, form remains editable
- **Network Error:** "Connection failed. Check your internet and try again."

---

### 9. Edit User Form

**Route:** `/admin/users/{user_id}/edit`
**Permission:** Admin only
**Purpose:** Edit existing user's email, role, or status

**Components:**
- Email input (pre-filled) with validation
- Role selection (pre-selected)
- Name field (pre-filled, optional)
- Submit button with loading state
- Cancel button
- Delete user button (danger zone)

**User Interactions:**
1. View pre-filled form → See current user data
2. Edit email → Live validation checks format and uniqueness
3. Change role → Select different role
4. Submit form → Update user, show success message
5. Delete user → Confirm modal, then delete

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Users           Edit User                        │
├────────────────────────────────────────────────────────────┤
│ Editing: judge1@test.com                                   │
│                                                            │
│ Email Address: *                                           │
│ [judge1@test.com__________________]                        │
│ User will receive a sign-in link at this address          │
│                                                            │
│ Role: *                                                    │
│ ○ Admin     - Full system access                          │
│ ○ Staff     - Manage tournaments, dancers, registration   │
│ ○ MC        - Start battles, manage pools                 │
│ ● Judge     - Score battles only                          │
│                                                            │
│ Name: (optional)                                           │
│ [Judge One_____________________]                           │
│ Display name for UI                                        │
│                                                            │
│ ───────────────────────────────────────                   │
│                                                            │
│ [Update User]  [Cancel]                                    │
│                                                            │
│ ───────────────────────────────────────                   │
│ Danger Zone                                                │
│                                                            │
│ [Delete User]                                              │
│ This action cannot be undone                               │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Users            │
│ Edit User                  │
├────────────────────────────┤
│ Editing:                   │
│ judge1@test.com            │
│                            │
│ Email Address: *           │
│ [judge1@test.com_____]     │
│ User will receive a        │
│ sign-in link here          │
│                            │
│ Role: *                    │
│ ○ Admin                    │
│   Full system access       │
│                            │
│ ○ Staff                    │
│   Manage tournaments,      │
│   dancers, registration    │
│                            │
│ ○ MC                       │
│   Start battles,           │
│   manage pools             │
│                            │
│ ● Judge                    │
│   Score battles only       │
│                            │
│ Name: (optional)           │
│ [Judge One__________]      │
│ Display name for UI        │
│                            │
│ ──────────────────────     │
│                            │
│ [Update User]              │
│ [Cancel]                   │
│                            │
│ ──────────────────────     │
│ Danger Zone                │
│                            │
│ [Delete User]              │
│ Cannot be undone           │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Edit user form -->
<form
  hx-put="/admin/users/123"
  hx-target="#form-messages"
  hx-swap="innerHTML"
  hx-indicator="#submit-btn"
>
  <label for="email">Email Address: *</label>
  <input
    type="email"
    id="email"
    name="email"
    value="judge1@test.com"
    required
    hx-post="/admin/users/check-email?exclude=123"
    hx-trigger="blur"
    hx-target="#email-validation"
  >
  <div id="email-validation" role="status" aria-live="polite"></div>

  <fieldset>
    <legend>Role: *</legend>
    <label>
      <input type="radio" name="role" value="admin">
      Admin - Full system access
    </label>
    <label>
      <input type="radio" name="role" value="staff">
      Staff - Manage tournaments, dancers, registration
    </label>
    <label>
      <input type="radio" name="role" value="mc">
      MC - Start battles, manage pools
    </label>
    <label>
      <input type="radio" name="role" value="judge" checked>
      Judge - Score battles only
    </label>
  </fieldset>

  <label for="name">Name: (optional)</label>
  <input type="text" id="name" name="name" value="Judge One">

  <button type="submit" id="submit-btn">Update User</button>
  <a href="/admin/users" role="button" class="secondary">Cancel</a>
</form>

<div id="form-messages" role="status" aria-live="polite"></div>

<!-- Delete button in danger zone -->
<section class="danger-zone">
  <h3>Danger Zone</h3>
  <button
    hx-delete="/admin/users/123"
    hx-confirm="Delete user judge1@test.com? This cannot be undone."
    hx-target="body"
    class="secondary"
  >
    Delete User
  </button>
  <small>This action cannot be undone</small>
</section>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through all form fields → Update button → Cancel button → Delete button
  - Arrow keys for radio buttons
  - Space to toggle checkbox and radio buttons
- **Screen Reader Announcements:**
  - Form pre-filled announced: "Editing user judge1@test.com"
  - Email validation announced: "Email is available"
  - Status toggle announced: "User status set to active/inactive"
  - Update announced: "Updating user..."
  - Success announced: "User updated successfully"
  - Delete confirmation announced as modal
- **ARIA Labels:**
  - Email validation: `role="status"`, `aria-live="polite"`
  - Status checkbox: `aria-describedby="status-help"`
  - Submit button: `aria-busy="true"` during submission
  - Delete button: `aria-label="Delete user judge1@test.com permanently"`
  - Danger zone: `role="region"`, `aria-label="Danger zone"`
- **Focus Management:**
  - Focus moves to first error field if validation fails
  - Focus moves to success message after update
  - Focus returns to users list after delete
  - Delete button has visual warning styling

**Validation States:**
- **Loading Form:** Skeleton inputs shown while fetching user data
- **Form Loaded:** All fields pre-filled with current values
- **Empty Email:** "Email address is required" (on submit)
- **Invalid Email Format:** "Please enter a valid email address" (on blur)
- **Email Already Exists:** "This email is already registered" (async check)
- **Email Unchanged:** No validation message (skip uniqueness check)
- **No Role Selected:** "Please select a role" (on submit)
- **Status Active:** Checkbox checked, no warning
- **Status Inactive:** Checkbox unchecked, "User cannot sign in" warning
- **Submitting:** Button shows spinner, text changes to "Updating...", form disabled
- **Success:** Redirect to users list with flash message "User updated: judge1@test.com"
- **Backend Error:** Red banner with error message, form remains editable
- **Delete Confirmation:** Modal with "Delete user judge1@test.com?" prompt
- **Deleting:** Modal shows spinner, "Deleting..."
- **Delete Success:** Redirect to users list with "User deleted" message
- **Delete Error:** "Failed to delete user: [reason]" message

---

## Section 8: Tournament Management Pages

### 10. Tournament List

**Route:** `/tournaments`
**Permission:** Staff, Admin
**Purpose:** View all tournaments, filter by status, create/edit tournaments

**Components:**
- Tournament cards with status badges
- Filter by status (Draft, Active, Completed)
- Search by name
- Create tournament button
- Edit/view actions per tournament
- Tournament metadata (date, categories, phase)

**User Interactions:**
1. View tournaments list → See all tournaments with status and metadata
2. Filter by status → Select status filter, list updates
3. Search by name → Type in search field, list filters in real-time
4. Create tournament → Navigate to create tournament form
5. View tournament → Navigate to tournament detail page
6. Edit tournament → Navigate to edit tournament form

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────────────┐
│ ← Back                    Tournaments                              │
├────────────────────────────────────────────────────────────────────┤
│ [+ Create Tournament]                                              │
│                                                                    │
│ Filter: [All Status ▼]     Search: [____________] 🔍              │
│                                                                    │
│ ┌──────────────────────┬──────────────────────┬──────────────────┐│
│ │ Summer Battle 2024   │ Winter Showdown 2024 │ Spring Jam 2024  ││
│ │ [Active] [Pools]     │ [Active] [Preselect] │ [Completed]      ││
│ │                      │                      │                  ││
│ │ Created: 2024-06-01  │ Created: 2024-01-15  │ Created:         ││
│ │ Categories: 3        │ Categories: 2        │ 2024-03-10       ││
│ │ • Hip Hop 1v1        │ • Breaking Solo      │ Categories: 4    ││
│ │ • Breaking Duo       │ • Krump 1v1          │ • Hip Hop 1v1    ││
│ │ • Krump 1v1          │                      │ • Breaking Duo   ││
│ │                      │ Phase: Preselection  │ • Locking 1v1    ││
│ │ Phase: Pools         │ 25 performers        │ • Popping 1v1    ││
│ │ 32 performers        │                      │                  ││
│ │                      │ [View Details]       │ Winner:          ││
│ │ [View Details]       │ [Edit Tournament]    │ B-Boy Storm      ││
│ │ [Edit Tournament]    │                      │                  ││
│ │                      │                      │ [View Details]   ││
│ └──────────────────────┴──────────────────────┴──────────────────┘│
│                                                                    │
│ ┌──────────────────────┬──────────────────────┬──────────────────┐│
│ │ Fall Classic 2024    │ New Year Battle 2025 │ (Empty slot)     ││
│ │ [Draft]              │ [Draft]              │                  ││
│ │                      │                      │                  ││
│ │ Created: 2024-08-20  │ Created: 2024-11-01  │                  ││
│ │ Categories: 0        │ Categories: 1        │                  ││
│ │                      │ • Hip Hop 1v1        │                  ││
│ │ Phase: Registration  │                      │                  ││
│ │ 0 performers         │ Phase: Registration  │                  ││
│ │                      │ 3 performers         │                  ││
│ │ [View Details]       │                      │                  ││
│ │ [Edit Tournament]    │ [View Details]       │                  ││
│ │                      │ [Edit Tournament]    │                  ││
│ └──────────────────────┴──────────────────────┴──────────────────┘│
│                                                                    │
│ Showing 5 of 8 tournaments                     [Previous] [Next]  │
└────────────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Tournaments                │
├────────────────────────────┤
│ [+ Create Tournament]      │
│                            │
│ Filter: [All Status ▼]     │
│ Search: [____________] 🔍  │
│                            │
│ ┌────────────────────────┐ │
│ │ Summer Battle 2024     │ │
│ │ [Active] [Pools]       │ │
│ │                        │ │
│ │ Created: 2024-06-01    │ │
│ │ Categories: 3          │ │
│ │ • Hip Hop 1v1          │ │
│ │ • Breaking Duo         │ │
│ │ • Krump 1v1            │ │
│ │                        │ │
│ │ Phase: Pools           │ │
│ │ 32 performers          │ │
│ │                        │ │
│ │ [View Details]         │ │
│ │ [Edit Tournament]      │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Winter Showdown 2024   │ │
│ │ [Active] [Preselect]   │ │
│ │                        │ │
│ │ Created: 2024-01-15    │ │
│ │ Categories: 2          │ │
│ │ • Breaking Solo        │ │
│ │ • Krump 1v1            │ │
│ │                        │ │
│ │ Phase: Preselection    │ │
│ │ 25 performers          │ │
│ │                        │ │
│ │ [View Details]         │ │
│ │ [Edit Tournament]      │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Spring Jam 2024        │ │
│ │ [Completed]            │ │
│ │                        │ │
│ │ Created: 2024-03-10    │ │
│ │ Categories: 4          │ │
│ │ Winner: B-Boy Storm    │ │
│ │                        │ │
│ │ [View Details]         │ │
│ └────────────────────────┘ │
│                            │
│ 5 of 8 tournaments         │
│ [Previous] [Next]          │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Search field with live filtering -->
<input
  type="search"
  name="search"
  placeholder="Search tournaments..."
  hx-get="/tournaments/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#tournaments-grid"
  hx-indicator="#search-spinner"
>
<span id="search-spinner" class="htmx-indicator">🔍</span>

<!-- Status filter dropdown -->
<select
  name="status"
  hx-get="/tournaments"
  hx-trigger="change"
  hx-target="#tournaments-grid"
>
  <option value="">All Status</option>
  <option value="draft">Draft</option>
  <option value="active">Active</option>
  <option value="completed">Completed</option>
</select>

<!-- Tournament grid with cards -->
<div id="tournaments-grid" class="grid">
  <!-- Tournament cards loaded here -->
  <article class="tournament-card">
    <header>
      <h3>Summer Battle 2024</h3>
      <div class="badges">
        <span class="badge active">Active</span>
        <span class="badge phase">Pools</span>
      </div>
    </header>
    <p>Created: 2024-06-01</p>
    <p>Categories: 3</p>
    <ul>
      <li>Hip Hop 1v1</li>
      <li>Breaking Duo</li>
      <li>Krump 1v1</li>
    </ul>
    <footer>
      <a href="/tournaments/123" role="button">View Details</a>
      <a href="/tournaments/123/edit" role="button" class="secondary">Edit</a>
    </footer>
  </article>
</div>

<!-- Pagination -->
<nav aria-label="Tournaments pagination">
  <ul>
    <li>
      <a
        href="#"
        hx-get="/tournaments?page=1"
        hx-target="#tournaments-grid"
      >
        Previous
      </a>
    </li>
    <li>
      <a
        href="#"
        hx-get="/tournaments?page=2"
        hx-target="#tournaments-grid"
      >
        Next
      </a>
    </li>
  </ul>
</nav>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through Create button → Filter dropdown → Search field → Tournament cards → View/Edit buttons
  - Enter/Space to activate buttons and links
  - Arrow keys in filter dropdown
- **Screen Reader Announcements:**
  - Search results announced: "3 tournaments found for 'summer'"
  - Filter changes announced: "Filtered to Active status, 2 tournaments found"
  - Tournament count announced: "Showing 5 of 8 tournaments"
  - Page changes announced: "Page 2 of 3"
- **ARIA Labels:**
  - Create button: `aria-label="Create new tournament"`
  - Filter dropdown: `aria-label="Filter tournaments by status"`
  - Search input: `aria-label="Search tournaments by name"`
  - Tournament cards: `role="article"` with `aria-label="Tournament: Summer Battle 2024"`
  - View button: `aria-label="View details for Summer Battle 2024"`
  - Edit button: `aria-label="Edit Summer Battle 2024"`
  - Pagination: `aria-label="Tournaments pagination"`
- **Focus Management:**
  - Focus moves to filtered results after filter change
  - Focus preserved on current card after HTMX update
  - Focus moves to first card on page change

**Validation States:**
- **Loading Initial List:** Skeleton cards shown (6 placeholder cards)
- **Empty List:** "No tournaments yet. Create your first tournament!"
- **Empty Search:** "No tournaments found for 'xyz'"
- **Empty Filter:** "No tournaments with status 'Draft'"
- **Searching:** Spinner icon in search field
- **Filtering:** Brief loading indicator on grid
- **Active Tournament:** Green "Active" badge with phase indicator
- **Draft Tournament:** Gray "Draft" badge, registration phase
- **Completed Tournament:** Blue "Completed" badge with winner info
- **First Page:** Previous button disabled
- **Last Page:** Next button disabled
- **Loading Page:** Skeleton cards during pagination

---

### 11. Create Tournament Form

**Route:** `/tournaments/create`
**Permission:** Staff, Admin
**Purpose:** Create new tournament with name and initial settings

**Components:**
- Tournament name input with validation
- Date picker (optional, for display)
- Description textarea (optional)
- Submit button with loading state
- Cancel button

**User Interactions:**
1. Enter tournament name → Live validation checks uniqueness
2. Select date (optional) → Date picker for tournament date
3. Enter description (optional) → Multi-line text for tournament info
4. Submit form → Create tournament, redirect to detail page
5. Cancel → Return to tournaments list

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Tournaments     Create Tournament                │
├────────────────────────────────────────────────────────────┤
│ Create a new tournament                                    │
│                                                            │
│ Tournament Name: *                                         │
│ [_____________________________________]                    │
│ Example: "Summer Battle 2024", "Winter Showdown"          │
│                                                            │
│ Date: (optional)                                           │
│ [____/____/________] 📅                                    │
│ Tournament date for display purposes                       │
│                                                            │
│ Description: (optional)                                    │
│ [_____________________________________]                    │
│ [_____________________________________]                    │
│ [_____________________________________]                    │
│ Brief description of the tournament                        │
│                                                            │
│ ───────────────────────────────────────                   │
│                                                            │
│ ℹ️ After creating the tournament, you can:                │
│ • Add categories with battle formats                       │
│ • Register dancers                                         │
│ • Manage tournament phases                                 │
│                                                            │
│ ───────────────────────────────────────                   │
│                                                            │
│ [Create Tournament]  [Cancel]                              │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Tournaments      │
│ Create Tournament          │
├────────────────────────────┤
│ Create a new tournament    │
│                            │
│ Tournament Name: *         │
│ [____________________]     │
│ Example: "Summer Battle    │
│ 2024", "Winter Showdown"   │
│                            │
│ Date: (optional)           │
│ [____/____/________] 📅    │
│ Tournament date for        │
│ display purposes           │
│                            │
│ Description: (optional)    │
│ [____________________]     │
│ [____________________]     │
│ [____________________]     │
│ Brief description of       │
│ the tournament             │
│                            │
│ ──────────────────────     │
│                            │
│ ℹ️ After creating:         │
│ • Add categories           │
│ • Register dancers         │
│ • Manage phases            │
│                            │
│ ──────────────────────     │
│                            │
│ [Create Tournament]        │
│ [Cancel]                   │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Create tournament form -->
<form
  hx-post="/tournaments"
  hx-target="#form-messages"
  hx-swap="innerHTML"
  hx-indicator="#submit-btn"
>
  <label for="name">Tournament Name: *</label>
  <input
    type="text"
    id="name"
    name="name"
    required
    hx-post="/tournaments/check-name"
    hx-trigger="blur"
    hx-target="#name-validation"
    hx-swap="innerHTML"
    placeholder="Summer Battle 2024"
  >
  <div id="name-validation" role="status" aria-live="polite"></div>
  <small>Example: "Summer Battle 2024", "Winter Showdown"</small>

  <label for="date">Date: (optional)</label>
  <input
    type="date"
    id="date"
    name="date"
  >
  <small>Tournament date for display purposes</small>

  <label for="description">Description: (optional)</label>
  <textarea
    id="description"
    name="description"
    rows="3"
    placeholder="Brief description of the tournament"
  ></textarea>

  <div class="info-box">
    <p>ℹ️ After creating the tournament, you can:</p>
    <ul>
      <li>Add categories with battle formats</li>
      <li>Register dancers</li>
      <li>Manage tournament phases</li>
    </ul>
  </div>

  <button type="submit" id="submit-btn">Create Tournament</button>
  <a href="/tournaments" role="button" class="secondary">Cancel</a>
</form>

<div id="form-messages" role="status" aria-live="polite"></div>

<!-- Success response redirects to tournament detail page -->
<!-- Error response shows in #form-messages -->
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through name field → date picker → description textarea → Create button → Cancel button
  - Enter to submit from name field
  - Arrow keys for date picker navigation
- **Screen Reader Announcements:**
  - Name validation announced: "Name is available" or "Name already exists"
  - Date selection announced: "Tournament date set to June 1, 2024"
  - Form submission announced: "Creating tournament..."
  - Success announced: "Tournament created successfully"
  - Error announced: "Error: [message]"
- **ARIA Labels:**
  - Name input: `aria-required="true"`, `aria-describedby="name-help"`
  - Name validation: `role="status"`, `aria-live="polite"`
  - Date picker: `aria-label="Tournament date (optional)"`
  - Description: `aria-label="Tournament description (optional)"`
  - Submit button: `aria-busy="true"` during submission
  - Form messages: `role="status"` for success, `role="alert"` for errors
  - Info box: `role="note"`, `aria-label="Next steps information"`
- **Focus Management:**
  - Focus moves to first error field if validation fails
  - Focus moves to success message after creation
  - Focus returns to form if backend error occurs

**Validation States:**
- **Empty Name:** "Tournament name is required" (on submit)
- **Name Too Short:** "Name is required" (on blur)
- **Name Already Exists:** "Tournament name already exists" (async check on blur)
- **Name Available:** Green checkmark icon, "Name is available"
- **Invalid Date:** "Please enter a valid date" (if date format incorrect)
- **Future Date:** Green checkmark, valid date
- **Past Date:** Warning icon, "Tournament date is in the past" (allowed but warned)
- **Description Too Long:** "Description cannot exceed 500 characters" (character counter)
- **Submitting:** Button shows spinner, text changes to "Creating...", form disabled
- **Success:** Redirect to tournament detail page with flash message "Tournament created: Summer Battle 2024"
- **Backend Error:** Red banner with error message, form remains editable
- **Network Error:** "Connection failed. Check your internet and try again."

---

## Section 9: Dancer Management Pages

### 12. Dancers List

**Route:** `/dancers`
**Permission:** Staff, Admin
**Purpose:** View all dancers, search, create/edit dancers

**Components:**
- Dancers table/cards with blaze name and email
- Search by name, blaze, or email
- Create dancer button
- Edit/view actions per dancer
- Infinite scroll for loading more results (10 initial, load more on scroll)

**User Interactions:**
1. View dancers list → See all dancers with blaze name and email
2. Search dancers → Type in search field, list filters in real-time
3. Create dancer → Navigate to create dancer form
4. View dancer profile → Navigate to dancer profile page
5. Edit dancer → Navigate to edit dancer form

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────────────┐
│ ← Back                    Dancers                                  │
├────────────────────────────────────────────────────────────────────┤
│ [+ Create Dancer]                                                  │
│                                                                    │
│ Search: [_______________________________] 🔍                       │
│ Search by name, blaze, or email                                   │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐│
│ │ Blaze Name ▲▼   │ Real Name ▲▼  │ Email ▲▼         │ Actions  ││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ B-Boy Storm     │ John Doe      │ storm@ex.com     │ [Profile]││
│ │                 │               │                  │ [Edit]   ││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ Crazy Legs      │ Sarah Smith   │ legs@ex.com      │ [Profile]││
│ │                 │               │                  │ [Edit]   ││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ B-Girl Fierce   │ Maria Garcia  │ fierce@ex.com    │ [Profile]││
│ │                 │               │                  │ [Edit]   ││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ The Kid         │ Mike Johnson  │ kid@ex.com       │ [Profile]││
│ │                 │               │                  │ [Edit]   ││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ Breakmaster     │ Alex Chen     │ master@ex.com    │ [Profile]││
│ │                 │               │                  │ [Edit]   ││
│ ├────────────────────────────────────────────────────────────────┤│
│ │ DJ Spin         │ Lisa Wong     │ spin@ex.com      │ [Profile]││
│ │                 │               │                  │ [Edit]   ││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                    │
│ Showing 10 of 24 dancers                                          │
│ ↓ Scroll for more                                                 │
└────────────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Dancers                    │
├────────────────────────────┤
│ [+ Create Dancer]          │
│                            │
│ Search: [____________] 🔍  │
│ By name, blaze, or email   │
│                            │
│ ┌────────────────────────┐ │
│ │ 🎭 B-Boy Storm         │ │
│ │ John Doe               │ │
│ │ storm@example.com      │ │
│ │ [Profile] [Edit]       │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ 🎭 Crazy Legs          │ │
│ │ Sarah Smith            │ │
│ │ legs@example.com       │ │
│ │ [Profile] [Edit]       │ │
│ └────────────────────────┘ │
│                            │
│ ... (more cards)           │
│                            │
│ 10 of 24 dancers           │
│ ↓ Scroll for more          │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Search field with live filtering -->
<input
  type="search"
  name="search"
  placeholder="Search by name, blaze, or email..."
  hx-get="/dancers/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#dancers-table"
  hx-indicator="#search-spinner"
>
<span id="search-spinner" class="htmx-indicator">🔍</span>

<!-- Dancers table with sortable columns -->
<table id="dancers-table">
  <thead>
    <tr>
      <th>
        <a
          href="#"
          hx-get="/dancers?sort=blaze_name&order=asc"
          hx-target="#dancers-table"
          hx-swap="outerHTML"
        >
          Blaze Name ▲▼
        </a>
      </th>
      <th>
        <a
          href="#"
          hx-get="/dancers?sort=real_name&order=asc"
          hx-target="#dancers-table"
          hx-swap="outerHTML"
        >
          Real Name ▲▼
        </a>
      </th>
      <th>
        <a
          href="#"
          hx-get="/dancers?sort=email&order=asc"
          hx-target="#dancers-table"
          hx-swap="outerHTML"
        >
          Email ▲▼
        </a>
      </th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>B-Boy Storm</td>
      <td>John Doe</td>
      <td>storm@example.com</td>
      <td>
        <a href="/dancers/123" role="button" class="secondary">Profile</a>
        <a href="/dancers/123/edit" role="button" class="secondary">Edit</a>
      </td>
    </tr>
    <!-- More rows... -->
  </tbody>
</table>

<!-- Infinite scroll trigger (loads more when visible) -->
<div
  id="load-more-trigger"
  hx-get="/dancers?offset=10&limit=10"
  hx-trigger="revealed"
  hx-target="#dancers-table tbody"
  hx-swap="beforeend"
  hx-indicator="#loading-more"
>
  <span id="loading-more" class="htmx-indicator">Loading more dancers...</span>
</div>

<p class="dancer-count">Showing <span id="current-count">10</span> of <span id="total-count">24</span> dancers</p>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through Create button → Search field → Table rows → Profile/Edit buttons
  - Arrow keys to navigate table cells
  - Enter/Space to activate sort headers, buttons
- **Screen Reader Announcements:**
  - Table: `role="table"` with `aria-label="Dancers list"`
  - Row count announced: "Showing 10 of 24 dancers"
  - Search results announced: "3 dancers found for 'storm'"
  - Sort changes announced: "Sorted by blaze name, ascending"
  - More loaded announced: "10 more dancers loaded"
- **ARIA Labels:**
  - Create button: `aria-label="Create new dancer"`
  - Search input: `aria-label="Search dancers by name, blaze, or email"`
  - Sort headers: `aria-sort="ascending"` or `aria-sort="descending"`
  - Profile button: `aria-label="View profile for B-Boy Storm"`
  - Edit button: `aria-label="Edit B-Boy Storm"`
  - Loading indicator: `aria-busy="true"` during load
- **Focus Management:**
  - Focus moves to search results after filtering
  - Focus preserved on sort header after table update
  - Focus preserved during infinite scroll (no jump)

**Validation States:**
- **Loading Initial List:** Skeleton rows shown (10 placeholder rows)
- **Empty List:** "No dancers yet. Create your first dancer!"
- **Empty Search:** "No dancers found for 'xyz'"
- **Searching:** Spinner icon in search field
- **Sorting:** Arrow icon changes (▲ for asc, ▼ for desc)
- **Loading More:** "Loading more dancers..." indicator at bottom
- **All Loaded:** "All 24 dancers loaded" (no more trigger)

---

### 13. Create Dancer Form

**Route:** `/dancers/create`
**Permission:** Staff, Admin
**Purpose:** Create new dancer with blaze name, real name, and email

**Components:**
- Blaze name input (required, unique)
- Real name input (required)
- Email input (required, unique, validated)
- Submit button with loading state
- Cancel button

**User Interactions:**
1. Enter blaze name → Live validation checks uniqueness
2. Enter real name → Required field for identification
3. Enter email → Live validation checks format and uniqueness
4. Submit form → Create dancer, redirect to dancers list
5. Cancel → Return to dancers list

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Dancers         Create Dancer                    │
├────────────────────────────────────────────────────────────┤
│ Add a new dancer to the system                             │
│                                                            │
│ Blaze Name: *                                              │
│ [_____________________________________]                    │
│ Stage name / Artist name (e.g., "B-Boy Storm")            │
│                                                            │
│ Real Name: *                                               │
│ [_____________________________________]                    │
│ Full legal name (e.g., "John Doe")                        │
│                                                            │
│ Email: *                                                   │
│ [_____________________________________]                    │
│ Contact email address                                      │
│                                                            │
│ ───────────────────────────────────────                   │
│                                                            │
│ [Create Dancer]  [Cancel]                                  │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Dancers          │
│ Create Dancer              │
├────────────────────────────┤
│ Add a new dancer           │
│                            │
│ Blaze Name: *              │
│ [____________________]     │
│ Stage name / Artist name   │
│ (e.g., "B-Boy Storm")      │
│                            │
│ Real Name: *               │
│ [____________________]     │
│ Full legal name            │
│ (e.g., "John Doe")         │
│                            │
│ Email: *                   │
│ [____________________]     │
│ Contact email address      │
│                            │
│ ──────────────────────     │
│                            │
│ [Create Dancer]            │
│ [Cancel]                   │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Create dancer form -->
<form
  hx-post="/dancers"
  hx-target="#form-messages"
  hx-swap="innerHTML"
  hx-indicator="#submit-btn"
>
  <label for="blaze_name">Blaze Name: *</label>
  <input
    type="text"
    id="blaze_name"
    name="blaze_name"
    required
    hx-post="/dancers/check-blaze"
    hx-trigger="blur"
    hx-target="#blaze-validation"
    hx-swap="innerHTML"
    placeholder="B-Boy Storm"
  >
  <div id="blaze-validation" role="status" aria-live="polite"></div>
  <small>Stage name / Artist name (e.g., "B-Boy Storm")</small>

  <label for="real_name">Real Name: *</label>
  <input
    type="text"
    id="real_name"
    name="real_name"
    required
    placeholder="John Doe"
  >
  <small>Full legal name (e.g., "John Doe")</small>

  <label for="email">Email: *</label>
  <input
    type="email"
    id="email"
    name="email"
    required
    hx-post="/dancers/check-email"
    hx-trigger="blur"
    hx-target="#email-validation"
    hx-swap="innerHTML"
    placeholder="storm@example.com"
  >
  <div id="email-validation" role="status" aria-live="polite"></div>
  <small>Contact email address</small>

  <button type="submit" id="submit-btn">Create Dancer</button>
  <a href="/dancers" role="button" class="secondary">Cancel</a>
</form>

<div id="form-messages" role="status" aria-live="polite"></div>

<!-- Success response redirects to dancers list -->
<!-- Error response shows in #form-messages -->
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through blaze name → real name → email → Create button → Cancel button
  - Enter to submit from any field
- **Screen Reader Announcements:**
  - Blaze validation announced: "Blaze name is available" or "Already exists"
  - Email validation announced: "Email is available" or "Already registered"
  - Form submission announced: "Creating dancer..."
  - Success announced: "Dancer created successfully"
  - Error announced: "Error: [message]"
- **ARIA Labels:**
  - Blaze input: `aria-required="true"`, `aria-describedby="blaze-help"`
  - Real name input: `aria-required="true"`, `aria-describedby="name-help"`
  - Email input: `aria-required="true"`, `aria-describedby="email-help"`
  - Validation divs: `role="status"`, `aria-live="polite"`
  - Submit button: `aria-busy="true"` during submission
  - Form messages: `role="status"` for success, `role="alert"` for errors
- **Focus Management:**
  - Focus moves to first error field if validation fails
  - Focus moves to success message after creation
  - Focus returns to form if backend error occurs

**Validation States:**
- **Empty Blaze Name:** "Blaze name is required" (on submit)
- **Blaze Name Empty:** "Blaze name is required" (on blur)
- **Blaze Name Already Exists:** "This blaze name is already taken" (async check)
- **Blaze Name Available:** Green checkmark icon, "Blaze name is available"
- **Empty Real Name:** "Real name is required" (on submit)
- **Empty Email:** "Email is required" (on submit)
- **Invalid Email Format:** "Please enter a valid email address" (on blur)
- **Email Already Exists:** "This email is already registered" (async check)
- **Email Available:** Green checkmark icon, "Email is available"
- **Submitting:** Button shows spinner, text changes to "Creating...", form disabled
- **Success:** Redirect to dancers list with flash message "Dancer created: B-Boy Storm"
- **Backend Error:** Red banner with error message, form remains editable
- **Network Error:** "Connection failed. Check your internet and try again."

---

### 14. Edit Dancer Form

**Route:** `/dancers/{dancer_id}/edit`
**Permission:** Staff, Admin
**Purpose:** Edit existing dancer's blaze name, real name, or email

**Components:**
- Blaze name input (pre-filled, unique)
- Real name input (pre-filled)
- Email input (pre-filled, unique, validated)
- Submit button with loading state
- Cancel button
- Delete dancer button (danger zone)

**User Interactions:**
1. View pre-filled form → See current dancer data
2. Edit blaze name → Live validation checks uniqueness
3. Edit real name → Update legal name
4. Edit email → Live validation checks format and uniqueness
5. Submit form → Update dancer, show success message
6. Delete dancer → Confirm modal, then delete

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Dancers         Edit Dancer                      │
├────────────────────────────────────────────────────────────┤
│ Editing: B-Boy Storm                                       │
│                                                            │
│ Blaze Name: *                                              │
│ [B-Boy Storm__________________________]                    │
│ Stage name / Artist name                                   │
│                                                            │
│ Real Name: *                                               │
│ [John Doe_________________________________]                │
│ Full legal name                                            │
│                                                            │
│ Email: *                                                   │
│ [storm@example.com____________________]                    │
│ Contact email address                                      │
│                                                            │
│ ───────────────────────────────────────                   │
│                                                            │
│ [Update Dancer]  [Cancel]                                  │
│                                                            │
│ ───────────────────────────────────────                   │
│ Danger Zone                                                │
│                                                            │
│ [Delete Dancer]                                            │
│ Cannot delete if registered to an active tournament.       │
│ This action cannot be undone.                              │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Dancers          │
│ Edit Dancer                │
├────────────────────────────┤
│ Editing: B-Boy Storm       │
│                            │
│ Blaze Name: *              │
│ [B-Boy Storm_________]     │
│ Stage name / Artist name   │
│                            │
│ Real Name: *               │
│ [John Doe____________]     │
│ Full legal name            │
│                            │
│ Email: *                   │
│ [storm@example.com___]     │
│ Contact email address      │
│                            │
│ ──────────────────────     │
│                            │
│ [Update Dancer]            │
│ [Cancel]                   │
│                            │
│ ──────────────────────     │
│ Danger Zone                │
│                            │
│ [Delete Dancer]            │
│ Cannot delete if in        │
│ active tournament.         │
│ Cannot be undone.          │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Edit dancer form -->
<form
  hx-put="/dancers/123"
  hx-target="#form-messages"
  hx-swap="innerHTML"
  hx-indicator="#submit-btn"
>
  <label for="blaze_name">Blaze Name: *</label>
  <input
    type="text"
    id="blaze_name"
    name="blaze_name"
    value="B-Boy Storm"
    required
    hx-post="/dancers/check-blaze?exclude=123"
    hx-trigger="blur"
    hx-target="#blaze-validation"
  >
  <div id="blaze-validation" role="status" aria-live="polite"></div>

  <label for="real_name">Real Name: *</label>
  <input
    type="text"
    id="real_name"
    name="real_name"
    value="John Doe"
    required
  >

  <label for="email">Email: *</label>
  <input
    type="email"
    id="email"
    name="email"
    value="storm@example.com"
    required
    hx-post="/dancers/check-email?exclude=123"
    hx-trigger="blur"
    hx-target="#email-validation"
  >
  <div id="email-validation" role="status" aria-live="polite"></div>

  <button type="submit" id="submit-btn">Update Dancer</button>
  <a href="/dancers" role="button" class="secondary">Cancel</a>
</form>

<div id="form-messages" role="status" aria-live="polite"></div>

<!-- Delete button in danger zone -->
<section class="danger-zone">
  <h3>Danger Zone</h3>
  <button
    hx-delete="/dancers/123"
    hx-confirm="Delete dancer B-Boy Storm? This cannot be undone."
    hx-target="body"
    class="secondary"
  >
    Delete Dancer
  </button>
  <small>Cannot delete if registered to an active tournament. This action cannot be undone.</small>
</section>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through all form fields → Update button → Cancel button → Delete button
  - Enter to submit from any field
- **Screen Reader Announcements:**
  - Form pre-filled announced: "Editing dancer B-Boy Storm"
  - Blaze validation announced: "Blaze name is available"
  - Email validation announced: "Email is available"
  - Update announced: "Updating dancer..."
  - Success announced: "Dancer updated successfully"
  - Delete confirmation announced as modal
- **ARIA Labels:**
  - Validation divs: `role="status"`, `aria-live="polite"`
  - Submit button: `aria-busy="true"` during submission
  - Delete button: `aria-label="Delete dancer B-Boy Storm permanently"`
  - Danger zone: `role="region"`, `aria-label="Danger zone"`
- **Focus Management:**
  - Focus moves to first error field if validation fails
  - Focus moves to success message after update
  - Focus returns to dancers list after delete
  - Delete button has visual warning styling

**Validation States:**
- **Loading Form:** Skeleton inputs shown while fetching dancer data
- **Form Loaded:** All fields pre-filled with current values
- **Empty Blaze Name:** "Blaze name is required" (on submit)
- **Blaze Name Already Exists:** "This blaze name is already taken" (async check)
- **Blaze Name Unchanged:** No validation message (skip uniqueness check)
- **Empty Real Name:** "Real name is required" (on submit)
- **Empty Email:** "Email is required" (on submit)
- **Invalid Email Format:** "Please enter a valid email address" (on blur)
- **Email Already Exists:** "This email is already registered" (async check)
- **Email Unchanged:** No validation message (skip uniqueness check)
- **Submitting:** Button shows spinner, text changes to "Updating...", form disabled
- **Success:** Redirect to dancers list with flash message "Dancer updated: B-Boy Storm"
- **Backend Error:** Red banner with error message, form remains editable
- **Delete Confirmation:** Modal with "Delete dancer B-Boy Storm?" prompt
- **Deleting:** Modal shows spinner, "Deleting..."
- **Delete Success:** Redirect to dancers list with "Dancer deleted" message
- **Delete Error:** "Failed to delete dancer: [reason]" (e.g., has active registrations)

---

### 15. Dancer Profile

**Route:** `/dancers/{dancer_id}`
**Permission:** Staff, Admin
**Purpose:** View dancer's complete profile and tournament history

**Components:**
- Dancer info card (blaze, real name, email)
- Tournament registrations list
- Edit dancer button
- Back to list button

**User Interactions:**
1. View dancer info → See blaze name, real name, email
2. View registrations → See all tournament categories registered
3. Edit dancer → Navigate to edit dancer form
4. Back to list → Return to dancers list

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Dancers         Dancer Profile                   │
├────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🎭 B-Boy Storm                          [Edit Dancer]  │ │
│ │                                                        │ │
│ │ Real Name: John Doe                                   │ │
│ │ Email: storm@example.com                              │ │
│ │ Created: 2024-01-15                                   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Tournament Registrations (3)                               │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Summer Battle 2024                                     │ │
│ │ Category: Hip Hop 1v1                                  │ │
│ │ Phase: Pools                                           │ │
│ │ Pool: A                                                │ │
│ │ Record: 3 wins, 1 loss                                 │ │
│ │ [View Tournament]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Winter Showdown 2024                                   │ │
│ │ Category: Breaking Solo                                │ │
│ │ Phase: Completed                                       │ │
│ │ Result: 1st Place 🏆                                    │ │
│ │ [View Tournament]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Spring Jam 2024                                        │ │
│ │ Category: Hip Hop 1v1                                  │ │
│ │ Phase: Completed                                       │ │
│ │ Result: 3rd Place 🥉                                    │ │
│ │ [View Tournament]                                      │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Dancers          │
│ Dancer Profile             │
├────────────────────────────┤
│ ┌────────────────────────┐ │
│ │ 🎭 B-Boy Storm         │ │
│ │                        │ │
│ │ Real Name:             │ │
│ │ John Doe               │ │
│ │                        │ │
│ │ Email:                 │ │
│ │ storm@example.com      │ │
│ │                        │ │
│ │ Created:               │ │
│ │ 2024-01-15             │ │
│ │                        │ │
│ │ [Edit Dancer]          │ │
│ └────────────────────────┘ │
│                            │
│ Tournament Registrations   │
│ (3)                        │
│                            │
│ ┌────────────────────────┐ │
│ │ Summer Battle 2024     │ │
│ │ Hip Hop 1v1            │ │
│ │ Phase: Pools           │ │
│ │ Pool: A                │ │
│ │ Record: 3W - 1L        │ │
│ │ [View Tournament]      │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Winter Showdown 2024   │ │
│ │ Breaking Solo          │ │
│ │ Phase: Completed       │ │
│ │ Result: 1st Place 🏆   │ │
│ │ [View Tournament]      │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ Spring Jam 2024        │ │
│ │ Hip Hop 1v1            │ │
│ │ Phase: Completed       │ │
│ │ Result: 3rd Place 🥉   │ │
│ │ [View Tournament]      │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Dancer profile (mostly static, minimal HTMX) -->
<article class="dancer-profile">
  <header>
    <h2>🎭 B-Boy Storm</h2>
    <a href="/dancers/123/edit" role="button">Edit Dancer</a>
  </header>

  <dl>
    <dt>Real Name:</dt>
    <dd>John Doe</dd>

    <dt>Email:</dt>
    <dd>storm@example.com</dd>

    <dt>Created:</dt>
    <dd>2024-01-15</dd>
  </dl>
</article>

<section>
  <h3>Tournament Registrations (3)</h3>

  <article class="registration-card">
    <h4>Summer Battle 2024</h4>
    <p>Category: Hip Hop 1v1</p>
    <p>Phase: Pools</p>
    <p>Pool: A</p>
    <a href="/tournaments/123" role="button">View Tournament</a>
  </article>

  <!-- More registration cards... -->
</section>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through Edit button → View Tournament buttons → Back button
  - Enter/Space to activate buttons
- **Screen Reader Announcements:**
  - Profile loaded announced: "Dancer profile for B-Boy Storm"
  - Registration count announced: "3 tournament registrations"
- **ARIA Labels:**
  - Profile section: `role="article"`, `aria-label="Dancer profile for B-Boy Storm"`
  - Edit button: `aria-label="Edit dancer B-Boy Storm"`
  - Registration cards: `role="article"` with tournament name
  - View buttons: `aria-label="View tournament Summer Battle 2024"`
- **Focus Management:**
  - Focus on Edit button when page loads
  - Focus preserved after navigation

**Validation States:**
- **Loading Profile:** Skeleton layout shown while fetching data
- **Profile Loaded:** All info displayed with proper formatting
- **No Registrations:** "No tournament registrations yet"
- **Active Registrations:** Green badge, current phase shown
- **Completed Registrations:** Blue badge, final placement shown
- **Loading Error:** "Failed to load dancer profile. Please try again."

---

## Section 10: Registration Pages (Enhanced)

### 16. Registration Workflow - Tournament Selection

**Route:** `/registration`
**Permission:** Staff, Admin
**Purpose:** Select tournament before registering dancers

**Components:**
- Tournament selection list (active tournaments only)
- Tournament status and phase badges
- Continue to registration button
- Back to overview button

**User Interactions:**
1. View active tournaments → See list of tournaments accepting registrations
2. Select tournament → Highlight selected tournament
3. Continue → Navigate to dancer registration page for selected tournament
4. Back → Return to overview

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back                    Register Dancer                  │
├────────────────────────────────────────────────────────────┤
│ Step 1: Select Tournament                                  │
│                                                            │
│ Choose a tournament to register dancers:                   │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ○ Summer Battle 2024                [Active] [Reg.]   │ │
│ │   Created: 2024-06-01                                  │ │
│ │   Categories: 3 (Hip Hop 1v1, Breaking Duo, Krump)   │ │
│ │   Phase: Registration                                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ○ Winter Showdown 2024              [Active] [Reg.]   │ │
│ │   Created: 2024-01-15                                  │ │
│ │   Categories: 2 (Breaking Solo, Krump 1v1)           │ │
│ │   Phase: Registration                                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ○ Fall Classic 2024                 [Draft]            │ │
│ │   Created: 2024-08-20                                  │ │
│ │   Categories: 0                                        │ │
│ │   Phase: Registration (no categories yet)              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Continue to Registration] (disabled until tournament      │
│ selected)                                                  │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Register Dancer            │
├────────────────────────────┤
│ Step 1: Select Tournament  │
│                            │
│ Choose a tournament:       │
│                            │
│ ┌────────────────────────┐ │
│ │ ○ Summer Battle 2024   │ │
│ │ [Active] [Reg.]        │ │
│ │                        │ │
│ │ Created: 2024-06-01    │ │
│ │ Categories: 3          │ │
│ │ Phase: Registration    │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ ○ Winter Showdown 2024 │ │
│ │ [Active] [Reg.]        │ │
│ │                        │ │
│ │ Created: 2024-01-15    │ │
│ │ Categories: 2          │ │
│ │ Phase: Registration    │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ ○ Fall Classic 2024    │ │
│ │ [Draft]                │ │
│ │                        │ │
│ │ Created: 2024-08-20    │ │
│ │ Categories: 0          │ │
│ │ Phase: Registration    │ │
│ └────────────────────────┘ │
│                            │
│ [Continue to Registration] │
│ (disabled until selected)  │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Tournament selection form -->
<form action="/registration/select-tournament" method="get">
  <fieldset>
    <legend>Choose a tournament to register dancers:</legend>

    <label class="tournament-option">
      <input
        type="radio"
        name="tournament_id"
        value="123"
        required
        hx-get="/registration/123/categories"
        hx-trigger="change"
        hx-target="#category-preview"
      >
      <div class="tournament-card">
        <h3>Summer Battle 2024</h3>
        <span class="badge active">Active</span>
        <span class="badge phase">Registration</span>
        <p>Created: 2024-06-01</p>
        <p>Categories: 3 (Hip Hop 1v1, Breaking Duo, Krump)</p>
        <p>Phase: Registration</p>
      </div>
    </label>

    <!-- More tournament options... -->
  </fieldset>

  <div id="category-preview" role="status" aria-live="polite">
    <!-- Category details loaded here when tournament selected -->
  </div>

  <button type="submit">Continue to Registration</button>
</form>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab to first radio button → Arrow keys to move between tournaments
  - Space to select tournament
  - Tab to Continue button
- **Screen Reader Announcements:**
  - Tournament count announced: "3 tournaments available for registration"
  - Selection announced: "Summer Battle 2024 selected"
  - Category preview announced when tournament selected
- **ARIA Labels:**
  - Fieldset: `<legend>` provides group label
  - Radio buttons: `aria-describedby` pointing to tournament details
  - Continue button: `aria-disabled="true"` when no selection
  - Category preview: `role="status"`, `aria-live="polite"`
- **Focus Management:**
  - Focus moves to Continue button after selection
  - Focus returns to radio group if validation fails

**Validation States:**
- **Loading Tournaments:** Skeleton cards shown
- **No Active Tournaments:** "No tournaments accepting registrations"
- **No Selection:** Continue button disabled, gray background
- **Tournament Selected:** Radio button checked, card highlighted with border
- **Draft Tournament Selected:** Warning message: "This tournament has no categories yet"
- **Category Preview Loading:** Spinner in preview area
- **Category Preview Loaded:** List of available categories displayed

---

## Section 11: Phase Management Pages

### 17. Phase Overview

**Route:** `/phases`
**Permission:** Staff, Admin, MC, Judge
**Purpose:** View current tournament phase and available actions

**Components:**
- Current tournament and phase display
- Phase progression timeline
- Available actions per role
- Quick stats (performers, categories, battles)

**User Interactions:**
1. View current phase → See phase name and status
2. View phase timeline → See progression through tournament phases
3. View available actions → See role-specific actions for current phase
4. Navigate to action → Click action button to perform phase-specific tasks

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back                    Tournament Phases                │
├────────────────────────────────────────────────────────────┤
│ Summer Battle 2024                                         │
│                                                            │
│ Phase Timeline:                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [✅ Registration] → [✅ Preselection] → [🔵 Pools]      │ │
│ │                                                        │ │
│ │ → [⚪ Finals] → [⚪ Completed]                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Current Phase: Pools                                       │
│ Started: 2024-06-15 14:30                                  │
│                                                            │
│ Quick Stats:                                               │
│ • Performers: 32                                           │
│ • Categories: 3                                            │
│ • Pools: 6                                                 │
│ • Battles: 24 (12 completed, 8 in progress, 4 pending)   │
│                                                            │
│ Available Actions:                                         │
│                                                            │
│ Staff & Admin:                                             │
│ • [View All Battles]                                       │
│ • [Advance to Finals] (available when all pools complete)  │
│                                                            │
│ MC:                                                        │
│ • [Start Next Battle]                                      │
│ • [View Battle Queue]                                      │
│                                                            │
│ Judge:                                                     │
│ • [Score Battles] (3 battles awaiting your scores)        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Tournament Phases          │
├────────────────────────────┤
│ Summer Battle 2024         │
│                            │
│ Phase Timeline:            │
│ ┌────────────────────────┐ │
│ │ ✅ Registration        │ │
│ │ ✅ Preselection        │ │
│ │ 🔵 Pools (Current)     │ │
│ │ ⚪ Finals               │ │
│ │ ⚪ Completed            │ │
│ └────────────────────────┘ │
│                            │
│ Current Phase: Pools       │
│ Started: 2024-06-15 14:30  │
│                            │
│ Quick Stats:               │
│ • Performers: 32           │
│ • Categories: 3            │
│ • Pools: 6                 │
│ • Battles: 24              │
│   (12 done, 8 active,      │
│    4 pending)              │
│                            │
│ Available Actions:         │
│                            │
│ Staff & Admin:             │
│ • [View All Battles]       │
│ • [Advance to Finals]      │
│   (when pools complete)    │
│                            │
│ MC:                        │
│ • [Start Next Battle]      │
│ • [View Battle Queue]      │
│                            │
│ Judge:                     │
│ • [Score Battles]          │
│   (3 awaiting scores)      │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Phase overview (mostly static, some HTMX for stats) -->
<article class="phase-overview">
  <header>
    <h2>Summer Battle 2024</h2>
  </header>

  <!-- Phase timeline -->
  <section class="phase-timeline">
    <div class="phase completed">
      <span class="icon">✅</span>
      <span>Registration</span>
    </div>
    <div class="arrow">→</div>
    <div class="phase completed">
      <span class="icon">✅</span>
      <span>Preselection</span>
    </div>
    <div class="arrow">→</div>
    <div class="phase current">
      <span class="icon">🔵</span>
      <span>Pools</span>
    </div>
    <div class="arrow">→</div>
    <div class="phase pending">
      <span class="icon">⚪</span>
      <span>Finals</span>
    </div>
    <div class="arrow">→</div>
    <div class="phase pending">
      <span class="icon">⚪</span>
      <span>Completed</span>
    </div>
  </section>

  <!-- Quick stats with live updates -->
  <section
    id="phase-stats"
    hx-get="/phases/stats"
    hx-trigger="every 30s"
    hx-swap="innerHTML"
  >
    <h3>Quick Stats:</h3>
    <ul>
      <li>Performers: 32</li>
      <li>Categories: 3</li>
      <li>Pools: 6</li>
      <li>Battles: 24 (12 completed, 8 in progress, 4 pending)</li>
    </ul>
  </section>

  <!-- Role-specific actions -->
  <section class="available-actions">
    <h3>Available Actions:</h3>
    <!-- Actions filtered by user role -->
  </section>
</article>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through action buttons
  - Enter/Space to activate actions
- **Screen Reader Announcements:**
  - Current phase announced: "Current phase: Pools"
  - Timeline announced: "Phase 3 of 5: Pools"
  - Stats updates announced with `aria-live="polite"`
  - Available actions count announced
- **ARIA Labels:**
  - Timeline: `role="list"` with phase steps as list items
  - Current phase: `aria-current="step"`
  - Stats section: `role="region"`, `aria-label="Tournament statistics"`
  - Action buttons: Descriptive labels with role requirements
- **Focus Management:**
  - Focus on first available action when page loads
  - Focus preserved after stats update

**Validation States:**
- **Loading Phase Data:** Skeleton layout shown
- **Phase Loaded:** All info displayed with current phase highlighted
- **Battles Pending:** Orange badge on Pools phase
- **Battles Complete:** Green checkmark on phase
- **Advance Available:** "Advance to Finals" button enabled (green)
- **Advance Unavailable:** Button disabled with reason (gray)
- **No Actions Available:** "No actions available in this phase"

---

### 18. Confirm Phase Advancement

**Route:** `/phases/confirm-advance`
**Permission:** Admin only
**Purpose:** Review validation checks before advancing to next phase

**Components:**
- Current and target phase display
- Validation checks list (pass/fail)
- Warning messages for potential issues
- Confirm/cancel buttons

**User Interactions:**
1. View validation checks → See all requirements for advancement
2. Review warnings → See any potential issues
3. Confirm advance → Proceed with phase advancement
4. Cancel → Return to phase overview

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back                    Confirm Phase Advancement        │
├────────────────────────────────────────────────────────────┤
│ Advance Tournament Phase                                   │
│                                                            │
│ Tournament: Summer Battle 2024                             │
│ Current Phase: Preselection                                │
│ Target Phase: Pools                                        │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ Validation Checks:                                         │
│                                                            │
│ ✅ All categories have minimum performers                  │
│    • Hip Hop 1v1: 8 performers (min: 5) ✓                │
│    • Breaking Duo: 6 performers (min: 5) ✓               │
│    • Krump 1v1: 10 performers (min: 5) ✓                 │
│                                                            │
│ ✅ All performers passed preselection                      │
│    • 24 performers selected                                │
│    • 8 performers eliminated                               │
│                                                            │
│ ✅ Pool assignments configured                             │
│    • 6 pools created                                       │
│    • Pool sizes: [4, 4, 4, 4, 4, 4] (balanced)            │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ This will:                                                 │
│ • Start pool battles for all categories                    │
│ • Allow MCs to begin battles                               │
│ • Staff/Admin will encode battle results (V1)              │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ [Confirm & Advance to Pools]  [Cancel]                     │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Confirm Advancement        │
├────────────────────────────┤
│ Advance Tournament Phase   │
│                            │
│ Tournament:                │
│ Summer Battle 2024         │
│                            │
│ Current: Preselection      │
│ Target: Pools              │
│                            │
│ ──────────────────────     │
│                            │
│ Validation Checks:         │
│                            │
│ ✅ All categories have     │
│ minimum performers         │
│ • Hip Hop 1v1: 8/5 ✓      │
│ • Breaking Duo: 6/5 ✓     │
│ • Krump 1v1: 10/5 ✓       │
│                            │
│ ✅ All performers passed   │
│ preselection               │
│ • 24 selected              │
│ • 8 eliminated             │
│                            │
│ ✅ Pool assignments        │
│ configured                 │
│ • 6 pools created          │
│ • Sizes: [4,4,4,4,4,4]     │
│                            │
│ ──────────────────────     │
│                            │
│ This will:                 │
│ • Start pool battles       │
│ • Allow MCs to begin       │
│ • Staff encodes results    │
│                            │
│ ──────────────────────     │
│                            │
│ [Confirm & Advance]        │
│ [Cancel]                   │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Confirmation form -->
<form
  hx-post="/phases/advance"
  hx-confirm="Are you sure you want to advance to Pools phase? This action cannot be undone."
  hx-target="body"
>
  <input type="hidden" name="tournament_id" value="123">
  <input type="hidden" name="target_phase" value="pools">

  <!-- Validation checks display -->
  <section class="validation-checks">
    <h3>Validation Checks:</h3>

    <div class="check passed">
      <span class="icon">✅</span>
      <div class="details">
        <strong>All categories have minimum performers</strong>
        <ul>
          <li>Hip Hop 1v1: 8 performers (min: 5) ✓</li>
          <li>Breaking Duo: 6 performers (min: 5) ✓</li>
          <li>Krump 1v1: 10 performers (min: 5) ✓</li>
        </ul>
      </div>
    </div>

    <div class="check passed">
      <span class="icon">✅</span>
      <div class="details">
        <strong>All performers passed preselection</strong>
        <p>24 performers selected, 8 eliminated</p>
      </div>
    </div>

  </section>

  <section class="impact">
    <h3>This will:</h3>
    <ul>
      <li>Start pool battles for all categories</li>
      <li>Allow MCs to begin battles</li>
      <li>Staff/Admin will encode battle results (V1)</li>
    </ul>
  </section>

  <button type="submit" class="primary">Confirm & Advance to Pools</button>
  <a href="/phases" role="button" class="secondary">Cancel</a>
</form>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through validation checks (focusable for screen readers)
  - Tab to Confirm button → Cancel button
- **Screen Reader Announcements:**
  - Validation summary announced: "3 checks passed, 1 warning"
  - Each check announced with pass/fail/warning status
  - Confirmation dialog announced as modal
- **ARIA Labels:**
  - Validation section: `role="region"`, `aria-label="Validation checks"`
  - Check items: `role="listitem"` with status
  - Warning checks: `role="alert"` for warnings
  - Confirm button: `aria-describedby` pointing to impact section
- **Focus Management:**
  - Focus on first validation check when page loads
  - Focus moves to Confirm button after review
  - Focus trapped in confirmation modal

**Validation States:**
- **Loading Checks:** Spinner with "Running validation checks..."
- **All Checks Pass:** All green checkmarks, Confirm button enabled
- **Checks Failed:** Red X icons, Confirm button disabled, error messages
- **Checks with Warnings:** Orange warning icons, Confirm button enabled with warnings
- **Advancing:** Button shows spinner, "Advancing to Pools..."
- **Success:** Redirect to phases overview with "Advanced to Pools phase"
- **Advancement Failed:** Red banner with error, "Failed to advance: [reason]"

---

### 19. Phase Validation Errors

**Route:** `/phases/validation-errors`
**Permission:** Admin only
**Purpose:** View detailed validation errors preventing phase advancement

**Components:**
- Error list grouped by category
- Suggested actions to resolve each error
- Links to relevant pages to fix issues
- Retry validation button

**User Interactions:**
1. View errors → See all validation failures
2. Review suggested actions → Understand how to fix each error
3. Navigate to fix → Click link to go to relevant page
4. Retry validation → Re-run checks after fixing issues

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Phases          Phase Validation Errors          │
├────────────────────────────────────────────────────────────┤
│ Cannot Advance: Preselection → Pools                       │
│                                                            │
│ Tournament: Summer Battle 2024                             │
│                                                            │
│ ❌ 1 error must be resolved before advancing               │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ Category: Breaking Duo                                     │
│                                                            │
│ ❌ Insufficient performers                                 │
│    • Current: 4 performers                                 │
│    • Required: 5 performers (minimum)                      │
│    • Formula: (2 pools × 2) + 1 = 5                       │
│                                                            │
│    Suggested actions:                                      │
│    • Register more dancers for this category               │
│    • Need more performers (minimum 5 for 2 pools)         │
│                                                            │
│    [View Category] [Register Dancers]                      │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ [Retry Validation]                                         │
└────────────────────────────────────────────────────────────┘
```

**Note:** Pool imbalance errors are not possible because the system automatically distributes performers evenly across pools (sizes differ by at most 1). Judge assignment errors are V2 only - in V1, Staff/Admin encodes battle results directly.

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Phases           │
│ Validation Errors          │
├────────────────────────────┤
│ Cannot Advance:            │
│ Preselection → Pools       │
│                            │
│ Tournament:                │
│ Summer Battle 2024         │
│                            │
│ ❌ 1 error to resolve      │
│                            │
│ ──────────────────────     │
│                            │
│ Breaking Duo               │
│                            │
│ ❌ Insufficient performers │
│ • Current: 4               │
│ • Required: 5              │
│ • Formula: (2×2) + 1 = 5  │
│                            │
│ Suggested actions:         │
│ • Register more dancers    │
│ • Reduce pools to 2        │
│   (min: 5 performers)      │
│                            │
│ [View Category]            │
│ [Register Dancers]         │
│                            │
│ ──────────────────────     │
│                            │
│ [Retry Validation]         │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Validation errors page -->
<article class="validation-errors">
  <header>
    <h2>Cannot Advance: Preselection → Pools</h2>
    <p>Tournament: Summer Battle 2024</p>
    <div class="error-summary" role="alert">
      ❌ 1 error must be resolved before advancing
    </div>
  </header>

  <!-- Error list -->
  <section class="error-list">
    <article class="error-item">
      <h3>Category: Breaking Duo</h3>
      <div class="error-details">
        <strong>❌ Insufficient performers</strong>
        <ul>
          <li>Current: 4 performers</li>
          <li>Required: 5 performers (minimum)</li>
          <li>Formula: (2 pools × 2) + 1 = 5</li>
        </ul>
        <div class="suggested-actions">
          <strong>Suggested actions:</strong>
          <ul>
            <li>Register more dancers for this category</li>
            <li>Reduce number of pools to 2 (min: 5 performers)</li>
          </ul>
        </div>
        <div class="action-buttons">
          <a href="/tournaments/123/categories/456" role="button">View Category</a>
          <a href="/registration?tournament=123&category=456" role="button">Register Dancers</a>
        </div>
      </div>
    </article>
  </section>

  <!-- Retry button with HTMX -->
  <button
    hx-post="/phases/validate"
    hx-target="body"
    hx-indicator="#retry-spinner"
  >
    Retry Validation
  </button>
  <span id="retry-spinner" class="htmx-indicator">Validating...</span>
</article>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through error items → action buttons → retry button
  - Enter/Space to activate buttons
- **Screen Reader Announcements:**
  - Error count announced: "1 error must be resolved" (or count)
  - Each error announced with category and type
  - Suggested actions announced as list
  - Retry result announced: "Validation passed" or "Still has errors"
- **ARIA Labels:**
  - Error summary: `role="alert"` for immediate announcement
  - Error list: `role="list"` with items
  - Action buttons: Descriptive labels with context
  - Retry button: `aria-busy="true"` during validation
- **Focus Management:**
  - Focus on first error when page loads
  - Focus moves to Retry button after reviewing errors
  - Focus returns to first remaining error after retry

**Validation States:**
- **Loading Errors:** Skeleton layout shown
- **Errors Loaded:** All errors displayed with details
- **Error Grouped by Category:** Related errors shown together
- **Critical Errors:** Red background, must be fixed
- **Warning Errors:** Orange background, can proceed with caution
- **Retrying Validation:** Button shows spinner, "Validating..."
- **Validation Pass:** Redirect to confirm advance page with "All checks passed!"
- **Validation Still Failing:** Refresh error list, highlight remaining errors
- **No Errors:** "All validation checks passed! Ready to advance."

---

## Section 12: Battle Management Pages

### 20. Battle Detail View

**Route:** `/battles/{battle_id}`
**Permission:** Staff, Admin, MC (Judge in V2)
**Purpose:** View battle details, performers, and results

> **V1 vs V2:** In V1, Staff/Admin encodes the winner. In V2, Judge scores are displayed.

**Components:**
- Battle metadata (number, pool, category)
- Performer cards with names
- Winner display (V1: encoded result, V2: judge scores)
- Battle status and result
- Actions based on role and status

**User Interactions:**
1. View battle info → See battle number, performers, pool
2. View result → See winner (V1) or individual judge scores (V2)
3. Start battle (MC only) → Change status to In Progress
4. Encode result (V1: Staff/Admin) → Navigate to encoding interface
5. Score battle (V2: Judge only) → Navigate to scoring interface

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back to Battles         Battle Detail                    │
├────────────────────────────────────────────────────────────┤
│ Battle #12 • Hip Hop 1v1 • Pool A                          │
│ Status: [Completed] ✅                                      │
│                                                            │
│ ┌──────────────────────┬──────────────────────────────────┐│
│ │ 🎭 B-Boy Storm       │ 🎭 Crazy Legs                   ││
│ │ Winner 🏆            │                                  ││
│ │                      │                                  ││
│ │ John Doe             │ Sarah Smith                     ││
│ │ storm@example.com    │ legs@example.com                ││
│ └──────────────────────┴──────────────────────────────────┘│
│                                                            │
│ Judge Scores (V2 Only):                                    │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Judge #1: B-Boy Storm (3-2)                           │ │
│ │ Judge #2: B-Boy Storm (3-1)                           │ │
│ │ Judge #3: B-Boy Storm (3-2)                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Final Result: B-Boy Storm wins 3-0                         │
│                                                            │
│ MC Actions (if status = Ready):                            │
│ [Start Battle]                                             │
│                                                            │
│ V1 Staff/Admin Actions (if status = In Progress):          │
│ [Encode Winner]                                            │
│                                                            │
│ V2 Judge Actions (if status = In Progress):                │
│ [Score Battle] (if haven't scored yet)                     │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back to Battles          │
│ Battle Detail              │
├────────────────────────────┤
│ Battle #12                 │
│ Hip Hop 1v1 • Pool A       │
│ [Completed] ✅              │
│                            │
│ ┌────────────────────────┐ │
│ │ 🎭 B-Boy Storm         │ │
│ │ Winner 🏆              │ │
│ │                        │ │
│ │ John Doe               │ │
│ │ storm@example.com      │ │
│ └────────────────────────┘ │
│                            │
│ vs                         │
│                            │
│ ┌────────────────────────┐ │
│ │ 🎭 Crazy Legs          │ │
│ │                        │ │
│ │ Sarah Smith            │ │
│ │ legs@example.com       │ │
│ └────────────────────────┘ │
│                            │
│ Judge Scores:              │
│                            │
│ Judge #1:                  │
│ B-Boy Storm (3-2)          │
│                            │
│ Judge #2:                  │
│ B-Boy Storm (3-1)          │
│                            │
│ Judge #3:                  │
│ B-Boy Storm (3-2)          │
│                            │
│ Final Result:              │
│ B-Boy Storm wins 3-0       │
│                            │
│ Battle Timeline:           │
│ • Started: 14:35           │
│ • All scored: 14:38        │
│ • Completed: 14:38         │
│                            │
│ MC Actions:                │
│ [Start Battle]             │
│ (if Ready status)          │
│                            │
│ Judge Actions:             │
│ [Score Battle]             │
│ (if In Progress & not      │
│  scored)                   │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Battle detail page -->
<article class="battle-detail">
  <header>
    <h2>Battle #12 • Hip Hop 1v1 • Pool A</h2>
    <span class="badge status-completed">Completed ✅</span>
  </header>

  <!-- Performers -->
  <section class="performers">
    <article class="performer winner">
      <span class="icon">🎭</span>
      <h3>B-Boy Storm</h3>
      <span class="badge winner-badge">Winner 🏆</span>
      <p>John Doe</p>
      <p>storm@example.com</p>
    </article>

    <div class="vs">vs</div>

    <article class="performer">
      <span class="icon">🎭</span>
      <h3>Crazy Legs</h3>
      <p>Sarah Smith</p>
      <p>legs@example.com</p>
    </article>
  </section>

  <!-- Judge scores -->
  <section class="judge-scores">
    <h3>Judge Scores:</h3>
    <ul>
      <li>Judge #1: B-Boy Storm (3-2)</li>
      <li>Judge #2: B-Boy Storm (3-1)</li>
      <li>Judge #3: B-Boy Storm (3-2)</li>
    </ul>
    <p class="final-result">Final Result: B-Boy Storm wins 3-0</p>
  </section>

  <!-- Battle timeline -->
  <section class="timeline">
    <h3>Battle Timeline:</h3>
    <ul>
      <li>Started: 2024-06-15 14:35</li>
      <li>All judges scored: 2024-06-15 14:38</li>
      <li>Completed: 2024-06-15 14:38</li>
    </ul>
  </section>

  <!-- Role-based actions -->
  <section class="actions">
    <!-- MC: Start battle if Ready -->
    <button
      hx-post="/battles/123/start"
      hx-confirm="Start Battle #12?"
      hx-target="body"
    >
      Start Battle
    </button>

    <!-- Judge: Score battle if In Progress and haven't scored -->
    <a href="/battles/123/score" role="button">
      Score Battle
    </a>
  </section>
</article>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through performer cards → scores → action buttons
  - Enter/Space to activate buttons
- **Screen Reader Announcements:**
  - Battle status announced: "Battle 12, status: Completed"
  - Winner announced: "Winner: B-Boy Storm"
  - Scores announced: "Judge 1 scored B-Boy Storm 3 to 2"
  - Final result announced: "Final result: B-Boy Storm wins 3 to 0"
- **ARIA Labels:**
  - Performer cards: `role="article"` with dancer names
  - Winner badge: `aria-label="Winner"`
  - Scores section: `role="region"`, `aria-label="Judge scores"`
  - Timeline: `role="region"`, `aria-label="Battle timeline"`
  - Action buttons: Context-specific labels
- **Focus Management:**
  - Focus on first action button when page loads
  - Focus preserved after status changes

**Validation States:**
- **Loading Battle:** Skeleton layout shown
- **Battle Loaded:** All details displayed
- **Status: Ready:** Gray badge, "Start Battle" button enabled (MC)
- **Status: In Progress:** Orange badge, "Score Battle" enabled (Judges who haven't scored)
- **Status: Completed:** Green badge with checkmark, winner highlighted
- **Partial Scores:** "Waiting for 1 more judge" message
- **All Scores In:** "All judges scored, calculating winner..."
- **No Actions Available:** "No actions available" (for completed battles)

---

### 21. Battle Result Encoding (V1 - Staff/Admin)

**Route:** `/battles/{battle_id}/encode`
**Permission:** Staff, Admin
**Purpose:** Encode battle results (winner selection) - used in V1 before Judge interface

> **Note:** In V1, Staff/Admin manually encodes battle results. The Judge Scoring Interface (Section 21.1) is a V2 feature.

**Components:**
- Battle info (category, pool, performers)
- Winner selection buttons
- Confirm result button
- Cancel button

**User Interactions:**
1. View battle → See performers and battle info
2. Select winner → Click on the winning performer
3. Confirm → Submit result to system
4. Cancel → Return to battle list without encoding

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Cancel                  Encode Battle #12 Result         │
├────────────────────────────────────────────────────────────┤
│ Hip Hop 1v1 • Pool A                                       │
│                                                            │
│ Select the winner of this battle:                          │
│                                                            │
│ ┌────────────────────────┬────────────────────────────────┐│
│ │                        │                                ││
│ │   🎭 B-Boy Storm       │   🎭 Crazy Legs                ││
│ │                        │                                ││
│ │   [Select as Winner]   │   [Select as Winner]           ││
│ │                        │                                ││
│ └────────────────────────┴────────────────────────────────┘│
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ [Confirm Winner: ______] (enabled after selection)         │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Cancel                   │
│ Encode Battle #12 Result   │
├────────────────────────────┤
│ Hip Hop 1v1 • Pool A       │
│                            │
│ Select the winner:         │
│                            │
│ ┌────────────────────────┐ │
│ │  🎭 B-Boy Storm        │ │
│ │  [Select as Winner]    │ │
│ └────────────────────────┘ │
│                            │
│           vs               │
│                            │
│ ┌────────────────────────┐ │
│ │  🎭 Crazy Legs         │ │
│ │  [Select as Winner]    │ │
│ └────────────────────────┘ │
│                            │
│ ──────────────────────     │
│                            │
│ [Confirm Winner: ______]   │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- V1 Battle result encoding -->
<form
  id="encode-form"
  hx-post="/battles/123/encode"
  hx-target="body"
>
  <header>
    <h2>Encode Battle #12 Result</h2>
    <p>Hip Hop 1v1 • Pool A</p>
  </header>

  <section class="performers">
    <article class="performer">
      <span class="icon">🎭</span>
      <h3>B-Boy Storm</h3>
      <button
        type="button"
        class="select-winner"
        data-performer-id="performer-1"
        onclick="selectWinner('performer-1', 'B-Boy Storm')"
      >
        Select as Winner
      </button>
    </article>

    <div class="vs">vs</div>

    <article class="performer">
      <span class="icon">🎭</span>
      <h3>Crazy Legs</h3>
      <button
        type="button"
        class="select-winner"
        data-performer-id="performer-2"
        onclick="selectWinner('performer-2', 'Crazy Legs')"
      >
        Select as Winner
      </button>
    </article>
  </section>

  <input type="hidden" name="winner_id" id="winner-id" value="">

  <button
    type="submit"
    id="confirm-btn"
    disabled
  >
    Confirm Winner: <span id="winner-name">______</span>
  </button>
</form>

<script>
function selectWinner(performerId, performerName) {
  document.getElementById('winner-id').value = performerId;
  document.getElementById('winner-name').textContent = performerName;
  document.getElementById('confirm-btn').disabled = false;
  // Highlight selected performer
  document.querySelectorAll('.performer').forEach(p => p.classList.remove('selected'));
  event.target.closest('.performer').classList.add('selected');
}
</script>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through Cancel → Performer 1 button → Performer 2 button → Confirm
  - Enter/Space to select winner
- **Screen Reader Announcements:**
  - Battle info announced on page load
  - "Selected B-Boy Storm as winner" when performer selected
  - "Winner confirmed" on submission
- **ARIA Labels:**
  - Performer buttons: `aria-label="Select B-Boy Storm as winner"`
  - Confirm button: `aria-disabled="true"` until selection made
- **Focus Management:**
  - Focus on first performer button when page loads
  - Focus moves to Confirm button after selection

**Validation States:**
- **Loading Battle:** Skeleton layout shown
- **Battle Loaded:** Both performers displayed
- **No Selection:** Confirm button disabled
- **Winner Selected:** Performer highlighted, Confirm enabled
- **Submitting:** Button shows "Confirming..."
- **Success:** Redirect to battle list with "Result recorded" message
- **Error:** "Failed to record result. Please try again."

---

### 21.1 Judge Scoring Interface (V2 Only - Enhanced)

> **V2 Feature:** This interface is for Judge accounts to score battles directly. In V1, Staff/Admin encodes results using the Battle Result Encoding interface (Section 21).

**Route:** `/battles/{battle_id}/score`
**Permission:** Judge only
**Purpose:** Score a battle between two performers

**Components:**
- Performer names and info
- Score buttons for each performer
- Round tracker
- Submit score button
- Real-time score display

**User Interactions:**
1. View performers → See both dancers' names
2. Score round → Click performer who won the round
3. View current score → See running tally
4. Submit score → Finalize and submit to system
5. Confirm → Return to battle list

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Cancel                  Score Battle #12                 │
├────────────────────────────────────────────────────────────┤
│ Hip Hop 1v1 • Pool A                                       │
│                                                            │
│ Round 1 of 5                                               │
│                                                            │
│ Who won this round?                                        │
│                                                            │
│ ┌────────────────────────┬────────────────────────────────┐│
│ │                        │                                ││
│ │   🎭 B-Boy Storm       │   🎭 Crazy Legs                ││
│ │                        │                                ││
│ │   Current Score: 0     │   Current Score: 0             ││
│ │                        │                                ││
│ │   [Score for Storm]    │   [Score for Crazy Legs]       ││
│ │                        │                                ││
│ └────────────────────────┴────────────────────────────────┘│
│                                                            │
│ Progress: [○][○][○][○][○]                                  │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ After scoring all rounds:                                  │
│ [Submit Score] (disabled until all rounds scored)          │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Cancel                   │
│ Score Battle #12           │
├────────────────────────────┤
│ Hip Hop 1v1 • Pool A       │
│                            │
│ Round 1 of 5               │
│                            │
│ Who won this round?        │
│                            │
│ ┌────────────────────────┐ │
│ │                        │ │
│ │  🎭 B-Boy Storm        │ │
│ │                        │ │
│ │  Current Score: 0      │ │
│ │                        │ │
│ │  [Score for Storm]     │ │
│ │                        │ │
│ └────────────────────────┘ │
│                            │
│           vs               │
│                            │
│ ┌────────────────────────┐ │
│ │                        │ │
│ │  🎭 Crazy Legs         │ │
│ │                        │ │
│ │  Current Score: 0      │ │
│ │                        │ │
│ │  [Score for Crazy Legs]│ │
│ │                        │ │
│ └────────────────────────┘ │
│                            │
│ Progress:                  │
│ [○][○][○][○][○]            │
│                            │
│ ──────────────────────     │
│                            │
│ After all rounds:          │
│ [Submit Score]             │
│ (disabled until done)      │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Judge scoring interface -->
<form
  id="scoring-form"
  hx-post="/battles/123/score"
  hx-target="#score-confirmation"
>
  <header>
    <h2>Score Battle #12</h2>
    <p>Hip Hop 1v1 • Pool A</p>
    <p id="round-indicator">Round <span id="current-round">1</span> of 5</p>
  </header>

  <section class="performers">
    <article class="performer">
      <span class="icon">🎭</span>
      <h3>B-Boy Storm</h3>
      <p class="score">Current Score: <span id="storm-score">0</span></p>
      <button
        type="button"
        class="score-button"
        data-performer="storm"
        onclick="scoreRound('storm')"
      >
        Score for Storm
      </button>
    </article>

    <div class="vs">vs</div>

    <article class="performer">
      <span class="icon">🎭</span>
      <h3>Crazy Legs</h3>
      <p class="score">Current Score: <span id="legs-score">0</span></p>
      <button
        type="button"
        class="score-button"
        data-performer="legs"
        onclick="scoreRound('legs')"
      >
        Score for Crazy Legs
      </button>
    </article>
  </section>

  <!-- Progress indicator -->
  <section class="progress">
    <p>Progress:</p>
    <div class="rounds">
      <span class="round" data-round="1">○</span>
      <span class="round" data-round="2">○</span>
      <span class="round" data-round="3">○</span>
      <span class="round" data-round="4">○</span>
      <span class="round" data-round="5">○</span>
    </div>
  </section>

  <!-- Hidden input to store scores -->
  <input type="hidden" name="scores" id="scores-data" value="">

  <!-- Submit button (enabled after all rounds) -->
  <button type="submit" id="submit-btn" disabled>
    Submit Score
  </button>
</form>

<div id="score-confirmation" role="status" aria-live="polite"></div>

<script>
// JavaScript for client-side scoring logic
let currentRound = 1;
let scores = { storm: 0, legs: 0 };
let roundWinners = [];

function scoreRound(performer) {
  if (currentRound > 5) return;

  // Update score
  scores[performer]++;
  document.getElementById(performer + '-score').textContent = scores[performer];

  // Mark round as scored
  roundWinners.push(performer);
  document.querySelector(`[data-round="${currentRound}"]`).textContent = '●';
  document.querySelector(`[data-round="${currentRound}"]`).classList.add('scored');

  // Move to next round
  currentRound++;
  document.getElementById('current-round').textContent = currentRound;

  // Enable submit if all rounds done
  if (currentRound > 5) {
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('scores-data').value = JSON.stringify(roundWinners);
  }
}
</script>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab between score buttons
  - Enter/Space to score for performer
  - Tab to Submit button when enabled
- **Screen Reader Announcements:**
  - Round announced: "Round 1 of 5"
  - Score announced after each round: "Storm scores, current: 1 to 0"
  - All rounds complete announced: "All rounds scored, ready to submit"
  - Submission announced: "Score submitted successfully"
- **ARIA Labels:**
  - Score buttons: `aria-label="Score round 1 for B-Boy Storm"`
  - Current scores: `aria-live="polite"` for updates
  - Progress indicator: `role="progressbar"`, `aria-valuenow="1"`, `aria-valuemax="5"`
  - Submit button: `aria-disabled="true"` until ready
- **Focus Management:**
  - Focus moves between score buttons
  - Focus moves to Submit button when all rounds scored
  - Focus moves to confirmation message after submission

**Validation States:**
- **Round 1:** Both scores at 0, progress shows 0/5 rounds
- **Round Scored:** Score updates, progress indicator fills one circle
- **Mid-Battle:** Running score displayed (e.g., "2-1")
- **All Rounds Scored:** Submit button enabled (green)
- **Submitting:** Button shows spinner, "Submitting score..."
- **Success:** Redirect to battles list with "Score submitted" message
- **Already Scored:** "You have already scored this battle"
- **Battle Not Started:** "Battle has not started yet"
- **Battle Completed:** "This battle is already completed"

---

### 22. MC Battle Management

**Route:** `/battles/mc`
**Permission:** MC only
**Purpose:** Start and manage battles from MC perspective

**Components:**
- Upcoming battles queue
- Current battle display
- Start next battle button
- Battle status indicators
- Pool and category filters

**User Interactions:**
1. View battle queue → See list of upcoming battles
2. Start next battle → Begin the next pending battle
3. View current battle → See battle in progress
4. Filter battles → View specific pool or category
5. Monitor progress → See judges' scoring status

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back                    MC: Battle Management            │
├────────────────────────────────────────────────────────────┤
│ Tournament: Summer Battle 2024 • Phase: Pools              │
│                                                            │
│ Current Battle:                                            │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Battle #12 • Hip Hop 1v1 • Pool A    [In Progress] 🔴 │ │
│ │                                                        │ │
│ │ B-Boy Storm  vs  Crazy Legs                           │ │
│ │                                                        │ │
│ │ Judges: 2/3 scored  ⚠️ Waiting for Judge #3           │ │
│ │                                                        │ │
│ │ [View Battle Details]                                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ───────────────────────────────────────────────────────    │
│                                                            │
│ Upcoming Battles (8):                                      │
│                                                            │
│ Filter: [All Pools ▼] [All Categories ▼]                  │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ #13 • Hip Hop 1v1 • Pool A          [Ready] ⏸️          │ │
│ │ Phoenix  vs  Thunder                                   │ │
│ │ [Start Battle]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ #14 • Breaking Duo • Pool B         [Ready] ⏸️          │ │
│ │ Storm/Fierce  vs  Kid/Breakmaster                      │ │
│ │ [Start Battle]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ #15 • Krump 1v1 • Pool C            [Ready] ⏸️          │ │
│ │ Lightning  vs  Blaze                                   │ │
│ │ [Start Battle]                                         │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Start Next Battle] (starts #13)                           │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ MC: Battle Management      │
├────────────────────────────┤
│ Summer Battle 2024         │
│ Phase: Pools               │
│                            │
│ Current Battle:            │
│                            │
│ ┌────────────────────────┐ │
│ │ Battle #12             │ │
│ │ Hip Hop 1v1 • Pool A   │ │
│ │ [In Progress] 🔴       │ │
│ │                        │ │
│ │ B-Boy Storm            │ │
│ │   vs                   │ │
│ │ Crazy Legs             │ │
│ │                        │ │
│ │ Judges: 2/3 scored     │ │
│ │ ⚠️ Waiting for Judge #3│ │
│ │                        │ │
│ │ [View Details]         │ │
│ └────────────────────────┘ │
│                            │
│ ──────────────────────     │
│                            │
│ Upcoming Battles (8):      │
│                            │
│ Filter: [All Pools ▼]      │
│ [All Categories ▼]         │
│                            │
│ ┌────────────────────────┐ │
│ │ #13 • Hip Hop 1v1      │ │
│ │ Pool A [Ready] ⏸️       │ │
│ │                        │ │
│ │ Phoenix  vs  Thunder   │ │
│ │                        │ │
│ │ [Start Battle]         │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ #14 • Breaking Duo     │ │
│ │ Pool B [Ready] ⏸️       │ │
│ │                        │ │
│ │ Storm/Fierce vs        │ │
│ │ Kid/Breakmaster        │ │
│ │                        │ │
│ │ [Start Battle]         │ │
│ └────────────────────────┘ │
│                            │
│ [Start Next Battle]        │
│ (starts #13)               │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- MC Battle Management -->
<article class="mc-management">
  <header>
    <h2>MC: Battle Management</h2>
    <p>Tournament: Summer Battle 2024 • Phase: Pools</p>
  </header>

  <!-- Current battle (if any) -->
  <section
    id="current-battle"
    hx-get="/battles/current"
    hx-trigger="every 10s"
    hx-swap="innerHTML"
  >
    <h3>Current Battle:</h3>
    <article class="battle-card in-progress">
      <h4>Battle #12 • Hip Hop 1v1 • Pool A</h4>
      <span class="badge in-progress">In Progress 🔴</span>
      <p>B-Boy Storm vs Crazy Legs</p>
      <p>Judges: 2/3 scored ⚠️ Waiting for Judge #3</p>
      <a href="/battles/12" role="button">View Battle Details</a>
    </article>
  </section>

  <!-- Upcoming battles -->
  <section class="upcoming-battles">
    <h3>Upcoming Battles (8):</h3>

    <!-- Filters -->
    <div class="filters">
      <select
        name="pool"
        hx-get="/battles/mc"
        hx-trigger="change"
        hx-target="#battle-queue"
      >
        <option value="">All Pools</option>
        <option value="A">Pool A</option>
        <option value="B">Pool B</option>
        <option value="C">Pool C</option>
      </select>

      <select
        name="category"
        hx-get="/battles/mc"
        hx-trigger="change"
        hx-target="#battle-queue"
      >
        <option value="">All Categories</option>
        <option value="1">Hip Hop 1v1</option>
        <option value="2">Breaking Duo</option>
        <option value="3">Krump 1v1</option>
      </select>
    </div>

    <!-- Battle queue -->
    <div id="battle-queue">
      <article class="battle-card ready">
        <h4>#13 • Hip Hop 1v1 • Pool A</h4>
        <span class="badge ready">Ready ⏸️</span>
        <p>Phoenix vs Thunder</p>
        <button
          hx-post="/battles/13/start"
          hx-confirm="Start Battle #13?"
          hx-target="#current-battle"
        >
          Start Battle
        </button>
      </article>

      <!-- More battles... -->
    </div>

    <!-- Start next battle (quick action) -->
    <button
      class="primary"
      hx-post="/battles/next/start"
      hx-confirm="Start next battle (#13)?"
      hx-target="#current-battle"
    >
      Start Next Battle
    </button>
  </section>
</article>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through filters → battle cards → Start buttons
  - Enter/Space to activate buttons and filters
- **Screen Reader Announcements:**
  - Current battle announced with status
  - Judge progress announced: "2 of 3 judges scored"
  - Queue count announced: "8 upcoming battles"
  - Filter changes announced: "Filtered to Pool A, 3 battles"
  - Battle started announced: "Battle 13 started"
- **ARIA Labels:**
  - Current battle: `role="region"`, `aria-label="Current battle"`
  - Battle cards: `role="article"` with battle number
  - Start buttons: `aria-label="Start battle 13: Phoenix vs Thunder"`
  - Filters: Descriptive labels for each dropdown
- **Focus Management:**
  - Focus preserved on current battle after auto-refresh
  - Focus moves to success message after starting battle
  - Focus returns to queue after action

**Validation States:**
- **Loading Queue:** Skeleton cards shown
- **No Current Battle:** "No battle in progress"
- **Battle In Progress:** Orange badge, judge status displayed
- **Waiting for Judges:** Warning icon with judge count
- **All Judges Scored:** "Calculating winner..." message
- **Battle Complete:** Green badge, winner announced
- **Empty Queue:** "No upcoming battles"
- **Starting Battle:** Button shows spinner, "Starting..."
- **Start Success:** Current battle updates, queue refreshes
- **Start Failed:** Error message, "Failed to start battle"

---

### 23. Pool Standings

**Route:** `/pools/{pool_id}/standings`
**Permission:** Staff, Admin, MC, Judge
**Purpose:** View current standings and rankings in a pool

**Components:**
- Pool info (category, performers count)
- Standings table with win/loss records
- Performer rankings
- Advancement indicators

**User Interactions:**
1. View standings → See ranked list of performers
2. View records → See win/loss record for each performer
3. Monitor advancement → See who advances to next phase
4. Refresh standings → Get latest results

**Desktop Layout (> 768px):**
```
┌────────────────────────────────────────────────────────────┐
│ ← Back                    Pool Standings                   │
├────────────────────────────────────────────────────────────┤
│ Hip Hop 1v1 • Pool A                                       │
│ 4 performers • 6 battles (4 completed, 2 pending)          │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Rank│Performer    │Wins│Losses│Points│Status         │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │  1  │ B-Boy Storm │ 3  │  0   │  3   │ ✅ Advances   │ │
│ │  2  │ Phoenix     │ 2  │  1   │  2   │ ✅ Advances   │ │
│ │  3  │ Thunder     │ 1  │  2   │  1   │ ❌ Eliminated │ │
│ │  4  │ Crazy Legs  │ 0  │  3   │  0   │ ❌ Eliminated │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Advancement:                                               │
│ • Top 2 performers advance to Finals                       │
│ • B-Boy Storm and Phoenix advance                          │
│                                                            │
│ Recent Battles:                                            │
│ • Battle #12: B-Boy Storm def. Crazy Legs (3-0)           │
│ • Battle #11: Phoenix def. Thunder (2-1)                   │
│ • Battle #10: B-Boy Storm def. Thunder (3-0)              │
│                                                            │
│ Pending Battles:                                           │
│ • Battle #13: Phoenix vs Thunder                           │
│ • Battle #14: B-Boy Storm vs Phoenix                       │
│                                                            │
│ [View All Battles]  [Refresh Standings]                    │
└────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ← Back                     │
│ Pool Standings             │
├────────────────────────────┤
│ Hip Hop 1v1 • Pool A       │
│ 4 performers               │
│ 6 battles (4 done, 2 left) │
│                            │
│ ┌────────────────────────┐ │
│ │ 1. B-Boy Storm         │ │
│ │    3W - 0L (3 pts)     │ │
│ │    ✅ Advances to Finals│ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ 2. Phoenix             │ │
│ │    2W - 1L (2 pts)     │ │
│ │    ✅ Advances to Finals│ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ 3. Thunder             │ │
│ │    1W - 2L (1 pt)      │ │
│ │    ❌ Eliminated        │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │ 4. Crazy Legs          │ │
│ │    0W - 3L (0 pts)     │ │
│ │    ❌ Eliminated        │ │
│ └────────────────────────┘ │
│                            │
│ Advancement:               │
│ Top 2 advance to Finals    │
│                            │
│ Recent Battles:            │
│ • #12: Storm def. Legs     │
│   (3-0)                    │
│ • #11: Phoenix def.        │
│   Thunder (2-1)            │
│                            │
│ Pending:                   │
│ • #13: Phoenix vs Thunder  │
│ • #14: Storm vs Phoenix    │
│                            │
│ [View All Battles]         │
│ [Refresh Standings]        │
└────────────────────────────┘
```

**HTMX Interactions:**
```html
<!-- Pool standings -->
<article
  class="pool-standings"
  hx-get="/pools/123/standings"
  hx-trigger="every 30s"
  hx-swap="outerHTML"
>
  <header>
    <h2>Pool Standings</h2>
    <p>Hip Hop 1v1 • Pool A</p>
    <p>4 performers • 6 battles (4 completed, 2 pending)</p>
  </header>

  <!-- Standings table -->
  <table class="standings">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Performer</th>
        <th>Wins</th>
        <th>Losses</th>
        <th>Points</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr class="advances">
        <td>1</td>
        <td>B-Boy Storm</td>
        <td>3</td>
        <td>0</td>
        <td>3</td>
        <td>✅ Advances</td>
      </tr>
      <tr class="advances">
        <td>2</td>
        <td>Phoenix</td>
        <td>2</td>
        <td>1</td>
        <td>2</td>
        <td>✅ Advances</td>
      </tr>
      <tr class="eliminated">
        <td>3</td>
        <td>Thunder</td>
        <td>1</td>
        <td>2</td>
        <td>1</td>
        <td>❌ Eliminated</td>
      </tr>
      <tr class="eliminated">
        <td>4</td>
        <td>Crazy Legs</td>
        <td>0</td>
        <td>3</td>
        <td>0</td>
        <td>❌ Eliminated</td>
      </tr>
    </tbody>
  </table>

  <!-- Advancement info -->
  <section class="advancement-info">
    <h3>Advancement:</h3>
    <p>Top 2 performers advance to Finals</p>
    <p>B-Boy Storm and Phoenix advance</p>
  </section>

  <!-- Recent battles -->
  <section class="recent-battles">
    <h3>Recent Battles:</h3>
    <ul>
      <li>Battle #12: B-Boy Storm def. Crazy Legs (3-0)</li>
      <li>Battle #11: Phoenix def. Thunder (2-1)</li>
      <li>Battle #10: B-Boy Storm def. Thunder (3-0)</li>
    </ul>
  </section>

  <!-- Pending battles -->
  <section class="pending-battles">
    <h3>Pending Battles:</h3>
    <ul>
      <li>Battle #13: Phoenix vs Thunder</li>
      <li>Battle #14: B-Boy Storm vs Phoenix</li>
    </ul>
  </section>

  <!-- Actions -->
  <div class="actions">
    <a href="/battles?pool=123" role="button">View All Battles</a>
    <button
      hx-get="/pools/123/standings"
      hx-target="closest article"
      hx-swap="outerHTML"
    >
      Refresh Standings
    </button>
  </div>
</article>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Tab through table rows → action buttons
  - Enter/Space to activate buttons
- **Screen Reader Announcements:**
  - Standings announced: "Pool A standings, 4 performers"
  - Each row announced with rank and record
  - Advancement status announced: "B-Boy Storm, rank 1, advances"
  - Updates announced with `aria-live="polite"`
- **ARIA Labels:**
  - Table: `role="table"`, `aria-label="Pool standings"`
  - Rows: Context for rank and status
  - Advancement section: `role="region"`, `aria-label="Advancement information"`
  - Refresh button: `aria-label="Refresh standings"`
- **Focus Management:**
  - Focus preserved on table after auto-refresh
  - Focus moves to updated row after manual refresh

**Validation States:**
- **Loading Standings:** Skeleton table shown
- **Standings Loaded:** All data displayed with formatting
- **Ties in Ranking:** "Tied at rank 2" indicator
- **Complete Pool:** All battles finished, final standings
- **Incomplete Pool:** "X battles remaining" message
- **Refreshing:** Brief spinner, seamless update
- **Auto-Refresh Active:** Timestamp shown: "Last updated: 14:45"
- **No Battles Yet:** "No battles completed yet"

---

## Section 13: Projection Display Pages

### 13.1 Full-Screen Battle View

**Purpose:** Large-format display for audience viewing during battles, typically shown on projectors or large screens.

**Permissions:** Public (no authentication required)

**User Interactions:**
1. Display automatically refreshes as judges submit scores
2. Real-time updates show current round and score changes
3. Auto-advances to next battle when current battle concludes
4. Displays battle queue and upcoming matches
5. Can cycle through different display modes (battle view → standings → sponsors)

**Full-Screen Layout (1920x1080+ recommended):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUMMER BATTLE 2024                                   │
│                      HIP HOP 1V1 • POOL A • BATTLE #12                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────┐   ┌─────────────────────────────────┐│
│   │         B-BOY STORM             │   │         CRAZY LEGS              ││
│   │                                 │   │                                 ││
│   │      ███████                    │   │      ███████                    ││
│   │      ███████                    │   │      ███████                    ││
│   │      ███████                    │   │      ███████                    ││
│   │                                 │   │                                 ││
│   │      SCORE: 3                   │   │      SCORE: 1                   ││
│   │      ========                   │   │      ========                   ││
│   │      ● ● ● ○ ○                  │   │      ● ○ ○ ○ ○                  ││
│   │                                 │   │                                 ││
│   └─────────────────────────────────┘   └─────────────────────────────────┘│
│                                                                              │
│                          ROUND 4 OF 5 IN PROGRESS                            │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  JUDGES SCORING:    Judge #1 ✓    Judge #2 ✓    Judge #3 ⏳        │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   NEXT UP: Battle #13 • Phoenix vs Thunder                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**HTMX/JavaScript:**
```html
<!-- Auto-refreshing battle display -->
<div
  id="battle-display"
  hx-get="/projection/battle/current"
  hx-trigger="every 3s"
  hx-swap="innerHTML"
>
  <header>
    <h1>Summer Battle 2024</h1>
    <h2>Hip Hop 1v1 • Pool A • Battle #12</h2>
  </header>

  <div class="battle-arena">
    <!-- Performer 1 -->
    <article class="performer left">
      <h3>B-Boy Storm</h3>
      <div class="avatar">
        <img src="/avatars/storm.jpg" alt="B-Boy Storm">
      </div>
      <div class="score-display">
        <span class="score">3</span>
        <div class="rounds">
          <span class="won">●</span>
          <span class="won">●</span>
          <span class="won">●</span>
          <span class="pending">○</span>
          <span class="pending">○</span>
        </div>
      </div>
    </article>

    <!-- VS Divider -->
    <div class="vs-divider">
      <span>VS</span>
    </div>

    <!-- Performer 2 -->
    <article class="performer right">
      <h3>Crazy Legs</h3>
      <div class="avatar">
        <img src="/avatars/legs.jpg" alt="Crazy Legs">
      </div>
      <div class="score-display">
        <span class="score">1</span>
        <div class="rounds">
          <span class="won">●</span>
          <span class="pending">○</span>
          <span class="pending">○</span>
          <span class="pending">○</span>
          <span class="pending">○</span>
        </div>
      </div>
    </article>
  </div>

  <div class="round-status">
    <h3>Round 4 of 5 in Progress</h3>
  </div>

  <div class="judge-status">
    <span>Judge #1 ✓</span>
    <span>Judge #2 ✓</span>
    <span class="waiting">Judge #3 ⏳</span>
  </div>

  <footer class="next-battle">
    <p>Next Up: Battle #13 • Phoenix vs Thunder</p>
  </footer>
</div>

<style>
/* Full-screen display styling */
#battle-display {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  padding: 2rem;
  font-family: 'Arial Black', sans-serif;
}

header {
  text-align: center;
}

header h1 {
  font-size: 3rem;
  margin: 0;
}

header h2 {
  font-size: 1.5rem;
  margin: 0.5rem 0;
  opacity: 0.8;
}

.battle-arena {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex: 1;
}

.performer {
  text-align: center;
  padding: 2rem;
  border: 3px solid rgba(255,255,255,0.2);
  border-radius: 1rem;
  background: rgba(255,255,255,0.05);
  min-width: 400px;
}

.performer h3 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.avatar {
  width: 250px;
  height: 250px;
  margin: 0 auto 2rem;
  border-radius: 50%;
  overflow: hidden;
  border: 5px solid #fff;
}

.score-display .score {
  font-size: 5rem;
  font-weight: bold;
  display: block;
  margin-bottom: 1rem;
}

.rounds {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.rounds span {
  font-size: 2rem;
}

.rounds .won {
  color: #00ff00;
}

.rounds .pending {
  color: rgba(255,255,255,0.3);
}

.vs-divider {
  font-size: 4rem;
  font-weight: bold;
  opacity: 0.5;
}

.round-status {
  text-align: center;
  font-size: 2rem;
  padding: 1rem;
  background: rgba(255,255,255,0.1);
  border-radius: 0.5rem;
}

.judge-status {
  display: flex;
  justify-content: center;
  gap: 2rem;
  font-size: 1.5rem;
}

.judge-status .waiting {
  opacity: 0.5;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

.next-battle {
  text-align: center;
  font-size: 1.25rem;
  opacity: 0.7;
}
</style>
```

**Accessibility:**
- **Keyboard Navigation:** Not applicable (display-only screen)
- **Screen Reader Announcements:**
  - Display is visual-only, not intended for screen reader users
  - Designed for large-format audience viewing
- **ARIA Labels:** Minimal (not interactive)
- **Focus Management:** No focus required (auto-updating display)

**Validation States:**
- **Battle in Progress:** Live scoring updates, round indicator
- **Battle Complete:** Winner announced with final score
- **Waiting for Judges:** "Waiting for judges..." message with animation
- **Between Battles:** "Next battle starting soon..." countdown
- **No Active Battle:** Shows upcoming battle schedule
- **Connection Lost:** "Reconnecting..." message with retry animation
- **Tournament Complete:** Final standings and winner announcement

---

### 13.2 Pool Standings Leaderboard

**Purpose:** Large-format standings display showing current pool rankings for audience viewing.

**Permissions:** Public (no authentication required)

**User Interactions:**
1. Auto-refreshes every 30 seconds to show latest standings
2. Highlights performers who have advanced or are in advancement positions
3. Shows recent battle results at the bottom
4. Cycles between multiple pools if applicable

**Full-Screen Layout (1920x1080+ recommended):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUMMER BATTLE 2024                                   │
│                   HIP HOP 1V1 • POOL A STANDINGS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ╔═══════════════════════════════════════════════════════════════════╗      │
│   ║  RANK  │  PERFORMER       │  WINS  │  LOSSES  │  WIN %  │  STATUS ║      │
│   ╠═══════════════════════════════════════════════════════════════════╣      │
│   ║   1    │  B-Boy Storm     │   4    │    0     │  100%   │  ✓ ADV  ║      │
│   ║   2    │  Phoenix         │   3    │    1     │   75%   │  ✓ ADV  ║      │
│   ╠───────────────────────────────────────────────────────────────────╣      │
│   ║   3    │  Thunder         │   2    │    2     │   50%   │         ║      │
│   ║   4    │  Crazy Legs      │   1    │    3     │   25%   │         ║      │
│   ║   5    │  Lightning       │   0    │    4     │    0%   │         ║      │
│   ╚═══════════════════════════════════════════════════════════════════╝      │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  RECENT RESULTS:                                                    │   │
│   │  • Battle #12: B-Boy Storm def. Crazy Legs (3-1)                   │   │
│   │  • Battle #11: Phoenix def. Thunder (3-2)                          │   │
│   │  • Battle #10: B-Boy Storm def. Lightning (3-0)                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                    Last Updated: 14:45 • Auto-refresh: ON                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**HTMX/JavaScript:**
```html
<!-- Auto-refreshing standings leaderboard -->
<div
  id="standings-leaderboard"
  hx-get="/projection/standings"
  hx-trigger="every 30s"
  hx-swap="innerHTML"
>
  <header>
    <h1>Summer Battle 2024</h1>
    <h2>Hip Hop 1v1 • Pool A Standings</h2>
  </header>

  <table class="leaderboard">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Performer</th>
        <th>Wins</th>
        <th>Losses</th>
        <th>Win %</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr class="advancing">
        <td class="rank">1</td>
        <td class="performer">B-Boy Storm</td>
        <td class="wins">4</td>
        <td class="losses">0</td>
        <td class="percentage">100%</td>
        <td class="status">✓ ADV</td>
      </tr>
      <tr class="advancing">
        <td class="rank">2</td>
        <td class="performer">Phoenix</td>
        <td class="wins">3</td>
        <td class="losses">1</td>
        <td class="percentage">75%</td>
        <td class="status">✓ ADV</td>
      </tr>
      <tr>
        <td class="rank">3</td>
        <td class="performer">Thunder</td>
        <td class="wins">2</td>
        <td class="losses">2</td>
        <td class="percentage">50%</td>
        <td class="status"></td>
      </tr>
      <tr>
        <td class="rank">4</td>
        <td class="performer">Crazy Legs</td>
        <td class="wins">1</td>
        <td class="losses">3</td>
        <td class="percentage">25%</td>
        <td class="status"></td>
      </tr>
      <tr>
        <td class="rank">5</td>
        <td class="performer">Lightning</td>
        <td class="wins">0</td>
        <td class="losses">4</td>
        <td class="percentage">0%</td>
        <td class="status"></td>
      </tr>
    </tbody>
  </table>

  <section class="recent-results">
    <h3>Recent Results:</h3>
    <ul>
      <li>Battle #12: B-Boy Storm def. Crazy Legs (3-1)</li>
      <li>Battle #11: Phoenix def. Thunder (3-2)</li>
      <li>Battle #10: B-Boy Storm def. Lightning (3-0)</li>
    </ul>
  </section>

  <footer>
    <p>Last Updated: <span id="update-time">14:45</span> • Auto-refresh: ON</p>
  </footer>
</div>

<style>
/* Full-screen leaderboard styling */
#standings-leaderboard {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  padding: 3rem;
  font-family: 'Arial', sans-serif;
}

header {
  text-align: center;
  margin-bottom: 2rem;
}

header h1 {
  font-size: 3rem;
  margin: 0;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

header h2 {
  font-size: 1.8rem;
  margin: 0.5rem 0;
  opacity: 0.9;
}

.leaderboard {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 1.5rem;
  margin: 2rem 0;
}

.leaderboard thead {
  background: rgba(255,255,255,0.2);
}

.leaderboard th {
  padding: 1.5rem;
  text-align: left;
  font-weight: bold;
  border-bottom: 3px solid rgba(255,255,255,0.3);
}

.leaderboard tbody tr {
  background: rgba(255,255,255,0.05);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.leaderboard tbody tr.advancing {
  background: rgba(0,255,0,0.15);
  border-left: 5px solid #00ff00;
}

.leaderboard td {
  padding: 1.5rem;
}

.leaderboard .rank {
  font-size: 2rem;
  font-weight: bold;
  text-align: center;
  width: 100px;
}

.leaderboard .performer {
  font-size: 1.8rem;
  font-weight: bold;
}

.leaderboard .status {
  color: #00ff00;
  font-weight: bold;
  font-size: 1.5rem;
}

.recent-results {
  background: rgba(255,255,255,0.1);
  padding: 2rem;
  border-radius: 1rem;
  margin: 2rem 0;
}

.recent-results h3 {
  font-size: 1.8rem;
  margin-bottom: 1rem;
}

.recent-results ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recent-results li {
  font-size: 1.3rem;
  padding: 0.5rem 0;
  opacity: 0.9;
}

footer {
  text-align: center;
  font-size: 1.2rem;
  opacity: 0.7;
}
</style>
```

**Accessibility:**
- **Keyboard Navigation:** Not applicable (display-only screen)
- **Screen Reader Announcements:** Display is visual-only for audience
- **ARIA Labels:** Minimal (not interactive)
- **Focus Management:** No focus required

**Validation States:**
- **Loading Standings:** Skeleton table with loading animation
- **Standings Loaded:** Full standings with color-coded advancement
- **Pool Complete:** "Pool Complete" banner shown
- **Live Updates:** Smooth transitions when standings change
- **Ties in Ranking:** "Tied" indicator for equal records
- **No Battles Yet:** "Battles starting soon..." message
- **Multiple Pools:** Cycles through pools every 60 seconds

---

### 13.3 Upcoming Battles Queue

**Purpose:** Display showing upcoming battles for audience and participants.

**Permissions:** Public (no authentication required)

**User Interactions:**
1. Auto-refreshes every 10 seconds to show latest queue
2. Highlights currently active battle
3. Shows battle status (pending, in progress, complete)
4. Displays pool information for context

**Full-Screen Layout (1920x1080+ recommended):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUMMER BATTLE 2024                                   │
│                         UPCOMING BATTLES QUEUE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 🔴 NOW PLAYING                                                      │   │
│   │ Battle #12 • Hip Hop 1v1 • Pool A                                  │   │
│   │ B-Boy Storm vs Crazy Legs                                          │   │
│   │ Round 4 of 5 • Judges: 2/3 scored                                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ ⏳ UP NEXT                                                          │   │
│   │ Battle #13 • Hip Hop 1v1 • Pool A                                  │   │
│   │ Phoenix vs Thunder                                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ╔═══════════════════════════════════════════════════════════════════╗      │
│   ║ PENDING BATTLES:                                                  ║      │
│   ╠═══════════════════════════════════════════════════════════════════╣      │
│   ║ #14 │ B-Boy Storm vs Phoenix    │ Hip Hop 1v1 │ Pool A          ║      │
│   ║ #15 │ Thunder vs Crazy Legs     │ Hip Hop 1v1 │ Pool A          ║      │
│   ║ #16 │ Lightning vs B-Boy Storm  │ Hip Hop 1v1 │ Pool A          ║      │
│   ║ #17 │ Breeze vs Tornado         │ Popping 1v1 │ Pool B          ║      │
│   ║ #18 │ Flash vs Striker          │ Popping 1v1 │ Pool B          ║      │
│   ╚═══════════════════════════════════════════════════════════════════╝      │
│                                                                              │
│              Last Updated: 14:47 • Auto-refresh: ON (10s)                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**HTMX/JavaScript:**
```html
<!-- Auto-refreshing battle queue -->
<div
  id="battle-queue"
  hx-get="/projection/queue"
  hx-trigger="every 10s"
  hx-swap="innerHTML"
>
  <header>
    <h1>Summer Battle 2024</h1>
    <h2>Upcoming Battles Queue</h2>
  </header>

  <!-- Current Battle -->
  <article class="current-battle">
    <span class="badge live">🔴 NOW PLAYING</span>
    <h3>Battle #12 • Hip Hop 1v1 • Pool A</h3>
    <p class="performers">B-Boy Storm vs Crazy Legs</p>
    <p class="status">Round 4 of 5 • Judges: 2/3 scored</p>
  </article>

  <!-- Next Battle -->
  <article class="next-battle">
    <span class="badge next">⏳ UP NEXT</span>
    <h3>Battle #13 • Hip Hop 1v1 • Pool A</h3>
    <p class="performers">Phoenix vs Thunder</p>
  </article>

  <!-- Pending Battles Table -->
  <section class="pending-battles">
    <h3>Pending Battles:</h3>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Matchup</th>
          <th>Category</th>
          <th>Pool</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>#14</td>
          <td>B-Boy Storm vs Phoenix</td>
          <td>Hip Hop 1v1</td>
          <td>Pool A</td>
        </tr>
        <tr>
          <td>#15</td>
          <td>Thunder vs Crazy Legs</td>
          <td>Hip Hop 1v1</td>
          <td>Pool A</td>
        </tr>
        <tr>
          <td>#16</td>
          <td>Lightning vs B-Boy Storm</td>
          <td>Hip Hop 1v1</td>
          <td>Pool A</td>
        </tr>
        <tr>
          <td>#17</td>
          <td>Breeze vs Tornado</td>
          <td>Popping 1v1</td>
          <td>Pool B</td>
        </tr>
        <tr>
          <td>#18</td>
          <td>Flash vs Striker</td>
          <td>Popping 1v1</td>
          <td>Pool B</td>
        </tr>
      </tbody>
    </table>
  </section>

  <footer>
    <p>Last Updated: <span id="update-time">14:47</span> • Auto-refresh: ON (10s)</p>
  </footer>
</div>

<style>
/* Full-screen queue styling */
#battle-queue {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #232526 0%, #414345 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  padding: 2rem;
  font-family: 'Arial', sans-serif;
}

header {
  text-align: center;
  margin-bottom: 1rem;
}

header h1 {
  font-size: 3rem;
  margin: 0;
}

header h2 {
  font-size: 1.5rem;
  margin: 0.5rem 0;
  opacity: 0.8;
}

.current-battle {
  background: rgba(255,0,0,0.2);
  border: 3px solid #ff0000;
  padding: 2rem;
  border-radius: 1rem;
  margin: 1rem 0;
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0%, 100% { border-color: #ff0000; }
  50% { border-color: #ff6666; }
}

.next-battle {
  background: rgba(255,165,0,0.2);
  border: 3px solid #ffa500;
  padding: 2rem;
  border-radius: 1rem;
  margin: 1rem 0;
}

.badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: bold;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.badge.live {
  background: #ff0000;
  color: #fff;
}

.badge.next {
  background: #ffa500;
  color: #fff;
}

.current-battle h3,
.next-battle h3 {
  font-size: 2rem;
  margin: 0.5rem 0;
}

.performers {
  font-size: 2.5rem;
  font-weight: bold;
  margin: 1rem 0;
}

.status {
  font-size: 1.5rem;
  opacity: 0.8;
}

.pending-battles {
  background: rgba(255,255,255,0.1);
  padding: 2rem;
  border-radius: 1rem;
  margin: 1rem 0;
}

.pending-battles h3 {
  font-size: 1.8rem;
  margin-bottom: 1rem;
}

.pending-battles table {
  width: 100%;
  border-collapse: collapse;
  font-size: 1.3rem;
}

.pending-battles th {
  text-align: left;
  padding: 1rem;
  border-bottom: 2px solid rgba(255,255,255,0.3);
}

.pending-battles td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

footer {
  text-align: center;
  font-size: 1.2rem;
  opacity: 0.7;
}
</style>
```

**Accessibility:**
- **Keyboard Navigation:** Not applicable (display-only screen)
- **Screen Reader Announcements:** Display is visual-only for audience
- **ARIA Labels:** Minimal (not interactive)
- **Focus Management:** No focus required

**Validation States:**
- **Loading Queue:** Skeleton cards with loading animation
- **Queue Loaded:** Current, next, and pending battles displayed
- **No Current Battle:** "No battle in progress" message
- **No Pending Battles:** "All battles complete" message
- **Battle Transition:** Smooth animation as battles move up the queue
- **Connection Lost:** "Reconnecting..." message with retry animation

---

### 13.4 Tournament Bracket Visualization

**Purpose:** Visual bracket display showing tournament progression (for Finals phase).

**Permissions:** Public (no authentication required)

**User Interactions:**
1. Auto-refreshes as battles complete and winners advance
2. Shows full bracket structure with winner progression
3. Highlights active matches and completed paths
4. Updates in real-time as judges submit scores

**Full-Screen Layout (1920x1080+ recommended):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUMMER BATTLE 2024                                   │
│                       HIP HOP 1V1 • FINALS BRACKET                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   QUARTER-FINALS      SEMI-FINALS         FINALS          CHAMPION          │
│                                                                              │
│   ┌──────────────┐                                                          │
│   │ Storm (✓3-1) │──┐                                                       │
│   └──────────────┘  │   ┌──────────────┐                                    │
│                     ├───│ Storm (🔴)   │──┐                                 │
│   ┌──────────────┐  │   └──────────────┘  │                                 │
│   │ Phoenix      │──┘                     │   ┌──────────────┐              │
│   └──────────────┘                        ├───│   WINNER?    │              │
│                                           │   └──────────────┘              │
│   ┌──────────────┐                        │                                 │
│   │ Thunder      │──┐                     │                                 │
│   └──────────────┘  │   ┌──────────────┐  │                                 │
│                     ├───│ Legs (✓3-2)  │──┘                                 │
│   ┌──────────────┐  │   └──────────────┘                                    │
│   │ C.Legs (✓3-0)│──┘                                                       │
│   └──────────────┘                                                          │
│                                                                              │
│   Legend: ✓ = Winner | 🔴 = In Progress | ⏳ = Pending                       │
│                                                                              │
│   Current: Finals • Storm vs Crazy Legs • Round 2 of 5                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**HTMX/JavaScript:**
```html
<!-- Auto-refreshing bracket display -->
<div
  id="tournament-bracket"
  hx-get="/projection/bracket"
  hx-trigger="every 10s"
  hx-swap="innerHTML"
>
  <header>
    <h1>Summer Battle 2024</h1>
    <h2>Hip Hop 1v1 • Finals Bracket</h2>
  </header>

  <div class="bracket-container">
    <!-- Quarter-Finals Column -->
    <div class="bracket-column">
      <h3>Quarter-Finals</h3>
      <div class="bracket-matches">
        <article class="match completed">
          <div class="performer winner">B-Boy Storm ✓</div>
          <div class="score">3-1</div>
          <div class="performer">Phoenix</div>
        </article>
        <article class="match completed">
          <div class="performer">Thunder</div>
          <div class="score">0-3</div>
          <div class="performer winner">Crazy Legs ✓</div>
        </article>
      </div>
    </div>

    <!-- Semi-Finals Column -->
    <div class="bracket-column">
      <h3>Semi-Finals</h3>
      <div class="bracket-matches">
        <article class="match in-progress">
          <div class="performer active">B-Boy Storm 🔴</div>
          <div class="score">Round 2/5</div>
          <div class="performer active">Crazy Legs 🔴</div>
        </article>
      </div>
    </div>

    <!-- Finals Column -->
    <div class="bracket-column">
      <h3>Finals</h3>
      <div class="bracket-matches">
        <article class="match pending">
          <div class="performer">Winner SF1</div>
          <div class="score">vs</div>
          <div class="performer">Winner SF2</div>
        </article>
      </div>
    </div>

    <!-- Champion Column -->
    <div class="bracket-column champion-column">
      <h3>Champion</h3>
      <div class="bracket-matches">
        <article class="champion-card">
          <div class="trophy">🏆</div>
          <div class="champion-name">TBD</div>
        </article>
      </div>
    </div>
  </div>

  <footer class="legend">
    <p>Legend: ✓ = Winner | 🔴 = In Progress | ⏳ = Pending</p>
    <p>Current: Finals • Storm vs Crazy Legs • Round 2 of 5</p>
  </footer>
</div>

<style>
/* Full-screen bracket styling */
#tournament-bracket {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #134e5e 0%, #71b280 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 2rem;
  font-family: 'Arial', sans-serif;
  overflow: hidden;
}

header {
  text-align: center;
  margin-bottom: 1rem;
}

header h1 {
  font-size: 2.5rem;
  margin: 0;
}

header h2 {
  font-size: 1.5rem;
  margin: 0.5rem 0;
  opacity: 0.9;
}

.bracket-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex: 1;
  gap: 2rem;
}

.bracket-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bracket-column h3 {
  font-size: 1.5rem;
  margin-bottom: 2rem;
  text-align: center;
}

.bracket-matches {
  display: flex;
  flex-direction: column;
  gap: 4rem;
  width: 100%;
}

.match {
  background: rgba(255,255,255,0.1);
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 0.5rem;
  padding: 1rem;
  text-align: center;
  min-width: 200px;
}

.match.completed {
  border-color: rgba(0,255,0,0.5);
  background: rgba(0,255,0,0.1);
}

.match.in-progress {
  border-color: #ff0000;
  background: rgba(255,0,0,0.2);
  animation: pulse-match 2s infinite;
}

@keyframes pulse-match {
  0%, 100% { border-color: #ff0000; }
  50% { border-color: #ff6666; }
}

.match.pending {
  opacity: 0.5;
}

.performer {
  font-size: 1.3rem;
  padding: 0.5rem;
  margin: 0.25rem 0;
}

.performer.winner {
  font-weight: bold;
  color: #00ff00;
}

.performer.active {
  font-weight: bold;
  color: #ffff00;
}

.score {
  font-size: 1.1rem;
  padding: 0.5rem;
  opacity: 0.8;
}

.champion-column {
  flex: 1.5;
}

.champion-card {
  background: rgba(255,215,0,0.2);
  border: 3px solid #ffd700;
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  min-width: 250px;
}

.trophy {
  font-size: 5rem;
  margin: 1rem 0;
}

.champion-name {
  font-size: 2rem;
  font-weight: bold;
  color: #ffd700;
}

.legend {
  text-align: center;
  font-size: 1.2rem;
  margin-top: 1rem;
  opacity: 0.8;
}

.legend p {
  margin: 0.25rem 0;
}
</style>
```

**Accessibility:**
- **Keyboard Navigation:** Not applicable (display-only screen)
- **Screen Reader Announcements:** Display is visual-only for audience
- **ARIA Labels:** Minimal (not interactive)
- **Focus Management:** No focus required

**Validation States:**
- **Loading Bracket:** Skeleton bracket structure with loading animation
- **Bracket Loaded:** Full bracket with all matches displayed
- **Match In Progress:** Active match highlighted with pulsing border
- **Match Complete:** Winner highlighted in green, score shown
- **Pending Match:** Grayed out with "TBD" placeholder
- **Champion Crowned:** Gold trophy and winner name displayed
- **Connection Lost:** Shows last known bracket state

---

## Section 14: UI Components & States

### 14.1 Delete Confirmation Modal

**Purpose:** Confirm destructive actions before executing (delete users, dancers, tournaments, categories).

**Permissions:** Based on parent action (typically Admin or Staff)

**User Interactions:**
1. User clicks "Delete" button on an item
2. Modal appears with confirmation message and item details
3. User can confirm deletion or cancel
4. On confirm: Item is deleted, modal closes, flash message shown
5. On cancel: Modal closes, no action taken

**Desktop Layout (> 768px):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                                                                              │
│                  ┌──────────────────────────────────────┐                    │
│                  │ ⚠️ Confirm Delete                    │                    │
│                  ├──────────────────────────────────────┤                    │
│                  │                                      │                    │
│                  │ Are you sure you want to delete     │                    │
│                  │ this dancer?                        │                    │
│                  │                                      │                    │
│                  │ Name: B-Boy Storm                   │                    │
│                  │ Blaze Name: storm                   │                    │
│                  │                                      │                    │
│                  │ This action cannot be undone.       │                    │
│                  │                                      │                    │
│                  │ ┌────────────┐  ┌────────────────┐ │                    │
│                  │ │   Cancel   │  │ Delete Dancer  │ │                    │
│                  │ └────────────┘  └────────────────┘ │                    │
│                  └──────────────────────────────────────┘                    │
│                                                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 768px):**
```
┌────────────────────────────┐
│ ⚠️ Confirm Delete          │
├────────────────────────────┤
│                            │
│ Are you sure you want to  │
│ delete this dancer?        │
│                            │
│ Name: B-Boy Storm          │
│ Blaze Name: storm          │
│                            │
│ This action cannot be      │
│ undone.                    │
│                            │
│ ┌────────────────────────┐ │
│ │      Cancel            │ │
│ └────────────────────────┘ │
│                            │
│ ┌────────────────────────┐ │
│ │   Delete Dancer        │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

**HTMX/JavaScript:**
```html
<!-- Delete button triggers modal -->
<button
  hx-get="/dancers/123/confirm-delete"
  hx-target="#modal-container"
  hx-swap="innerHTML"
  class="secondary"
>
  Delete
</button>

<!-- Modal container (initially empty) -->
<div id="modal-container"></div>

<!-- Modal content (returned by server) -->
<dialog open>
  <article>
    <header>
      <h3>⚠️ Confirm Delete</h3>
      <button
        aria-label="Close"
        onclick="this.closest('dialog').close()"
      >
        ✕
      </button>
    </header>

    <p>Are you sure you want to delete this dancer?</p>

    <dl>
      <dt>Name:</dt>
      <dd>B-Boy Storm</dd>
      <dt>Blaze Name:</dt>
      <dd>storm</dd>
    </dl>

    <p><strong>This action cannot be undone.</strong></p>

    <footer>
      <button
        class="secondary"
        onclick="this.closest('dialog').close()"
      >
        Cancel
      </button>
      <button
        hx-delete="/dancers/123"
        hx-confirm="Are you absolutely sure?"
        hx-target="closest dialog"
        hx-swap="delete"
        class="danger"
      >
        Delete Dancer
      </button>
    </footer>
  </article>
</dialog>

<style>
dialog {
  border: none;
  border-radius: 0.5rem;
  box-shadow: 0 0 20px rgba(0,0,0,0.3);
  max-width: 500px;
  padding: 0;
}

dialog::backdrop {
  background: rgba(0,0,0,0.5);
}

dialog article {
  margin: 0;
}

dialog header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--pico-muted-border-color);
  padding: 1rem;
}

dialog header button {
  padding: 0.5rem;
  margin: 0;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

dialog footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  border-top: 1px solid var(--pico-muted-border-color);
  padding: 1rem;
}

button.danger {
  background: var(--pico-del-color);
  border-color: var(--pico-del-color);
}
</style>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Modal opens with focus on "Cancel" button
  - Tab cycles through buttons within modal
  - Esc key closes modal
- **Screen Reader Announcements:**
  - Modal announced: "Dialog: Confirm Delete"
  - Item details read out
  - Warning message emphasized
- **ARIA Labels:**
  - Dialog: `role="dialog"`, `aria-labelledby="dialog-title"`
  - Close button: `aria-label="Close dialog"`
  - Delete button: `aria-label="Delete dancer B-Boy Storm"`
- **Focus Management:**
  - Focus trapped within modal while open
  - Focus returns to triggering button on close

**Validation States:**
- **Modal Closed:** Not visible
- **Modal Open:** Visible with backdrop
- **Confirming:** Delete button shows loading state
- **Deletion Success:** Modal closes, flash message appears
- **Deletion Error:** Error message shown in modal

---

### 14.2 Flash Message System

**Purpose:** Provide user feedback for actions (success, error, warning, info).

**Permissions:** Available to all authenticated users

**User Interactions:**
1. Action triggers a flash message (e.g., "Dancer created successfully")
2. Message appears at top of page with appropriate styling
3. Message auto-dismisses after 5 seconds
4. User can manually dismiss by clicking X button

**Desktop & Mobile Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✅ Success: Dancer created successfully                              [✕]    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ❌ Error: Email is already registered                                [✕]    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ Warning: Tournament will be locked once registration closes       [✕]    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ℹ️ Info: Performers will be notified via email                       [✕]    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**HTMX/JavaScript:**
```html
<!-- Flash messages container (at top of page) -->
<div id="flash-messages" aria-live="polite" aria-atomic="true">
  <!-- Success message -->
  <article class="flash-message success" data-auto-dismiss="5000">
    <span class="icon">✅</span>
    <span class="message">Success: Dancer created successfully</span>
    <button
      class="close"
      onclick="this.parentElement.remove()"
      aria-label="Dismiss message"
    >
      ✕
    </button>
  </article>

  <!-- Error message -->
  <article class="flash-message error" data-auto-dismiss="5000">
    <span class="icon">❌</span>
    <span class="message">Error: Email is already registered</span>
    <button
      class="close"
      onclick="this.parentElement.remove()"
      aria-label="Dismiss message"
    >
      ✕
    </button>
  </article>

  <!-- Warning message -->
  <article class="flash-message warning" data-auto-dismiss="5000">
    <span class="icon">⚠️</span>
    <span class="message">Warning: Tournament will be locked once registration closes</span>
    <button
      class="close"
      onclick="this.parentElement.remove()"
      aria-label="Dismiss message"
    >
      ✕
    </button>
  </article>

  <!-- Info message -->
  <article class="flash-message info" data-auto-dismiss="5000">
    <span class="icon">ℹ️</span>
    <span class="message">Info: Performers will be notified via email</span>
    <button
      class="close"
      onclick="this.parentElement.remove()"
      aria-label="Dismiss message"
    >
      ✕
    </button>
  </article>
</div>

<style>
#flash-messages {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 500px;
}

.flash-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.flash-message.success {
  background: #d4edda;
  color: #155724;
  border-left: 4px solid #28a745;
}

.flash-message.error {
  background: #f8d7da;
  color: #721c24;
  border-left: 4px solid #dc3545;
}

.flash-message.warning {
  background: #fff3cd;
  color: #856404;
  border-left: 4px solid #ffc107;
}

.flash-message.info {
  background: #d1ecf1;
  color: #0c5460;
  border-left: 4px solid #17a2b8;
}

.flash-message .icon {
  font-size: 1.5rem;
}

.flash-message .message {
  flex: 1;
}

.flash-message .close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  margin: 0;
  opacity: 0.7;
}

.flash-message .close:hover {
  opacity: 1;
}

@media (max-width: 768px) {
  #flash-messages {
    right: 0.5rem;
    left: 0.5rem;
    max-width: none;
  }
}
</style>

<script>
// Auto-dismiss flash messages
document.querySelectorAll('.flash-message[data-auto-dismiss]').forEach(msg => {
  const delay = parseInt(msg.dataset.autoDismiss);
  setTimeout(() => {
    msg.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => msg.remove(), 300);
  }, delay);
});
</script>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Close button focusable with Tab
  - Enter/Space to dismiss
- **Screen Reader Announcements:**
  - Messages announced immediately via `aria-live="polite"`
  - Type and content read out
- **ARIA Labels:**
  - Container: `aria-live="polite"`, `aria-atomic="true"`
  - Close button: `aria-label="Dismiss message"`
- **Focus Management:**
  - Focus not forced to message (polite)
  - Close button receives focus on Tab

**Validation States:**
- **No Messages:** Container empty
- **Message Appearing:** Slide-in animation
- **Message Active:** Fully visible, auto-dismiss timer running
- **Message Dismissing:** Fade-out animation
- **Multiple Messages:** Stacked vertically with gap

---

### 14.3 Loading States

**Purpose:** Provide visual feedback during async operations (data fetching, form submission).

**Types:**
1. **Button Loading:** Spinner inside button during form submission
2. **Page Loading:** Full-page spinner during navigation
3. **Skeleton Loading:** Placeholder content while data loads
4. **Progress Bar:** For long-running operations

**Button Loading:**
```html
<button
  hx-post="/dancers"
  hx-indicator="#spinner"
  data-loading-text="Creating..."
>
  <span class="button-text">Create Dancer</span>
  <span id="spinner" class="htmx-indicator spinner"></span>
</button>

<style>
.spinner {
  display: none;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.htmx-request .htmx-indicator.spinner {
  display: inline-block;
}

.htmx-request .button-text {
  display: none;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
```

**Skeleton Loading:**
```html
<article class="skeleton">
  <div class="skeleton-header"></div>
  <div class="skeleton-line"></div>
  <div class="skeleton-line"></div>
  <div class="skeleton-line short"></div>
</article>

<style>
.skeleton {
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-header {
  width: 60%;
  height: 2rem;
  background: var(--pico-muted-border-color);
  border-radius: 0.25rem;
  margin-bottom: 1rem;
}

.skeleton-line {
  width: 100%;
  height: 1rem;
  background: var(--pico-muted-border-color);
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.skeleton-line.short {
  width: 40%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
```

**Progress Bar:**
```html
<div class="progress-container">
  <p>Processing tournament calculations...</p>
  <progress value="60" max="100">60%</progress>
  <small>60% complete</small>
</div>

<style>
.progress-container {
  text-align: center;
  padding: 2rem;
}

progress {
  width: 100%;
  height: 2rem;
  border-radius: 1rem;
  overflow: hidden;
}

progress::-webkit-progress-bar {
  background: var(--pico-muted-border-color);
}

progress::-webkit-progress-value {
  background: var(--pico-primary);
  transition: width 0.3s ease;
}
</style>
```

**Accessibility:**
- **ARIA Labels:**
  - Loading button: `aria-busy="true"` during request
  - Progress bar: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
  - Skeleton: `aria-busy="true"`, `aria-label="Loading content"`
- **Screen Reader Announcements:**
  - "Loading..." announced when state changes
  - Progress percentage announced as it updates

---

### 14.4 Empty States

**Purpose:** Inform users when no data exists or results are empty.

**Types:**
1. **No Data:** When database is empty (e.g., no dancers yet)
2. **No Results:** When search/filter returns nothing
3. **No Permissions:** When user lacks access to view content

**No Data State:**
```
┌────────────────────────────┐
│                            │
│         📋                 │
│                            │
│    No Dancers Yet          │
│                            │
│  Create your first dancer  │
│  to get started.           │
│                            │
│  ┌────────────────────┐    │
│  │  + Create Dancer   │    │
│  └────────────────────┘    │
│                            │
└────────────────────────────┘
```

**No Results State:**
```
┌────────────────────────────┐
│                            │
│         🔍                 │
│                            │
│  No dancers found          │
│                            │
│  Try adjusting your        │
│  search or filters.        │
│                            │
│  ┌────────────────────┐    │
│  │  Clear Filters     │    │
│  └────────────────────┘    │
│                            │
└────────────────────────────┘
```

**No Permissions State:**
```
┌────────────────────────────┐
│                            │
│         🔒                 │
│                            │
│  Access Restricted         │
│                            │
│  You don't have permission │
│  to view this content.     │
│                            │
│  Contact an administrator  │
│  for access.               │
│                            │
└────────────────────────────┘
```

**HTML/CSS:**
```html
<!-- No Data -->
<article class="empty-state">
  <div class="empty-icon">📋</div>
  <h3>No Dancers Yet</h3>
  <p>Create your first dancer to get started.</p>
  <a href="/dancers/new" role="button">+ Create Dancer</a>
</article>

<!-- No Results -->
<article class="empty-state">
  <div class="empty-icon">🔍</div>
  <h3>No dancers found</h3>
  <p>Try adjusting your search or filters.</p>
  <button
    hx-get="/dancers"
    hx-target="#dancers-list"
    hx-swap="outerHTML"
  >
    Clear Filters
  </button>
</article>

<!-- No Permissions -->
<article class="empty-state">
  <div class="empty-icon">🔒</div>
  <h3>Access Restricted</h3>
  <p>You don't have permission to view this content.</p>
  <p><small>Contact an administrator for access.</small></p>
</article>

<style>
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--pico-background-color);
  border: 1px dashed var(--pico-muted-border-color);
  border-radius: 0.5rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin-bottom: 0.5rem;
}

.empty-state p {
  margin-bottom: 1.5rem;
  opacity: 0.8;
}
</style>
```

**Accessibility:**
- **Screen Reader Announcements:**
  - Empty state announced as article with heading
  - Clear instructions provided
- **ARIA Labels:**
  - Icon: `aria-hidden="true"` (decorative)
  - Action button: Clear call-to-action text

---

### 14.5 Error States

**Purpose:** Handle and display errors gracefully with recovery options.

**Types:**
1. **404 Not Found:** Page or resource doesn't exist
2. **500 Server Error:** Internal server error
3. **Network Error:** Connection failure
4. **Validation Error:** Form field errors (covered in individual pages)

**404 Not Found:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                                   404                                        │
│                                                                              │
│                              Page Not Found                                  │
│                                                                              │
│                 The page you're looking for doesn't exist.                   │
│                 It may have been moved or deleted.                           │
│                                                                              │
│                          ┌──────────────────┐                                │
│                          │  Back to Home    │                                │
│                          └──────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**500 Server Error:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                                   500                                        │
│                                                                              │
│                          Something Went Wrong                                │
│                                                                              │
│                 An unexpected error occurred on our servers.                 │
│                 We've been notified and are working on it.                   │
│                                                                              │
│                          ┌──────────────────┐                                │
│                          │   Try Again      │                                │
│                          └──────────────────┘                                │
│                                                                              │
│                          Error ID: abc123def456                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Network Error:**
```
┌────────────────────────────┐
│         ⚠️                 │
│                            │
│  Connection Lost           │
│                            │
│  Unable to reach server.   │
│  Check your internet       │
│  connection and try again. │
│                            │
│  ┌────────────────────┐    │
│  │    Retry           │    │
│  └────────────────────┘    │
└────────────────────────────┘
```

**HTML/CSS:**
```html
<!-- 404 Error -->
<main class="error-page">
  <article>
    <h1>404</h1>
    <h2>Page Not Found</h2>
    <p>The page you're looking for doesn't exist.</p>
    <p>It may have been moved or deleted.</p>
    <a href="/" role="button">Back to Home</a>
  </article>
</main>

<!-- 500 Error -->
<main class="error-page">
  <article>
    <h1>500</h1>
    <h2>Something Went Wrong</h2>
    <p>An unexpected error occurred on our servers.</p>
    <p>We've been notified and are working on it.</p>
    <button
      onclick="location.reload()"
    >
      Try Again
    </button>
    <small>Error ID: {{ error_id }}</small>
  </article>
</main>

<!-- Network Error (HTMX response) -->
<article class="error-state network-error">
  <div class="error-icon">⚠️</div>
  <h3>Connection Lost</h3>
  <p>Unable to reach server. Check your internet connection and try again.</p>
  <button
    hx-get="{{ current_url }}"
    hx-target="closest article"
    hx-swap="outerHTML"
  >
    Retry
  </button>
</article>

<style>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  text-align: center;
}

.error-page h1 {
  font-size: 6rem;
  margin: 0;
  opacity: 0.3;
}

.error-page h2 {
  font-size: 2rem;
  margin: 1rem 0;
}

.error-page p {
  margin: 0.5rem 0;
  opacity: 0.8;
}

.error-page button,
.error-page a[role="button"] {
  margin-top: 2rem;
}

.error-state {
  text-align: center;
  padding: 3rem 2rem;
  background: var(--pico-background-color);
  border: 2px solid var(--pico-del-color);
  border-radius: 0.5rem;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-state h3 {
  color: var(--pico-del-color);
  margin-bottom: 1rem;
}
</style>
```

**Accessibility:**
- **Keyboard Navigation:**
  - Error page action button is focusable
  - Tab navigates to retry/home buttons
- **Screen Reader Announcements:**
  - Error announced with code and description
  - Recovery options clearly stated
- **ARIA Labels:**
  - Error container: `role="alert"` for critical errors
  - Retry button: `aria-label="Retry failed operation"`
- **Focus Management:**
  - Focus moves to error message or retry button

**Validation States:**
- **404:** Static page, no dynamic states
- **500:** Static page, retry button may reload
- **Network Error:** Retry button triggers new request
- **Recovery Success:** Error state replaced with normal content
- **Recovery Failure:** Error state persists, message updated

---

## Accessibility Guidelines

### Keyboard Navigation

**Tab Order:** Logical flow through interactive elements

**Required Interactions:**
- `Tab` - Move to next element
- `Shift + Tab` - Move to previous element
- `Enter` - Activate links and buttons
- `Space` - Toggle checkboxes, activate buttons
- `Esc` - Close modals (Phase 4)

**Skip Links:** (Phase 4 enhancement)
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
```

### Screen Reader Support

**Semantic HTML:**
- `<nav>` for navigation
- `<main>` for main content
- `<article>` for self-contained content
- `<section>` for thematic grouping
- `<header>` and `<footer>` within sections

**ARIA Labels:**
```html
<!-- Form fields with errors -->
<input
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<small id="email-error" role="alert">Email is required</small>

<!-- Loading states -->
<div aria-live="polite" aria-busy="true">
  Loading dancers...
</div>

<!-- Dynamic updates -->
<div role="status" aria-live="polite">
  Dancer registered successfully
</div>
```

### Color Contrast

**WCAG AA Requirements:**
- Text: 4.5:1 contrast ratio minimum
- Large text (18pt+): 3:1 minimum
- UI components: 3:1 minimum

**PicoCSS Defaults:** Meet WCAG AA in both light and dark modes

**Custom Colors:** Test with contrast checker before implementation

### Focus Indicators

**Visible Focus:** All interactive elements show clear focus state

**PicoCSS Default:** Blue outline (customizable via CSS variables)

**Custom Enhancement:**
```css
:focus-visible {
  outline: 3px solid var(--pico-primary);
  outline-offset: 2px;
}
```

---

## Responsive Design

### Mobile Optimizations

**Touch Targets:**
- Minimum size: 44x44px
- Spacing between targets: 8px minimum

**Typography:**
- Base font size: 16px (prevents zoom on iOS)
- Line height: 1.5 (comfortable reading)
- Max line length: 70 characters (readability)

**Forms:**
- Full-width inputs on mobile
- Stacked buttons (one per row)
- Large tap targets for radio/checkbox

**Tables:**
- Transform to cards on mobile (CSS)
- `data-label` attribute for context

### Tablet Considerations

**Breakpoint:** 769px - 1024px

**Layout:**
- Sidebar: Reduce to 200px or collapse
- Content: Maintain readability (max-width constraint)
- Forms: Allow two-column layouts where appropriate

### Desktop Enhancements

**Multi-Column Layouts:**
- Dashboard: 2-3 column grid for cards
- Forms: Side-by-side inputs where logical (first/last name)
- Tables: Full table layout with more columns visible

**Hover States:**
- Links: Underline on hover
- Buttons: Darken background
- Cards: Subtle shadow or border change

---

## Implementation Roadmap

### Phase 1.1 ✅ COMPLETE (Current)

**Goal:** Core UI foundation with PicoCSS

**Completed:**
- ✅ PicoCSS integration
- ✅ Vertical sidebar navigation
- ✅ Dashboard → Overview rename
- ✅ Base template restructure
- ✅ Responsive grid layout
- ✅ All 97 tests passing

**Templates Updated:**
- `base.html` - Sidebar, grid layout, PicoCSS
- `overview.html` - Renamed from dashboard, new design
- Auth redirect - Updated to `/overview`

### Phase 2: Battle Management (35% Infrastructure)

**Goal:** Battle generation, judging interface, real-time updates

**UI Components Needed:**
- Battle list page (auto-refresh with HTMX)
- Judge scoring interface
- Battle detail view
- Pool standings table
- MC battle management (start/stop battles)

**Technical Challenges:**
- Real-time updates (HTMX polling vs WebSockets)
- Judge synchronization (multiple judges scoring same battle)
- Battle state management (Ready → In Progress → Completed)

**Estimated Templates:** 10 new templates

### Phase 3: Projection Display

**Goal:** Public-facing display for tournament projection

**UI Components Needed:**
- Full-screen battle view (current battle, performers)
- Pool standings leaderboard
- Upcoming battles queue
- Sponsor slides (between battles)
- Tournament bracket visualization

**Technical Approach:**
- Separate layout (no sidebar, full-screen)
- Auto-refresh with HTMX
- Minimal interaction (read-only)

**Estimated Templates:** 5 new templates

### Phase 4: Polish & Enhancement

**Goal:** Production-ready polish and UX improvements

**Enhancements:**
- Delete confirmation modals
- Flash message system (success/error notifications)
- Inline form validation (live feedback)
- Search improvements (fuzzy matching, filters)
- Bulk actions (delete multiple dancers/users)
- Activity logs/audit trail
- Advanced keyboard shortcuts
- Print stylesheets (for tournament reports)

**Accessibility:**
- WCAG 2.1 AAA compliance (stretch goal)
- Complete screen reader testing
- Keyboard navigation testing
- Color contrast audit

**Performance:**
- Lazy loading for large tables
- Image optimization
- CSS/JS minification
- CDN for static assets

**Estimated Effort:** 3-4 weeks

### Phase 5: Judge-Specific Features (V2)

**Goal:** Advanced judging capabilities (V2 feature - judges score battles directly)

**Features:**
- Judge assignments (assign judges to tournaments)
- Scoring history (view past scores)
- Judge calibration (compare scores across judges)
- Conflict of interest management (judge cannot score own crew)
- Score normalization (adjust for judge bias)

**Estimated Templates:** 8 new templates

---

## Design Tokens (PicoCSS Variables)

### Colors

**Primary:**
- `--pico-primary`: Main brand color (blue)
- `--pico-primary-background`: Button/badge backgrounds
- `--pico-primary-hover-background`: Hover states

**Secondary:**
- `--pico-secondary`: Secondary actions (gray)
- `--pico-secondary-background`: Cancel buttons
- `--pico-secondary-hover-background`: Hover states

**Semantic:**
- `--pico-contrast`: High contrast (delete buttons)
- `--pico-muted-color`: Disabled states, placeholders
- `--pico-muted-border-color`: Borders, dividers

### Spacing

**PicoCSS Defaults:**
- `1rem` = 16px (base unit)
- Padding: 1rem (forms, buttons)
- Margin: 1rem (vertical rhythm)

**Custom Spacing:**
```css
:root {
  --spacing-xs: 0.25rem;  /* 4px */
  --spacing-sm: 0.5rem;   /* 8px */
  --spacing-md: 1rem;     /* 16px */
  --spacing-lg: 2rem;     /* 32px */
  --spacing-xl: 4rem;     /* 64px */
}
```

### Typography

**PicoCSS Defaults:**
- Font family: System font stack (no web fonts)
- Base size: 16px
- Scale: 1.25 (headings)

**Headings:**
- `h1`: 2.5rem (40px)
- `h2`: 2rem (32px)
- `h3`: 1.5rem (24px)

### Borders & Shadows

**Borders:**
- Radius: 0.25rem (4px)
- Width: 1px
- Color: `var(--pico-muted-border-color)`

**Shadows:**
- None by default (minimalist approach)
- Optional: Subtle shadow on cards (Phase 4)

---

## Version History

- **v1.0** (2025-01-19) - Original documentation (as-built reference)
- **v2.0** (2025-11-20) - Complete UX redesign with PicoCSS, minimalist principles, user flows

---

**Next Steps:**
1. Implement Phase 2 battle management UI
2. User testing on mobile devices
3. Accessibility audit with screen readers
4. Performance optimization (lazy loading, caching)
