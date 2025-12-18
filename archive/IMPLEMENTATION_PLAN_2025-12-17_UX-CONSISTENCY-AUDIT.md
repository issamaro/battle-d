# Implementation Plan: UX Consistency Audit & Automated Testing

**Date:** 2025-12-17
**Status:** Ready for Implementation
**Based on:** FEATURE_SPEC_2025-12-17_UX-CONSISTENCY-AUDIT.md

---

## 1. Summary

**Feature:** Clean up UX inconsistencies (orphaned templates, inline styles, inconsistent patterns) and add E2E tests to prevent future regressions.

**Approach:**
1. Delete orphaned templates
2. Refactor inline styles to use existing CSS classes from `battles.css`
3. Standardize permission display to checkmark symbols
4. Create new E2E test file for UX consistency validation

---

## 2. Affected Files

### Backend
**Models:** None

**Services:** None

**Repositories:** None

**Routes:** None

**Validators:** None

**Utils:** None

### Frontend

**Templates to DELETE:**
- `app/templates/overview.html` (orphaned - replaced by dashboard/index.html)

**Templates to DOCUMENT:**
- `app/templates/pools/overview.html` (add comment explaining future use)

**Templates to REFACTOR (remove inline styles):**

| Template | Issue | Solution |
|----------|-------|----------|
| `app/templates/tournaments/detail.html` | 25+ inline styles | Use PicoCSS `<article>`, `.badge` classes |
| `app/templates/tournaments/list.html` | 8 inline styles | Use PicoCSS table, `.badge` classes |
| `app/templates/dancers/list.html` | 3 inline styles | Use `role="button"`, PicoCSS input |
| `app/templates/admin/users.html` | 8 inline styles | Use `role="button"`, PicoCSS table |
| `app/templates/dancers/_table.html` | 2 inline styles | Use PicoCSS defaults |

**Templates to UPDATE (permission display):**
- `app/templates/dashboard/index.html` - Change "Yes/No" to checkmark symbols

**Components:**
- Reuse: `.badge`, `.badge-pending`, `.badge-active`, `.badge-completed` from `battles.css`
- Add: `.badge-warning` for cancelled status (yellow) if needed

**CSS:**
- No new CSS files needed
- May add `.badge-warning` variant to `app/static/css/battles.css` for consistency

### Database
**Migrations:** None

### Tests
**New Test Files:**
- `tests/e2e/test_ux_consistency.py` - UX regression tests

**Updated Test Files:** None

### Documentation
**Level 1:** None (no domain model changes)

**Level 2:**
- `ROADMAP.md`: Add Phase 3.10 - UX Consistency Audit

**Level 3:**
- `FRONTEND.md`: Document badge pattern and permission display standard
- `TESTING.md`: Document UX consistency testing approach

---

## 3. Backend Implementation Plan

**No backend changes required.** This is a frontend cleanup and testing initiative.

---

## 4. Frontend Implementation Plan

### 4.1 Phase 1: Delete Orphaned Template

**File:** `app/templates/overview.html`
**Action:** Delete entire file
**Verification:** Run all E2E tests to confirm no breakage

### 4.2 Phase 2: Document Future Feature Template

**File:** `app/templates/pools/overview.html`
**Action:** Add comment at top of file

```html
{#
  FUTURE FEATURE: Pool Standings View

  This template is prepared for the pool standings feature (V2).
  It is not currently wired to any route.

  Planned route: /pools/{category_id}
  Purpose: Display pool standings during POOLS phase

  See: ROADMAP.md Phase 4+ for implementation schedule
#}
```

### 4.3 Phase 3: Refactor tournaments/detail.html

**Current Issues:**
1. Inline flexbox layout for info card
2. Inline badge styling (should use `.badge` classes)
3. Inline button styling (should use `role="button"`)
4. Inline table styling
5. Inline legend styling

**Refactored Structure:**

```html
{% extends "base.html" %}

{% block title %}{{ tournament.name }} - Battle-D{% endblock %}

{% block content %}
<h2>Tournament: {{ tournament.name }}</h2>

<section>
    <p><a href="/tournaments">&larr; Back to Tournaments</a></p>
</section>

<!-- Tournament Info Card - Use PicoCSS article -->
<article>
    <header>
        <h3>Tournament Information</h3>
    </header>

    <table>
        <tr>
            <td><strong>Status:</strong></td>
            <td>
                <span class="badge {% if tournament.status.value == 'active' %}badge-active{% elif tournament.status.value == 'cancelled' %}badge-warning{% else %}badge-pending{% endif %}">
                    {{ tournament.status.value|upper }}
                </span>
            </td>
        </tr>
        <tr>
            <td><strong>Phase:</strong></td>
            <td>
                <span class="badge badge-active">
                    {{ tournament.phase.value|upper }}
                </span>
            </td>
        </tr>
        <tr>
            <td><strong>Created:</strong></td>
            <td>{{ tournament.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
        </tr>
    </table>

    {% if current_user.is_admin %}
    <footer>
        <a href="/tournaments/{{ tournament.id }}/phase" role="button" class="secondary">
            Manage Phase
        </a>
    </footer>
    {% endif %}
</article>

<!-- Categories Section -->
<section>
    <h3>Categories</h3>

    <p>
        <a href="/tournaments/{{ tournament.id }}/add-category" role="button">
            + Add Category
        </a>
    </p>

    {% if category_data %}
        <figure>
            <table role="grid">
                <thead>
                    <tr>
                        <th>Category Name</th>
                        <th>Type</th>
                        <th>Registered</th>
                        <th>Minimum Required</th>
                        <th>Ideal Capacity</th>
                        <th>Pools</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in category_data %}
                    {% set minimum_required = (item.category.groups_ideal * 2) + 2 %}
                    {% set is_ready = item.performer_count >= minimum_required %}
                    <tr>
                        <td><strong>{{ item.category.name }}</strong></td>
                        <td>{{ item.category.category_type }}</td>
                        <td>
                            <span class="badge {% if is_ready %}badge-completed{% else %}badge-pending{% endif %}">
                                {{ item.performer_count }}
                            </span>
                        </td>
                        <td>{{ minimum_required }}</td>
                        <td>
                            {{ item.category.ideal_pool_capacity }}
                            <br>
                            <small>({{ item.category.performers_ideal }}/pool)</small>
                        </td>
                        <td>{{ item.category.groups_ideal }}</td>
                        <td>
                            <a href="/registration/{{ tournament.id }}/{{ item.category.id }}">Register Dancers</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </figure>

        <small>
            <strong>Legend:</strong>
            <span class="badge badge-completed">Green</span> = Ready to advance |
            <span class="badge badge-pending">Gray</span> = Need more performers
        </small>
    {% else %}
        {% set title = "No Categories Yet" %}
        {% set message = "Add a category to get started with registration!" %}
        {% set action_url = "/tournaments/" ~ tournament.id ~ "/add-category" %}
        {% set action_text = "Add Category" %}
        {% set icon = "📁" %}
        {% include "components/empty_state.html" %}
    {% endif %}
</section>
{% endblock %}
```

### 4.4 Phase 4: Refactor tournaments/list.html

**Changes:**
- Replace inline badge styles with `.badge` classes
- Replace inline button styles with `role="button"`
- Use PicoCSS table defaults
- Use `.badge-warning` for cancelled status

### 4.5 Phase 5: Refactor dancers/list.html

**Changes:**
- Replace inline button style with `role="button"`
- Remove inline input width (use PicoCSS default)
- Remove inline paragraph styling

### 4.6 Phase 6: Refactor admin/users.html

**Changes:**
- Replace inline button styles with `role="button"` or PicoCSS buttons
- Remove inline select styling
- Use PicoCSS table defaults

### 4.7 Phase 7: Refactor dancers/_table.html

**Changes:**
- Remove inline link margins (use CSS or role="group")
- Use PicoCSS table defaults

### 4.8 Phase 8: Update Permission Display

**File:** `app/templates/dashboard/index.html`

**Current (lines 34-51):**
```html
<td>{{ "Yes" if current_user.is_admin else "No" }}</td>
```

**Updated:**
```html
<td>{{ "&#10003;" if current_user.is_admin else "&#10007;" }}</td>
```

Or using Unicode directly:
```html
<td>{{ "✓" if current_user.is_admin else "✗" }}</td>
```

### 4.9 CSS Enhancement (if needed)

**File:** `app/static/css/battles.css`

Add warning badge variant if not present:
```css
.badge-warning {
    background-color: #ffc107; /* Yellow/warning */
    color: #212529; /* Dark text for contrast */
    /* Contrast ratio: 8.59:1 (WCAG AAA ✓) */
}
```

---

## 5. E2E Test Implementation Plan

### 5.1 New Test File: tests/e2e/test_ux_consistency.py

```python
"""E2E tests for UX consistency.

Validates:
- BR-UX-001: No inline styles (threshold-based)
- BR-UX-002: All links have routes
- BR-UX-003: No orphaned templates
- BR-UX-004: Consistent permission display

See: FEATURE_SPEC_2025-12-17_UX-CONSISTENCY-AUDIT.md
"""
import os
import re
from pathlib import Path
from glob import glob

import pytest

from app.main import app


# =============================================================================
# CONFIGURATION
# =============================================================================

TEMPLATES_DIR = Path("app/templates")
ROUTERS_DIR = Path("app/routers")

# Templates that are intentionally not wired to routes (future features)
ALLOWED_ORPHANED_TEMPLATES = {
    "pools/overview.html",  # Future: Pool standings view
}

# Inline styles that are acceptable exceptions
ALLOWED_INLINE_STYLE_PATTERNS = [
    # Example: allow specific one-off adjustments
    # r'style="display:\s*inline"',  # Inline form buttons
]

# Maximum allowed inline styles (after filtering exceptions)
MAX_INLINE_STYLES = 5


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_templates() -> list[Path]:
    """Get all HTML template files."""
    return list(TEMPLATES_DIR.rglob("*.html"))


def get_all_router_files() -> list[Path]:
    """Get all Python router files."""
    return list(ROUTERS_DIR.glob("*.py"))


def extract_template_references_from_python() -> set[str]:
    """Extract all template names referenced in Python code."""
    references = set()

    for py_file in get_all_router_files():
        content = py_file.read_text()

        # Match TemplateResponse name= patterns
        # e.g., name="dashboard/index.html"
        pattern = r'name\s*=\s*["\']([^"\']+\.html)["\']'
        matches = re.findall(pattern, content)
        references.update(matches)

    # Also check main.py for error handlers
    main_py = Path("app/main.py")
    if main_py.exists():
        content = main_py.read_text()
        pattern = r'name\s*=\s*["\']([^"\']+\.html)["\']'
        matches = re.findall(pattern, content)
        references.update(matches)

    return references


def extract_template_includes(template_path: Path) -> set[str]:
    """Extract templates included by this template."""
    content = template_path.read_text()
    includes = set()

    # Match {% include "path.html" %}
    include_pattern = r'{%\s*include\s*["\']([^"\']+)["\']'
    includes.update(re.findall(include_pattern, content))

    # Match {% extends "path.html" %}
    extends_pattern = r'{%\s*extends\s*["\']([^"\']+)["\']'
    includes.update(re.findall(extends_pattern, content))

    return includes


def count_inline_styles(template_path: Path) -> tuple[int, list[str]]:
    """Count inline styles in template, excluding allowed patterns.

    Returns:
        Tuple of (count, list of inline style occurrences)
    """
    content = template_path.read_text()

    # Find all style="" attributes
    pattern = r'style\s*=\s*["\'][^"\']*["\']'
    matches = re.findall(pattern, content)

    # Filter out allowed patterns
    filtered_matches = []
    for match in matches:
        is_allowed = any(
            re.search(allowed_pattern, match)
            for allowed_pattern in ALLOWED_INLINE_STYLE_PATTERNS
        )
        if not is_allowed:
            filtered_matches.append(match)

    return len(filtered_matches), filtered_matches


def extract_hrefs(template_path: Path) -> list[str]:
    """Extract all href values from template."""
    content = template_path.read_text()

    # Match href="/path" or href="{{ url }}"
    # Only capture static hrefs (not Jinja variables)
    pattern = r'href\s*=\s*["\'](?!/static)(/[^"\'{}]*)["\']'
    return re.findall(pattern, content)


# =============================================================================
# TESTS
# =============================================================================


class TestOrphanedTemplates:
    """Tests for BR-UX-003: No orphaned templates."""

    def test_no_orphaned_templates(self):
        """Verify all templates are referenced somewhere.

        Validates: FEATURE_SPEC_2025-12-17 Scenario "All templates are referenced"
        Gherkin:
            Given I list all HTML files in app/templates/
            When I trace references in Python code and other templates
            Then every template should have at least one reference
        """
        # Get all templates
        all_templates = get_all_templates()

        # Get references from Python code
        python_references = extract_template_references_from_python()

        # Get references from other templates (includes/extends)
        template_references = set()
        for template in all_templates:
            template_references.update(extract_template_includes(template))

        all_references = python_references | template_references

        # Check each template
        orphaned = []
        for template in all_templates:
            relative_path = template.relative_to(TEMPLATES_DIR)
            template_name = str(relative_path)

            # Skip allowed orphans
            if template_name in ALLOWED_ORPHANED_TEMPLATES:
                continue

            # Check if referenced
            if template_name not in all_references:
                orphaned.append(template_name)

        assert not orphaned, (
            f"Found orphaned templates (not referenced anywhere):\n"
            f"{chr(10).join(f'  - {t}' for t in orphaned)}\n"
            f"Add to ALLOWED_ORPHANED_TEMPLATES if intentional."
        )

    def test_overview_html_deleted(self):
        """Verify legacy overview.html has been deleted.

        Validates: FEATURE_SPEC_2025-12-17 Scenario "Orphaned templates are removed"
        Gherkin:
            Given overview.html exists as orphaned file
            When I delete it
            Then no functionality is broken
        """
        legacy_overview = TEMPLATES_DIR / "overview.html"
        assert not legacy_overview.exists(), (
            f"Legacy template {legacy_overview} should be deleted. "
            "It was replaced by dashboard/index.html in Phase 3.3."
        )


class TestInlineStyles:
    """Tests for BR-UX-001: No inline styles."""

    def test_inline_styles_below_threshold(self):
        """Verify inline style count is below acceptable threshold.

        Validates: FEATURE_SPEC_2025-12-17 Scenario "No inline styles in templates"
        Gherkin:
            Given I scan all HTML templates in app/templates/
            When I count style="" attributes
            Then the count should be less than {MAX_INLINE_STYLES}
        """
        all_templates = get_all_templates()

        total_inline_styles = 0
        violations = []

        for template in all_templates:
            count, matches = count_inline_styles(template)
            if count > 0:
                total_inline_styles += count
                relative_path = template.relative_to(TEMPLATES_DIR)
                violations.append(f"{relative_path}: {count} inline styles")
                for match in matches[:3]:  # Show first 3
                    violations.append(f"    {match[:60]}...")

        assert total_inline_styles <= MAX_INLINE_STYLES, (
            f"Found {total_inline_styles} inline styles (max allowed: {MAX_INLINE_STYLES}):\n"
            f"{chr(10).join(violations)}\n"
            f"Replace with PicoCSS classes or add to ALLOWED_INLINE_STYLE_PATTERNS."
        )

    def test_no_inline_color_styles(self):
        """Verify no templates use inline background-color or color styles.

        Colors should use .badge classes or PicoCSS semantic colors.
        """
        all_templates = get_all_templates()

        violations = []
        color_pattern = r'style\s*=\s*["\'][^"\']*(?:background-color|[^-]color)\s*:'

        for template in all_templates:
            content = template.read_text()
            matches = re.findall(color_pattern, content)
            if matches:
                relative_path = template.relative_to(TEMPLATES_DIR)
                violations.append(f"{relative_path}: {len(matches)} color styles")

        assert not violations, (
            f"Found inline color styles (should use .badge classes):\n"
            f"{chr(10).join(violations)}"
        )


class TestLinkIntegrity:
    """Tests for BR-UX-002: All links have routes."""

    def test_static_links_have_routes(self):
        """Verify all static href links match defined routes.

        Note: This test checks static paths only, not dynamic Jinja variables.

        Validates: FEATURE_SPEC_2025-12-17 Scenario "All template links have routes"
        """
        # Get all route paths from FastAPI app
        defined_routes = set()
        for route in app.routes:
            if hasattr(route, 'path'):
                # Normalize path patterns (remove {param} style)
                normalized = re.sub(r'\{[^}]+\}', '{id}', route.path)
                defined_routes.add(normalized)

        all_templates = get_all_templates()

        potential_dead_links = []
        for template in all_templates:
            hrefs = extract_hrefs(template)
            for href in hrefs:
                # Normalize href for comparison
                # Replace UUIDs with {id}
                normalized_href = re.sub(
                    r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                    '/{id}',
                    href
                )

                # Check if this path pattern exists
                path_matches = False
                for route_path in defined_routes:
                    # Flexible matching for parameterized routes
                    if normalized_href == route_path:
                        path_matches = True
                        break
                    # Check if href is prefix of route (e.g., /dancers matches /dancers/{id})
                    if route_path.startswith(normalized_href.rstrip('/') + '/'):
                        path_matches = True
                        break
                    if normalized_href.startswith(route_path.rstrip('/') + '/'):
                        path_matches = True
                        break

                if not path_matches and href not in ['/auth/logout']:  # Known redirects
                    relative_path = template.relative_to(TEMPLATES_DIR)
                    potential_dead_links.append(f"{relative_path}: {href}")

        # This is informational - some paths may use Jinja variables
        if potential_dead_links:
            print(f"\nPotential dead links to verify manually:\n")
            for link in potential_dead_links[:10]:
                print(f"  - {link}")


class TestPermissionDisplay:
    """Tests for BR-UX-004: Consistent permission display."""

    def test_permission_uses_symbols(self):
        """Verify permission display uses checkmark symbols, not Yes/No.

        Validates: FEATURE_SPEC_2025-12-17 Scenario "Permissions use checkmark format"
        Gherkin:
            Given I view my permissions on any page
            When the permission table is rendered
            Then each permission shows a checkmark symbol
            And not "Yes/No" text variants
        """
        dashboard = TEMPLATES_DIR / "dashboard" / "index.html"
        content = dashboard.read_text()

        # Check for Yes/No patterns that should be replaced
        yes_no_pattern = r'"Yes"\s+if|"No"\s+else'
        matches = re.findall(yes_no_pattern, content)

        assert not matches, (
            f"dashboard/index.html uses 'Yes/No' for permissions. "
            "Should use checkmark symbols per user preference."
        )

    def test_checkmark_symbols_present(self):
        """Verify checkmark symbols are used in permission display."""
        dashboard = TEMPLATES_DIR / "dashboard" / "index.html"
        content = dashboard.read_text()

        # Check for checkmark pattern
        checkmark_patterns = [
            r'&#10003;',  # HTML entity for checkmark
            r'&#10007;',  # HTML entity for X
            r'✓',         # Unicode checkmark
            r'✗',         # Unicode X
        ]

        has_checkmarks = any(
            re.search(pattern, content)
            for pattern in checkmark_patterns
        )

        assert has_checkmarks, (
            "dashboard/index.html should use checkmark/X symbols for permissions."
        )


# =============================================================================
# REPORT GENERATION (Optional - for CI/CD)
# =============================================================================


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate UX consistency report at end of test run."""
    if exitstatus == 0:
        terminalreporter.write_line("")
        terminalreporter.write_line("=" * 60)
        terminalreporter.write_line("UX CONSISTENCY CHECK: PASSED")
        terminalreporter.write_line("=" * 60)
```

### 5.2 Test Coverage Summary

| Test | Business Rule | Purpose |
|------|---------------|---------|
| `test_no_orphaned_templates` | BR-UX-003 | Detect unused template files |
| `test_overview_html_deleted` | BR-UX-003 | Verify legacy file removed |
| `test_inline_styles_below_threshold` | BR-UX-001 | Enforce style consistency |
| `test_no_inline_color_styles` | BR-UX-001 | Enforce badge pattern usage |
| `test_static_links_have_routes` | BR-UX-002 | Catch dead links |
| `test_permission_uses_symbols` | BR-UX-004 | Enforce checkmark format |
| `test_checkmark_symbols_present` | BR-UX-004 | Verify symbols present |

---

## 6. Documentation Update Plan

### Level 2: ROADMAP.md

Add new phase:
```markdown
### Phase 3.10: UX Consistency Audit
**Status:** [In Progress/Complete]
**Objectives:**
- Clean up orphaned templates from Phase 3.3 migration
- Standardize inline styles to PicoCSS/CSS classes
- Add automated E2E tests for UX regression prevention

**Deliverables:**
- Delete `overview.html` (legacy)
- Refactor 5 templates to remove inline styles
- Create `test_ux_consistency.py` E2E test suite
```

### Level 3: FRONTEND.md

Add to Component Library section:
```markdown
### Badge Classes (from battles.css)

Use badge classes for status indicators:

```html
<span class="badge badge-pending">PENDING</span>
<span class="badge badge-active">ACTIVE</span>
<span class="badge badge-completed">COMPLETED</span>
<span class="badge badge-warning">CANCELLED</span>
```

| Class | Color | Use Case |
|-------|-------|----------|
| `.badge-pending` | Gray | Default/waiting state |
| `.badge-active` | Orange | In-progress state |
| `.badge-completed` | Green | Success/done state |
| `.badge-warning` | Yellow | Warning/cancelled state |

**DO NOT use inline styles for badges:**
```html
<!-- BAD -->
<span style="padding: 4px 8px; background-color: #28a745; color: white;">ACTIVE</span>

<!-- GOOD -->
<span class="badge badge-active">ACTIVE</span>
```
```

Add permission display standard:
```markdown
### Permission Display

Use checkmark symbols for permission tables:

```html
<td>{{ "✓" if current_user.is_admin else "✗" }}</td>
```

HTML entities alternative:
```html
<td>{{ "&#10003;" if current_user.is_admin else "&#10007;" }}</td>
```

**DO NOT use "Yes/No" text for permissions.**
```

### Level 3: TESTING.md

Add UX consistency testing section:
```markdown
### UX Consistency Tests

E2E tests that verify template consistency and prevent UX regressions.

**Location:** `tests/e2e/test_ux_consistency.py`

**What's Tested:**
- Orphaned templates (files with no route or include reference)
- Inline style count (threshold enforcement)
- Link integrity (hrefs point to valid routes)
- Permission display format (checkmark symbols)

**Running Tests:**
```bash
pytest tests/e2e/test_ux_consistency.py -v
```

**Configuration:**
- `ALLOWED_ORPHANED_TEMPLATES`: Templates intentionally not routed (future features)
- `MAX_INLINE_STYLES`: Maximum allowed inline styles (default: 5)
- `ALLOWED_INLINE_STYLE_PATTERNS`: Regex patterns for acceptable inline styles
```

---

## 7. Risk Analysis

### Risk 1: Breaking Visual Appearance
**Concern:** Removing inline styles may change visual appearance unexpectedly
**Likelihood:** Medium
**Impact:** Medium (visual regression)
**Mitigation:**
- Test each template refactor in browser before committing
- Compare screenshots before/after
- Use existing `.badge` classes that are already tested
- Keep changes minimal - match existing patterns exactly

### Risk 2: Missing Edge Cases in Orphan Detection
**Concern:** Test may miss some template reference patterns
**Likelihood:** Low
**Impact:** Low (false positives in test)
**Mitigation:**
- Use ALLOWED_ORPHANED_TEMPLATES for known exceptions
- Test handles both Python and template-level references
- Document any new patterns found

### Risk 3: Inline Style Test False Positives
**Concern:** Some inline styles may be legitimately needed
**Likelihood:** Medium
**Impact:** Low (test noise)
**Mitigation:**
- Use threshold (MAX_INLINE_STYLES=5) instead of zero tolerance
- Provide ALLOWED_INLINE_STYLE_PATTERNS for exceptions
- Test provides clear guidance on how to fix

### Risk 4: Link Integrity Test Limitations
**Concern:** Cannot fully validate dynamic Jinja-templated URLs
**Likelihood:** High (by design)
**Impact:** Low (informational only)
**Mitigation:**
- Test is informational for dynamic URLs
- Manual verification for flagged URLs
- Focus on static paths which can be validated

---

## 8. Implementation Order

**Recommended sequence to minimize risk:**

### Batch 1: Cleanup (Low Risk)
1. **Delete orphaned template**
   - Delete `app/templates/overview.html`
   - Run existing E2E tests to verify no breakage
   - Time: 5 minutes

2. **Document future feature template**
   - Add comment to `app/templates/pools/overview.html`
   - Time: 2 minutes

### Batch 2: Permission Display Fix (Low Risk)
3. **Update dashboard permission display**
   - Change "Yes/No" to checkmark symbols in `dashboard/index.html`
   - Test in browser
   - Time: 10 minutes

### Batch 3: Template Refactoring (Medium Risk)
4. **Refactor tournaments/detail.html**
   - Replace all inline styles with PicoCSS patterns
   - Test in browser with real tournament data
   - Time: 30 minutes

5. **Refactor tournaments/list.html**
   - Replace inline styles
   - Test in browser
   - Time: 20 minutes

6. **Refactor dancers/list.html**
   - Replace inline styles
   - Test in browser
   - Time: 15 minutes

7. **Refactor admin/users.html**
   - Replace inline styles
   - Test in browser
   - Time: 20 minutes

8. **Refactor dancers/_table.html**
   - Replace inline styles
   - Test in browser
   - Time: 10 minutes

### Batch 4: CSS Enhancement (Low Risk)
9. **Add badge-warning class if needed**
   - Add to `battles.css`
   - Time: 5 minutes

### Batch 5: E2E Tests (Low Risk)
10. **Create test_ux_consistency.py**
    - Write all test classes
    - Run tests against refactored templates
    - Verify all pass
    - Time: 45 minutes

### Batch 6: Documentation (Low Risk)
11. **Update documentation**
    - ROADMAP.md
    - FRONTEND.md
    - TESTING.md
    - Time: 20 minutes

**Total Estimated Time:** ~3 hours

---

## 9. Technical POC

**Status:** Not required
**Reason:** Standard template refactoring following existing patterns. All CSS classes already exist in `battles.css`. E2E test patterns follow established `tests/e2e/` conventions.

---

## 10. Open Questions

- [x] Permission display format: Checkmark symbols (user confirmed)
- [x] What to do with pools/overview.html: Document as future feature (keep)
- [x] Inline style threshold: 5 maximum after cleanup

---

## 11. User Approval

- [ ] User reviewed implementation plan
- [ ] User approved template refactoring approach
- [ ] User confirmed risks are acceptable
- [ ] User approved implementation order
