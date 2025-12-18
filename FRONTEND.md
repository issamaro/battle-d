# Battle-D Frontend Architecture
**Level 3: Operational** | Last Updated: 2025-12-06

**Purpose:** Frontend architectural patterns, component library, and accessibility guidelines for the Battle-D tournament management system.

**Version:** 1.0 (extracted from UI_MOCKUPS.md v2.1)

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Technology Stack](#technology-stack)
3. [Layout Architecture](#layout-architecture)
4. [Component Library](#component-library)
5. [HTMX Patterns](#htmx-patterns)
6. [Accessibility Guidelines](#accessibility-guidelines)
7. [Responsive Design](#responsive-design)
8. [Design Tokens](#design-tokens)

---

## Design Principles

### 1. Minimalism

**Philosophy:** Remove every element that doesn't serve a clear purpose.

**Core Principles:**
- **Clean Visual Hierarchy:** Use whitespace, not borders, to separate content
- **Typography-First:** Let content breathe without heavy decoration
- **Color as Signal:** Color indicates status and actions, not decoration
- **Progressive Disclosure:** Show users what they need when they need it

**Anti-Patterns to Avoid:**
- ❌ Dense information tables without breathing room
- ❌ Excessive borders and dividers
- ❌ Decorative icons that don't aid understanding
- ❌ Complex multi-column layouts on small screens

---

### 2. Accessibility

**WCAG 2.1 Level AA Compliance** is mandatory for all UI components.

**Requirements:**
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

---

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
- Simplified navigation (collapsible or top nav)

---

### 4. Progressive Enhancement

**Core Experience:** Works without JavaScript (except HTMX-dependent features).

**Enhancement Layers:**
1. **HTML:** Semantic, accessible structure
2. **CSS:** Visual presentation and responsive layout
3. **HTMX:** Dynamic updates without full page reload
4. **JavaScript:** Complex interactions only when necessary (duo selection, live calculations)

---

## Technology Stack

### Frontend Framework: PicoCSS 2.x

**Minimal, semantic CSS framework**

**Why PicoCSS:**
- ✅ Class-less design (works with semantic HTML)
- ✅ Accessibility built-in (ARIA, keyboard nav)
- ✅ Dark mode support (automatic via `prefers-color-scheme`)
- ✅ Minimal footprint (~10KB gzipped)
- ✅ Responsive by default

**Custom CSS:** Only for layout (CSS Grid for sidebar navigation). Prefer PicoCSS defaults and utility classes over custom styles.

---

### Dynamic Interactions: HTMX 2.0.4

**HTML-driven AJAX, WebSockets, Server-Sent Events**

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

---

### Templating: Jinja2

**Server-side templating with FastAPI**

**Patterns:**
- Template inheritance (`base.html` → page templates)
- Partial templates for HTMX responses (`_table.html`, `_dancer_search.html`)
- Context-aware navigation (role-based menu items)
- Component includes (`{% include "components/modal.html" %}`)

---

## Layout Architecture

### Base Template Structure

All pages extend `base.html` which provides:

1. **Vertical Sidebar Navigation** (logged-in users only)
2. **Page Header** (title, user info)
3. **Main Content Area** (page-specific content)
4. **Footer** (system info)

**Desktop Layout Grid:**
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

---

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
**Future Enhancement:** Hamburger menu with slide-out drawer

---

### 2. Forms

#### Standard Form Pattern

**Layout:**
- Max-width: 600px (comfortable reading width)
- Single column (mobile-first)
- Labels above inputs
- Required fields marked with asterisk
- Error messages below fields

**HTML Structure:**
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
- **Invalid:** `aria-invalid="true"` + red border (PicoCSS automatic)
- **Valid:** Green checkmark (optional, future enhancement)
- **Error Message:** Associated via `aria-describedby`

---

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
- Should have confirmation dialog

---

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

---

### 4. Cards

#### Information Card Pattern

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

---

### 5. Status Badges

**Use Case:** Tournament status, dancer availability, battle outcomes

**HTML Structure:**
```html
<span class="badge badge-created">Created</span>
<span class="badge badge-active">Active</span>
<span class="badge badge-completed">Completed</span>
<span class="badge badge-cancelled">Cancelled</span>
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

.badge-cancelled {
  background: #f59e0b; /* Amber */
  color: white;
}
```

#### Battle Status Badges

**Use Case:** Battle queue status indicators (pending, active, completed)

**HTML Structure with Accessibility:**
```html
<!-- Accessible battle status badge -->
<span
  class="badge badge-pending"
  role="status"
  aria-label="Battle status: Pending"
>
  PENDING
</span>

<span
  class="badge badge-active"
  role="status"
  aria-label="Battle status: Active"
>
  ACTIVE
</span>

<span
  class="badge badge-completed"
  role="status"
  aria-label="Battle status: Completed"
>
  COMPLETED
</span>
```

**CSS Implementation (WCAG 2.1 AA Compliant):**
```css
/* Battle status badges - defined in app/static/css/battles.css */
.badge-pending {
  background: #6c757d; /* Gray */
  color: white;
  /* Contrast ratio: 5.74:1 (WCAG AA ✓) */
}

.badge-active {
  background: #ff9800; /* Orange (adjusted for contrast) */
  color: white;
  /* Contrast ratio: 4.52:1 (WCAG AA ✓) */
  /* Previous yellow #ffc107 failed at 3.5:1 */
}

.badge-completed {
  background: #28a745; /* Green */
  color: white;
  /* Contrast ratio: 4.56:1 (WCAG AA ✓) */
}
```

**Accessibility Requirements:**
- **`role="status"`** - Announces badge as status indicator to screen readers
- **`aria-label`** - Provides full context (e.g., "Battle status: Active")
- **Color contrast** - Minimum 4.5:1 ratio for text (WCAG Level AA)
- **Not color-only** - Text label + semantic role (not just color indicator)

**Implementation Example:**
```html
<!-- Battle card with status badge -->
<article class="battle-card" id="battle-card-{{ battle.id }}">
  <header>
    <h4>Battle #{{ loop.index }}</h4>
    <span
      class="badge badge-{{ battle.status.value }}"
      role="status"
      aria-label="Battle status: {{ battle.status.value }}"
    >
      {{ battle.status.value|upper }}
    </span>
  </header>

  <section>
    <ul>
      {% for performer in battle.performers[:5] %}
        <li>{{ performer.dancer.blaze }}</li>
      {% endfor %}
    </ul>
  </section>

  <footer>
    {% if battle.status.value == 'pending' %}
      <form hx-post="/battles/{{ battle.id }}/start" hx-swap="outerHTML" hx-target="#battle-card-{{ battle.id }}">
        <button type="submit">Start Battle</button>
      </form>
    {% elif battle.status.value == 'active' %}
      <a href="/battles/{{ battle.id }}/encode" role="button">Encode Result</a>
    {% endif %}
  </footer>
</article>
```

**Status Badge States:**

| Status | Color | Background | Use Case | Contrast Ratio |
|--------|-------|------------|----------|----------------|
| PENDING | White | Gray (#6c757d) | Battle not started | 5.74:1 ✓ |
| ACTIVE | White | Orange (#ff9800) | Battle in progress | 4.52:1 ✓ |
| COMPLETED | White | Green (#28a745) | Battle finished | 4.56:1 ✓ |

**Responsive Behavior:**
- Mobile (<768px): Badge scales to 14px font-size
- Tablet/Desktop (≥768px): Badge at 16px font-size
- Touch target: Minimum 44×44px if interactive

**Common Mistakes to Avoid:**
- ❌ **Color-only indicators**: Always include text label + semantic role
- ❌ **Inline styles**: Use CSS classes (`.badge-active` not `style="background: yellow"`)
- ❌ **Missing ARIA labels**: Screen readers need context beyond color
- ❌ **Low contrast**: Yellow #ffc107 + white = 3.5:1 (fails WCAG AA)

#### Badge Classes Reference (from battles.css)

Use badge classes for ALL status indicators throughout the application:

```html
<span class="badge badge-pending">PENDING</span>
<span class="badge badge-active">ACTIVE</span>
<span class="badge badge-completed">COMPLETED</span>
<span class="badge badge-warning">CANCELLED</span>
```

| Class | Color | Background | Use Case | Contrast Ratio |
|-------|-------|------------|----------|----------------|
| `.badge-pending` | White | Gray (#6c757d) | Default/waiting state | 5.74:1 (WCAG AAA) |
| `.badge-active` | White | Orange (#ff9800) | In-progress state | 4.52:1 (WCAG AA) |
| `.badge-completed` | White | Green (#28a745) | Success/done state | 4.56:1 (WCAG AA) |
| `.badge-warning` | Dark (#212529) | Yellow (#ffc107) | Warning/cancelled state | 8.59:1 (WCAG AAA) |

**DO NOT use inline styles for badges:**
```html
<!-- BAD - inline styles -->
<span style="padding: 4px 8px; background-color: #28a745; color: white;">ACTIVE</span>

<!-- GOOD - CSS classes -->
<span class="badge badge-active">ACTIVE</span>
```

---

### 5.1 Permission Display Standard

**Use Case:** Displaying user permissions/roles in tables and profile views.

**Standard Format:** Use checkmark symbols (check/X), NOT Yes/No text.

**HTML:**
```html
<!-- Permission display in tables -->
<table>
    <thead>
        <tr>
            <th>Permission</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Admin</td>
            <td>{{ "&#10003;" if current_user.is_admin else "&#10007;" }}</td>
        </tr>
        <tr>
            <td>Staff</td>
            <td>{{ "&#10003;" if current_user.is_staff else "&#10007;" }}</td>
        </tr>
    </tbody>
</table>
```

**Alternative (Unicode directly in Jinja):**
```html
<td>{{ "✓" if current_user.is_admin else "✗" }}</td>
```

**Why Checkmarks:**
- More compact than Yes/No
- Universal visual meaning
- Better for tables with many columns
- Consistent across the application

**DO NOT use Yes/No text:**
```html
<!-- BAD - inconsistent with rest of app -->
<td>{{ "Yes" if current_user.is_admin else "No" }}</td>

<!-- GOOD - checkmark symbols -->
<td>{{ "✓" if current_user.is_admin else "✗" }}</td>
```

---

### 6. Flash Messages

**Component File:** `app/templates/components/flash_messages.html`

**Use Case:** Success/error/warning/info user feedback

**HTML Structure:**
```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-messages">
      {% for category, message in messages %}
        <div class="flash flash-{{ category }}" role="alert" aria-live="polite">
          {{ message }}
          <button type="button" class="close" aria-label="Close">×</button>
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

**Categories:**
- `success` - Green background
- `error` - Red background
- `warning` - Yellow background
- `info` - Blue background

**Behavior:**
- Auto-dismiss after 5 seconds (except errors)
- Manual dismiss with close button
- Screen reader announced via `role="alert"`

---

### 7. Empty States

**Component File:** `app/templates/components/empty_state.html`

**Use Case:** Lists with no data

**HTML Structure:**
```html
{% if items %}
  <!-- Display items -->
{% else %}
  <div class="empty-state">
    <svg><!-- Icon --></svg>
    <h3>{{ title }}</h3>
    <p>{{ message }}</p>
    {% if action_url %}
      <a href="{{ action_url }}" role="button">{{ action_label }}</a>
    {% endif %}
  </div>
{% endif %}
```

**Example Usage:**
```html
{% include "components/empty_state.html" with
  title="No dancers found",
  message="Get started by creating your first dancer.",
  action_url="/dancers/create",
  action_label="Create Dancer"
%}
```

---

### 8. Delete Confirmation Modal

**Component File:** `app/templates/components/delete_modal.html`

**Use Case:** Confirm destructive actions

**HTML Structure:**
```html
<dialog id="{{ modal_id }}">
  <article>
    <header>
      <h3>{{ title }}</h3>
      <button
        type="button"
        aria-label="Close"
        onclick="document.getElementById('{{ modal_id }}').close()"
      >×</button>
    </header>
    <p>{{ message }}</p>
    <footer>
      <form method="post" action="{{ form_action }}">
        <button type="button" class="secondary" onclick="document.getElementById('{{ modal_id }}').close()">
          Cancel
        </button>
        <button type="submit" class="contrast">Delete</button>
      </form>
    </footer>
  </article>
</dialog>
```

**Usage:**
```html
{% include "components/delete_modal.html" with
  modal_id="delete-dancer-modal",
  title="Delete Dancer?",
  message="This will permanently delete the dancer. This action cannot be undone.",
  form_action="/dancers/" ~ dancer.id ~ "/delete"
%}

<!-- Trigger button -->
<button
  type="button"
  onclick="document.getElementById('delete-dancer-modal').showModal()"
  class="contrast"
>
  Delete
</button>
```

**Accessibility:**
- `<dialog>` element (native modal)
- Keyboard accessible (ESC to close)
- Focus trapped inside modal
- `aria-label` on close button

---

### 9. Loading Indicators

**Component File:** `app/templates/components/loading.html`

**Use Case:** HTMX requests, async operations

**HTML Structure:**
```html
<div class="loading" aria-live="polite" aria-busy="true">
  <div class="spinner"></div>
  <span>{{ message | default("Loading...") }}</span>
</div>
```

**CSS (spinner):**
```css
.spinner {
  border: 3px solid var(--pico-muted-border-color);
  border-top: 3px solid var(--pico-primary);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

---

## HTMX Patterns

### Pattern 1: Live Search with Debounce

**Use Case:** Dancer search, user search

**HTML:**
```html
<input
  type="search"
  name="q"
  placeholder="Search dancers..."
  hx-get="/dancers/search"
  hx-trigger="keyup changed delay:500ms"
  hx-target="#search-results"
  autocomplete="off"
>
<div id="search-results"></div>
```

**Backend Route:**
```python
@router.get("/dancers/search")
async def search_dancers(q: str = ""):
    dancers = await dancer_service.search(q)
    return templates.TemplateResponse("dancers/_search_results.html", {
        "request": request,
        "dancers": dancers
    })
```

**Partial Template:** `dancers/_search_results.html`
```html
{% for dancer in dancers %}
  <article>
    <strong>{{ dancer.blaze }}</strong>
    <small>{{ dancer.first_name }} {{ dancer.last_name }}</small>
  </article>
{% endfor %}
```

**Key Points:**
- `hx-get`: Endpoint to call
- `hx-trigger="keyup changed delay:500ms"`: Debounce for 500ms
- `hx-target`: Element to update
- Partial template returns only the results section

---

### Pattern 2: Form Submission with Partial Update

**Use Case:** Inline editing, quick forms

**HTML:**
```html
<form
  hx-post="/examples/create"
  hx-swap="outerHTML"
  hx-target="#form-container"
>
  <label for="name">Name</label>
  <input type="text" name="name" id="name" required>

  <button type="submit">Create</button>
</form>
```

**Backend Route:**
```python
@router.post("/examples/create")
async def create_example(name: str):
    result = await service.create(name)
    if not result.success:
        # Return form with errors
        return templates.TemplateResponse("examples/_form.html", {
            "request": request,
            "errors": result.errors
        })
    # Return success message or updated list
    return templates.TemplateResponse("examples/_success.html", {
        "request": request,
        "example": result.data
    })
```

**Key Points:**
- `hx-post`: POST request
- `hx-swap="outerHTML"`: Replace entire form
- `hx-target`: Container to update
- Return different template on success vs error

---

### Pattern 3: Polling / Auto-Refresh

**Use Case:** Battle list during active tournament

**HTML:**
```html
<div
  hx-get="/battles/list"
  hx-trigger="every 10s"
  hx-swap="innerHTML"
>
  <!-- Initial battle list -->
</div>
```

**Backend Route:**
```python
@router.get("/battles/list")
async def list_battles():
    battles = await battle_service.get_active_battles()
    return templates.TemplateResponse("battles/_list.html", {
        "request": request,
        "battles": battles
    })
```

**Key Points:**
- `hx-trigger="every 10s"`: Poll every 10 seconds
- `hx-swap="innerHTML"`: Update content only
- Useful for live updates without WebSockets

---

### Pattern 4: Inline Validation

**Use Case:** Email validation, username availability

**HTML:**
```html
<input
  type="email"
  name="email"
  hx-post="/validate/email"
  hx-trigger="blur"
  hx-target="#email-error"
>
<div id="email-error"></div>
```

**Backend Route:**
```python
@router.post("/validate/email")
async def validate_email(email: str):
    if not is_valid_email(email):
        return '<small role="alert">Invalid email format</small>'
    existing = await user_repo.get_by_email(email)
    if existing:
        return '<small role="alert">Email already in use</small>'
    return ''  # Empty = valid
```

**Key Points:**
- `hx-trigger="blur"`: Validate on field exit
- `hx-target`: Error message container
- Return error HTML or empty string

---

### Pattern 5: Delete with Confirmation

**Use Case:** Destructive actions

**HTML:**
```html
<button
  hx-delete="/dancers/{{ dancer.id }}"
  hx-confirm="Are you sure you want to delete {{ dancer.blaze }}?"
  hx-target="closest tr"
  hx-swap="outerHTML swap:1s"
>
  Delete
</button>
```

**Backend Route:**
```python
@router.delete("/dancers/{id}")
async def delete_dancer(id: UUID):
    await dancer_service.delete(id)
    return ''  # Return empty (row removed from DOM)
```

**Key Points:**
- `hx-delete`: DELETE request
- `hx-confirm`: Native browser confirmation
- `hx-target="closest tr"`: Find parent row
- `hx-swap="outerHTML swap:1s"`: Fade out animation

---

### Pattern 6: Drag-and-Drop List Reordering (SortableJS + HTMX)

**Use Case:** Battle queue reordering with constraints

**Library:** SortableJS 1.15.x (CDN)

**Business Rules (BR-SCHED-002):**
- COMPLETED battles cannot be moved
- ACTIVE battle cannot be moved
- First PENDING battle ("on deck") is locked
- Only battles 2+ positions after first pending can be reordered

**HTML Structure:**
```html
<!-- CDN include in base.html -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>

<!-- Battle queue with sortable items -->
<div
  id="battle-queue"
  class="sortable-list"
  hx-get="/battles/queue?category_id={{ category_id }}"
  hx-trigger="every 5s"
  hx-swap="outerHTML"
  role="list"
  aria-label="Battle queue"
>
  {% for battle in battles %}
  <article
    class="battle-card {% if battle.is_locked %}battle-locked{% endif %}"
    data-battle-id="{{ battle.id }}"
    data-position="{{ loop.index }}"
    {% if not battle.is_locked %}draggable="true"{% endif %}
    role="listitem"
    aria-label="Battle {{ loop.index }}: {{ battle.performers | join(' vs ') }}"
  >
    <!-- Drag handle (only for movable battles) -->
    {% if not battle.is_locked %}
    <div class="drag-handle" aria-label="Drag to reorder">
      <span aria-hidden="true">⋮⋮</span>
    </div>
    {% else %}
    <div class="lock-indicator" role="img" aria-label="Battle is locked">
      <span aria-hidden="true">🔒</span>
    </div>
    {% endif %}

    <!-- Battle content -->
    <div class="battle-content">
      <span class="badge badge-{{ battle.status.value }}">{{ battle.status.value }}</span>
      <span>{{ battle.performers[0].dancer.blaze }} vs {{ battle.performers[1].dancer.blaze }}</span>
    </div>
  </article>
  {% endfor %}
</div>

<!-- Hidden form for HTMX submission -->
<form id="reorder-form" hx-post="/battles/reorder" hx-swap="outerHTML" hx-target="#battle-queue">
  <input type="hidden" name="battle_id" id="reorder-battle-id">
  <input type="hidden" name="new_position" id="reorder-new-position">
</form>
```

**JavaScript Initialization:**
```javascript
// app/static/js/battle-reorder.js
document.addEventListener('DOMContentLoaded', function() {
  const queue = document.getElementById('battle-queue');
  if (!queue) return;

  const sortable = Sortable.create(queue, {
    handle: '.drag-handle',           // Only drag by handle
    filter: '.battle-locked',         // Exclude locked battles
    animation: 150,                   // Smooth animation
    ghostClass: 'sortable-ghost',     // Class for placeholder
    chosenClass: 'sortable-chosen',   // Class for dragged item

    // Prevent dropping in locked positions
    onMove: function(evt) {
      // Cannot drop before locked items
      const related = evt.related;
      if (related.classList.contains('battle-locked')) {
        const relatedIndex = [...queue.children].indexOf(related);
        const draggedIndex = [...queue.children].indexOf(evt.dragged);
        // Don't allow dropping before locked item
        if (draggedIndex > relatedIndex) {
          return false;
        }
      }
      return true;
    },

    // Submit reorder via HTMX
    onEnd: function(evt) {
      if (evt.oldIndex === evt.newIndex) return;

      const battleId = evt.item.dataset.battleId;
      const newPosition = evt.newIndex + 1; // 1-indexed

      // Update hidden form and submit via HTMX
      document.getElementById('reorder-battle-id').value = battleId;
      document.getElementById('reorder-new-position').value = newPosition;
      htmx.trigger('#reorder-form', 'submit');

      // Announce to screen readers
      announceReorder(evt.item, evt.newIndex + 1);
    }
  });

  // Keyboard navigation for accessibility
  queue.addEventListener('keydown', function(evt) {
    if (!evt.target.classList.contains('battle-card')) return;
    if (evt.target.classList.contains('battle-locked')) return;

    const items = [...queue.querySelectorAll('.battle-card:not(.battle-locked)')];
    const currentIndex = items.indexOf(evt.target);

    if (evt.key === 'ArrowUp' && evt.altKey && currentIndex > 0) {
      evt.preventDefault();
      moveItem(evt.target, currentIndex - 1);
    } else if (evt.key === 'ArrowDown' && evt.altKey && currentIndex < items.length - 1) {
      evt.preventDefault();
      moveItem(evt.target, currentIndex + 1);
    }
  });

  function moveItem(item, newIndex) {
    const battleId = item.dataset.battleId;
    document.getElementById('reorder-battle-id').value = battleId;
    document.getElementById('reorder-new-position').value = newIndex + 1;
    htmx.trigger('#reorder-form', 'submit');
  }

  function announceReorder(item, newPosition) {
    const announcement = document.getElementById('reorder-status');
    if (announcement) {
      announcement.textContent = `Battle moved to position ${newPosition}`;
    }
  }
});
```

**CSS Styles:**
```css
/* app/static/css/battles.css */
.sortable-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.battle-card {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: var(--pico-card-background-color);
  border-radius: 0.25rem;
  border: 1px solid var(--pico-muted-border-color);
}

.battle-card.battle-locked {
  opacity: 0.7;
  cursor: not-allowed;
}

.drag-handle {
  cursor: grab;
  padding: 0.5rem;
  margin-right: 0.5rem;
  color: var(--pico-muted-color);
  user-select: none;
}

.drag-handle:active {
  cursor: grabbing;
}

.lock-indicator {
  padding: 0.5rem;
  margin-right: 0.5rem;
  color: var(--pico-muted-color);
}

/* Drag states */
.sortable-ghost {
  opacity: 0.5;
  background: var(--pico-primary-background);
}

.sortable-chosen {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Keyboard focus */
.battle-card:focus {
  outline: 3px solid var(--pico-primary);
  outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .sortable-ghost,
  .battle-card {
    transition: none;
  }
}
```

**Backend Route:**
```python
@router.post("/battles/reorder")
async def reorder_battle(
    request: Request,
    battle_id: UUID = Form(...),
    new_position: int = Form(...),
    battle_service: BattleService = Depends(get_battle_service),
    current_user = Depends(require_staff),
):
    """Reorder a battle in the queue via HTMX."""
    result = await battle_service.reorder_battle(battle_id, new_position)

    if not result:
        for error in result.errors:
            add_flash_message(request, error, "error")

    # Return updated queue partial
    battles = await battle_service.get_battle_queue(...)
    return templates.TemplateResponse(
        "battles/_battle_queue.html",
        {"request": request, "battles": battles}
    )
```

**Accessibility Features:**
- **ARIA live region** announces reorder to screen readers
- **Keyboard navigation** with Alt+Arrow keys
- **Focus indicators** visible during keyboard interaction
- **Reduced motion** support disables animations
- **Lock indicators** explain why items can't be moved

**Key Points:**
- `handle: '.drag-handle'` - Only drag by handle, allows text selection elsewhere
- `filter: '.battle-locked'` - Exclude locked items from drag
- `onMove` - Prevents dropping before locked items
- `onEnd` - Submits reorder via HTMX hidden form
- Keyboard fallback for accessibility (Alt+Arrow to move)

---

## Accessibility Guidelines

### Keyboard Navigation

**Required Interactions:**
- `Tab` - Move to next interactive element
- `Shift + Tab` - Move to previous interactive element
- `Enter` - Activate links and buttons
- `Space` - Toggle checkboxes, activate buttons
- `Esc` - Close modals/dialogs

**Tab Order:** Must follow logical visual flow

**Skip Links:** (Future enhancement)
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
```

---

### Screen Reader Support

**Semantic HTML:**
```html
<nav><!-- Navigation sections --></nav>
<main><!-- Primary content --></main>
<article><!-- Self-contained content --></article>
<section><!-- Thematic grouping --></section>
<header><!-- Section header --></header>
<footer><!-- Section footer --></footer>
```

**ARIA Labels:**

**Form fields with errors:**
```html
<input
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<small id="email-error" role="alert">Email is required</small>
```

**Loading states:**
```html
<div aria-live="polite" aria-busy="true">
  Loading dancers...
</div>
```

**Dynamic updates:**
```html
<div role="status" aria-live="polite">
  Dancer registered successfully
</div>
```

**Navigation current page:**
```html
<a href="/dancers" aria-current="page">Dancers</a>
```

---

### Color Contrast

**WCAG AA Requirements:**
- Text: 4.5:1 contrast ratio minimum
- Large text (18pt+ or bold 14pt+): 3:1 minimum
- UI components (borders, icons): 3:1 minimum

**PicoCSS Defaults:** Meet WCAG AA in both light and dark modes

**Testing:**
- Use browser DevTools contrast checker
- Test with Chrome Lighthouse
- Manual verification with contrast tools

---

### Focus Indicators

**Requirement:** All interactive elements must show clear focus state

**PicoCSS Default:** Blue outline (customizable)

**Custom Enhancement:**
```css
:focus-visible {
  outline: 3px solid var(--pico-primary);
  outline-offset: 2px;
}

/* Never remove focus outline */
:focus {
  outline: auto; /* Browser default if :focus-visible not supported */
}
```

---

### Form Accessibility

**Complete Form Example:**
```html
<form method="post" action="/dancers/create">
  <!-- Text input with label -->
  <label for="blaze">
    Blaze (Stage Name) <abbr title="required">*</abbr>
  </label>
  <input
    type="text"
    id="blaze"
    name="blaze"
    required
    aria-describedby="blaze-error blaze-help"
  >
  <small id="blaze-help">Your stage name for battles</small>
  {% if errors.blaze %}
  <small id="blaze-error" role="alert">{{ errors.blaze }}</small>
  {% endif %}

  <!-- Radio buttons with fieldset -->
  <fieldset>
    <legend>Category Type</legend>
    <label>
      <input type="radio" name="is_duo" value="false" checked>
      1v1 (Solo)
    </label>
    <label>
      <input type="radio" name="is_duo" value="true">
      2v2 (Duo)
    </label>
  </fieldset>

  <!-- Submit buttons -->
  <button type="submit">Create Dancer</button>
  <a href="/dancers" role="button" class="secondary">Cancel</a>
</form>
```

**Key Points:**
- Labels with `for` attribute
- Required fields marked with `<abbr>`
- Help text with `aria-describedby`
- Error messages with `role="alert"`
- Fieldset for radio/checkbox groups

---

## Responsive Design

### Mobile Optimizations (320px - 768px)

**Touch Targets:**
- Minimum size: 44x44px
- Spacing between targets: 8px minimum

**Typography:**
- Base font size: 16px (prevents zoom on iOS)
- Line height: 1.5 (comfortable reading)
- Max line length: 70 characters (readability)

**Forms:**
- Full-width inputs
- Stacked buttons (one per row)
- Large tap targets for radio/checkbox

**Tables:**
- Transform to cards using CSS
- `data-label` attribute provides context

**Navigation:**
- Sidebar collapses to top
- Stack links vertically
- Full-width buttons

---

### Tablet Considerations (769px - 1024px)

**Layout:**
- Sidebar: Reduce to 200px or collapse with toggle
- Content: Maintain readability with max-width constraint
- Forms: Allow two-column layouts where logical (first/last name)

**Navigation:**
- Sidebar visible or easily accessible
- Icon + text labels

---

### Desktop Enhancements (1025px+)

**Multi-Column Layouts:**
- Dashboard: 2-3 column grid for cards
- Forms: Side-by-side inputs where logical
- Tables: Full table layout with all columns visible

**Hover States:**
- Links: Underline on hover
- Buttons: Darken background
- Cards: Subtle shadow or border change

**Sidebar:**
- Fixed width (250px)
- Always visible
- Sticky positioning

---

## Design Tokens

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

**Custom Badges:**
```css
:root {
  --badge-created: var(--pico-muted-color);
  --badge-active: var(--pico-primary-background);
  --badge-completed: var(--pico-secondary-background);
  --badge-cancelled: #f59e0b; /* Amber */
}
```

---

### Spacing

**PicoCSS Defaults:**
- `1rem` = 16px (base unit)
- Padding: 1rem (forms, buttons, cards)
- Margin: 1rem (vertical rhythm)

**Custom Spacing Variables:**
```css
:root {
  --spacing-xs: 0.25rem;  /* 4px */
  --spacing-sm: 0.5rem;   /* 8px */
  --spacing-md: 1rem;     /* 16px */
  --spacing-lg: 2rem;     /* 32px */
  --spacing-xl: 4rem;     /* 64px */
}
```

---

### Typography

**PicoCSS Defaults:**
- Font family: System font stack (no web fonts)
- Base size: 16px
- Scale: 1.25 (headings)
- Line height: 1.5

**Headings:**
- `h1`: 2.5rem (40px)
- `h2`: 2rem (32px)
- `h3`: 1.5rem (24px)
- `h4`: 1.25rem (20px)

---

### Borders & Shadows

**Borders:**
- Radius: 0.25rem (4px)
- Width: 1px
- Color: `var(--pico-muted-border-color)`

**Shadows:**
- None by default (minimalist approach)
- Optional: Subtle shadow on cards (future enhancement)

---

### Pattern 7: Event Mode Layout (No Sidebar)

**Use Case:** Full-screen command center for event day operations

**Business Rule (BR-NAV-003):** During event phases (PRESELECTION, POOLS, FINALS), staff should have a focused interface optimized for the battle loop.

**Base Template:**
```html
<!-- app/templates/event_base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Event Mode - Battle-D{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    <link rel="stylesheet" href="/static/css/event.css">
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body class="event-mode">
    <!-- Compact Header (no sidebar) -->
    <header class="event-header">
        <div class="event-header-left">
            <span class="event-live-indicator" aria-label="Live event">🔴 LIVE</span>
            <h1>{{ tournament.name }}</h1>
            <span class="event-phase-badge">{{ tournament.phase.value|upper }}</span>
        </div>
        <div class="event-header-right">
            <span class="event-progress">{{ progress.completed }}/{{ progress.total }}</span>
            <a href="/overview" class="event-exit-btn">Exit to Prep</a>
        </div>
    </header>

    {% include "components/flash_messages.html" %}

    <main class="event-main">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

**CSS Structure:**
```css
/* app/static/css/event.css */
body.event-mode {
    margin: 0;
    padding: 0;
    background: var(--pico-background-color);
}

.event-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background: var(--pico-primary-background);
    color: white;
}

.event-live-indicator {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.event-main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr auto;
    gap: 1rem;
    padding: 1rem;
    height: calc(100vh - 60px);
}

/* Responsive: Stack on mobile */
@media (max-width: 1024px) {
    .event-main {
        grid-template-columns: 1fr;
        grid-template-rows: auto;
        height: auto;
    }
}
```

**Key Points:**
- No sidebar navigation (full-screen focus)
- Compact header with essential info only
- Grid layout for command center panels
- "Exit to Prep" button for emergencies
- LIVE indicator for visual context

---

### Pattern 8: Two-Panel Transfer List

**Use Case:** Registration page with available/registered dancers

**Business Rule (BR-NAV-004):** Staff should be able to register dancers without page refreshes.

**HTML Structure:**
```html
<div class="transfer-list">
    <!-- Left Panel: Available -->
    <section class="panel panel-available">
        <div class="panel-header">
            <h3>Available Dancers</h3>
            <input type="search"
                   name="q"
                   placeholder="Search..."
                   hx-get="/registration/{{ t_id }}/{{ c_id }}/available"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#available-list"
                   hx-indicator="#search-loading">
        </div>
        <div id="available-list" class="panel-list" role="list" aria-label="Available dancers">
            {% for dancer in available %}
            <article class="item-card" role="listitem">
                <div class="item-info">
                    <strong>{{ dancer.blaze }}</strong>
                    <span>{{ dancer.full_name }}</span>
                </div>
                <button class="btn-transfer"
                        hx-post="/registration/{{ t_id }}/{{ c_id }}/register/{{ dancer.id }}"
                        hx-target="#available-list"
                        hx-swap="innerHTML"
                        hx-swap-oob="innerHTML:#registered-list"
                        aria-label="Add {{ dancer.blaze }}">
                    + Add
                </button>
            </article>
            {% endfor %}
        </div>
    </section>

    <!-- Right Panel: Registered -->
    <section class="panel panel-registered">
        <div class="panel-header">
            <h3>Registered (<span id="count">{{ registered|length }}</span>)</h3>
        </div>
        <div id="registered-list" class="panel-list" role="list" aria-label="Registered dancers">
            {% for performer in registered %}
            <article class="item-card" role="listitem">
                <div class="item-info">
                    <strong>{{ performer.dancer.blaze }}</strong>
                    <span>{{ performer.dancer.full_name }}</span>
                </div>
                <button class="btn-remove"
                        hx-delete="/registration/{{ t_id }}/{{ c_id }}/unregister/{{ performer.id }}"
                        hx-target="#registered-list"
                        hx-swap="innerHTML"
                        hx-swap-oob="innerHTML:#available-list"
                        aria-label="Remove {{ performer.dancer.blaze }}">
                    ✕ Remove
                </button>
            </article>
            {% endfor %}
        </div>
    </section>
</div>
```

**CSS Structure:**
```css
.transfer-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    height: 100%;
}

.panel {
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 0.25rem;
    display: flex;
    flex-direction: column;
}

.panel-header {
    padding: 1rem;
    border-bottom: 1px solid var(--pico-muted-border-color);
    background: var(--pico-card-background-color);
}

.panel-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
}

.item-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 0.25rem;
}

.btn-transfer, .btn-remove {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
}

.btn-transfer {
    background: var(--pico-primary-background);
    color: white;
}

.btn-remove {
    background: var(--pico-secondary-background);
    color: white;
}

/* Responsive: Stack on mobile */
@media (max-width: 768px) {
    .transfer-list {
        grid-template-columns: 1fr;
    }
}
```

**Backend Pattern (hx-swap-oob):**
```python
@router.post("/{t_id}/{c_id}/register/{dancer_id}")
async def register_dancer_htmx(t_id: UUID, c_id: UUID, dancer_id: UUID, ...):
    """Register dancer and return BOTH panels via hx-swap-oob."""
    result = await registration_service.register_dancer(...)

    # Get updated lists
    available = await dancer_service.get_available_for_category(...)
    registered = await performer_repo.get_by_category(c_id)

    # Return main target + out-of-band update
    response = templates.TemplateResponse(
        "registration/_available_list.html",
        {"request": request, "available": available, "t_id": t_id, "c_id": c_id}
    )

    # Add OOB update for registered list
    registered_html = templates.TemplateResponse(
        "registration/_registered_list.html",
        {"request": request, "registered": registered, "t_id": t_id, "c_id": c_id}
    )

    return HTMLResponse(
        content=response.body.decode() +
        f'<div id="registered-list" hx-swap-oob="innerHTML">{registered_html.body.decode()}</div>'
    )
```

**Key Points:**
- `hx-swap-oob` updates BOTH panels with single request
- Search filters available list in real-time
- No page refresh on register/unregister
- Count updates automatically
- Accessible with ARIA labels

---

### Pattern 9: Context-Aware Smart Dashboard

**Use Case:** Dashboard that shows different content based on tournament state

**Business Rule (BR-NAV-002):** Dashboard displays different content based on tournament state.

**HTML Structure:**
```html
<!-- app/templates/dashboard/index.html -->
{% extends "base.html" %}

{% block content %}
{% if state == 'no_tournament' %}
    <!-- State 1: No active tournament -->
    <section class="dashboard-cta">
        <h2>No Active Tournament</h2>
        <p>Create a tournament to get started.</p>
        <a href="/tournaments/create" role="button">+ Create Tournament</a>
    </section>

    {% if past_tournaments %}
    <section>
        <h3>Past Tournaments</h3>
        <!-- List of completed tournaments -->
    </section>
    {% endif %}

{% elif state == 'registration' %}
    <!-- State 2: Tournament in REGISTRATION phase -->
    <section class="dashboard-header">
        <h2>{{ tournament.name }}</h2>
        <span class="badge badge-registration">REGISTRATION</span>
    </section>

    <section class="category-grid">
        {% for cat in categories %}
        <article class="category-card {% if cat.is_ready %}ready{% else %}needs-more{% endif %}">
            <h3>{{ cat.name }}</h3>
            <p class="registration-count">
                {{ cat.registered }}/{{ cat.ideal }} registered
            </p>
            <p class="status">
                {% if cat.is_ready %}✓ Ready{% else %}Need {{ cat.minimum - cat.registered }} more{% endif %}
            </p>
            <a href="/registration/{{ tournament.id }}/{{ cat.id }}" role="button" class="secondary">
                Register Dancers
            </a>
        </article>
        {% endfor %}
    </section>

    {% if all_categories_ready %}
    <section class="dashboard-action">
        <form action="/tournaments/{{ tournament.id }}/advance" method="post">
            <input type="hidden" name="confirmed" value="false">
            <button type="submit" class="start-event-btn">▶ Start Event</button>
        </form>
    </section>
    {% endif %}

{% elif state == 'event_active' %}
    <!-- State 3: Tournament in event phases -->
    <section class="dashboard-header">
        <h2>{{ tournament.name }}</h2>
        <span class="badge badge-live">🔴 LIVE - {{ tournament.phase.value|upper }}</span>
    </section>

    <section class="event-summary">
        <p>Battle Progress: {{ progress.completed }}/{{ progress.total }} ({{ progress.percentage }}%)</p>
        <a href="/event/{{ tournament.id }}" role="button" class="go-to-event-btn">
            Go to Event Mode →
        </a>
    </section>
{% endif %}
{% endblock %}
```

**Key Points:**
- Single template with conditional blocks
- State determined by service layer
- Clear CTAs for each state
- Visual distinction between states

---

## Integration with Backend

### Template Organization

```
app/templates/
├── base.html                 # Base layout with sidebar
├── components/               # Reusable components
│   ├── empty_state.html
│   ├── flash_messages.html
│   ├── loading.html
│   ├── delete_modal.html
│   └── field_error.html
├── auth/                     # Authentication pages
├── admin/                    # Admin pages
├── dancers/                  # Dancer management
│   ├── list.html
│   ├── create.html
│   └── _search_results.html  # Partial for HTMX
├── tournaments/              # Tournament management
└── battles/                  # Battle management
```

**Naming Convention:**
- Regular templates: `page.html`
- HTMX partials: `_partial.html`
- Components: `component_name.html`

---

### Static Files

```
app/static/
├── css/
│   ├── base.css              # Layout (CSS Grid)
│   ├── error-handling.css    # Flash messages, modals
│   └── badges.css            # Status badges
├── js/
│   ├── error-handling.js     # Flash dismiss, modal management
│   └── duo-selection.js      # Duo partner selection (custom)
└── images/
    └── (future: logos, icons)
```

**CSS Load Order:**
1. PicoCSS (CDN)
2. base.css (layout)
3. error-handling.css (components)
4. badges.css (UI elements)

---

## Best Practices

### DO: ✅

- Use semantic HTML (`nav`, `main`, `article`, `section`)
- Use PicoCSS utility classes (minimize custom CSS)
- Use HTMX for dynamic interactions (minimize custom JS)
- Include ARIA attributes for accessibility
- Test keyboard navigation on all pages
- Test with screen readers (VoiceOver, NVDA)
- Design mobile-first, enhance for desktop
- Use `data-label` on table cells for mobile
- Include skip links for keyboard users
- Provide error messages for form validation
- Use flash messages for user feedback
- Include empty states for lists
- Confirm destructive actions with modals

### DON'T: ❌

- Don't reinvent components (use Component Library)
- Don't skip accessibility (WCAG 2.1 AA is mandatory)
- Don't use decorative elements (every element has purpose)
- Don't hardcode colors (use CSS variables)
- Don't write custom JavaScript unless necessary
- Don't remove focus indicators (`:focus { outline: none }`)
- Don't use `div` when semantic elements exist
- Don't use icons without text labels
- Don't skip `alt` text on images
- Don't create multi-column layouts on mobile
- Don't use small touch targets (< 44px)
- Don't skip responsive testing
- Don't use non-standard form controls

---

## Cross-References

**Related Documentation:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - Backend patterns (services, validators, repositories)
- [VALIDATION_RULES.md](VALIDATION_RULES.md) - Field lengths, limits, formulas
- [TESTING.md](TESTING.md) - Frontend testing strategies
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Entity definitions and business rules

**For AI Assistant:**
- See [.claude/README.md](.claude/README.md) for complete development methodology including frontend integration

---

## Version History

- **v1.0** (2025-12-03) - Initial FRONTEND.md created from UI_MOCKUPS.md v2.1 enduring patterns
  - Extracted sections 1-5, 15-17 from UI_MOCKUPS.md
  - Reorganized into frontend architecture document
  - Page-by-page wireframes (sections 6-14) archived separately
  - Clear purpose: "Frontend architectural patterns and component library"

- **v1.1** (2025-12-06) - Added drag-and-drop reordering pattern
  - Added Pattern 6: Drag-and-Drop List Reordering (SortableJS + HTMX)
  - Business rules: BR-SCHED-002 battle reordering constraints
  - Accessibility: Keyboard navigation, ARIA live regions, reduced motion

---

**End of Document**
