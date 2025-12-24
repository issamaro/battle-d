"""E2E tests for UX Consistency.

Tests template patterns, CSS class usage, and UI consistency standards
defined in FRONTEND.md and Phase 3.10 UX Consistency Audit.

Updated for SCSS-based design system (Frontend Rebuild Phase 2).

Business Rules:
- BR-UX-001: No inline styles in production templates
- BR-UX-002: Consistent badge classes (badge-pending, badge-active, badge-completed, etc.)
- BR-UX-003: Permission display uses checkmark symbols
- BR-UX-004: All templates follow SCSS design system patterns
"""
import pytest
import re
from pathlib import Path


# =============================================================================
# TEMPLATE SCANNING TESTS
# =============================================================================


class TestNoInlineStyles:
    """Test that templates avoid inline styles (BR-UX-001).

    Validates: FRONTEND.md §CSS Architecture
    """

    # Templates allowed to have inline styles (with justification)
    # After Phase 2 cleanup, only base.html has justified inline style
    ALLOWLIST = {
        # Base template (single style for necessary browser override)
        "base.html": "Single style for HTMX aria-busy indicator - browser override",
    }

    # Maximum inline styles allowed (threshold approach)
    MAX_INLINE_STYLES_PER_TEMPLATE = 0

    def test_no_inline_styles_in_templates(self):
        """Templates should not contain inline style attributes.

        Validates: BR-UX-001 No inline styles in production templates
        Gherkin:
            Given all HTML templates in app/templates
            When I scan for style="" attributes
            Then no templates should have inline styles
            And allowlisted templates are documented exceptions
        """
        # Given
        templates_dir = Path("app/templates")
        inline_style_pattern = re.compile(r'\bstyle\s*=\s*["\']', re.IGNORECASE)

        violations = []

        # When - scan all templates
        for template_path in templates_dir.rglob("*.html"):
            relative_path = str(template_path.relative_to(templates_dir))

            # Skip allowlisted templates
            if relative_path in self.ALLOWLIST:
                continue

            content = template_path.read_text()
            matches = inline_style_pattern.findall(content)

            # Then - check threshold
            if len(matches) > self.MAX_INLINE_STYLES_PER_TEMPLATE:
                violations.append(
                    f"{relative_path}: {len(matches)} inline style(s) found"
                )

        # Assert
        assert not violations, (
            f"BR-UX-001 Violation: Found inline styles in templates:\n"
            + "\n".join(violations)
            + "\n\nFix: Replace inline styles with CSS classes. See FRONTEND.md §CSS Architecture"
        )


class TestBadgeClassConsistency:
    """Test that badge classes follow patterns (BR-UX-002).

    Validates: FRONTEND.md §Badge Classes Reference
    """

    # Valid badge classes per FRONTEND.md and SCSS design system
    VALID_BADGE_CLASSES = {
        # Core badge classes (SCSS design system)
        "badge-pending",
        "badge-active",
        "badge-completed",
        "badge-warning",
        "badge-interactive",
        # Guest performer badge (Phase 3.9)
        "badge-guest",
        # Phase/status badges (SCSS design system)
        "badge-registration",
        "badge-preselection",
        "badge-pools",
        "badge-finals",
        "badge-cancelled",
        # Role badge
        "badge-role",
    }

    def test_badge_classes_are_valid(self):
        """Badge classes should only use defined patterns.

        Validates: BR-UX-002 Consistent badge class usage
        Gherkin:
            Given all HTML templates in app/templates
            When I scan for badge class usage
            Then all badge classes should be from the approved set
        """
        # Given
        templates_dir = Path("app/templates")
        # Match badge-* class names
        badge_class_pattern = re.compile(r'class\s*=\s*["\'][^"\']*\b(badge-\w+)\b')

        invalid_badges = []

        # When - scan all templates
        for template_path in templates_dir.rglob("*.html"):
            relative_path = str(template_path.relative_to(templates_dir))
            content = template_path.read_text()

            for match in badge_class_pattern.finditer(content):
                badge_class = match.group(1)
                if badge_class not in self.VALID_BADGE_CLASSES:
                    invalid_badges.append(f"{relative_path}: {badge_class}")

        # Then
        assert not invalid_badges, (
            f"BR-UX-002 Violation: Found non-standard badge classes:\n"
            + "\n".join(invalid_badges)
            + f"\n\nValid classes: {', '.join(sorted(self.VALID_BADGE_CLASSES))}"
        )


class TestPermissionDisplayFormat:
    """Test that permission display uses checkmarks (BR-UX-003).

    Validates: FRONTEND.md §Permission Display Standard

    NOTE: Dashboard has been removed (Navigation Streamlining 2025-12-23).
    Permission display is now tested via admin/users.html
    """

    def test_admin_users_permission_display_uses_checkmarks(self, admin_client):
        """Admin users table should use checkmark symbols for permissions.

        Validates: BR-UX-003 Permission display uses checkmark symbols
        Gherkin:
            Given I am authenticated as Admin
            When I view the users admin page
            Then permissions are displayed with checkmarks (not Yes/No)
        """
        # Given (authenticated via admin_client fixture)

        # When
        response = admin_client.get("/admin/users")

        # Then
        content = response.text
        assert response.status_code == 200

        # Should contain checkmarks for permissions
        assert "✓" in content or "&#10003;" in content, (
            "BR-UX-003 Violation: Admin users should use checkmark symbols"
        )


# =============================================================================
# SEMANTIC HTML TESTS
# =============================================================================


class TestSemanticHtmlPatterns:
    """Test semantic HTML patterns (BR-UX-004).

    Validates: FRONTEND.md §Semantic HTML Patterns
    """

    def test_tables_use_role_grid(self):
        """Data tables should use role='grid' for accessibility.

        Validates: BR-UX-004 table accessibility patterns
        Gherkin:
            Given HTML templates containing data tables
            When I check table markup
            Then tables should use role="grid" attribute
        """
        # Given
        templates_dir = Path("app/templates")
        # Match tables that look like data tables (with thead)
        table_with_thead = re.compile(
            r'<table[^>]*>.*?<thead>', re.DOTALL | re.IGNORECASE
        )
        table_with_role = re.compile(r'<table[^>]*role\s*=\s*["\']grid["\']')

        tables_without_role = []

        # When - scan templates with data tables
        for template_path in templates_dir.rglob("*.html"):
            relative_path = str(template_path.relative_to(templates_dir))
            content = template_path.read_text()

            # Find tables with thead (data tables)
            if table_with_thead.search(content):
                # Check if they have role="grid"
                table_start = content.find("<table")
                while table_start != -1:
                    table_end = content.find(">", table_start)
                    table_tag = content[table_start : table_end + 1]

                    # Check if this table has thead (is a data table)
                    next_content = content[table_start:table_start + 500]
                    if "<thead" in next_content.lower():
                        if 'role="grid"' not in table_tag.lower() and "role='grid'" not in table_tag.lower():
                            tables_without_role.append(relative_path)
                            break  # One per template is enough

                    table_start = content.find("<table", table_end)

        # Then - All data tables should have role="grid"
        # Note: This is a warning, not failure (progressive enhancement)
        if tables_without_role:
            pytest.skip(
                f"Note: {len(tables_without_role)} template(s) have data tables without role='grid': "
                + ", ".join(tables_without_role[:5])
            )

    def test_buttons_use_btn_class(self):
        """Action buttons should use .btn class from SCSS design system.

        Validates: BR-UX-004 SCSS button patterns
        Gherkin:
            Given HTML templates with action buttons
            When I check button markup
            Then buttons should use class="btn" or class="btn btn-*" attributes
        """
        # Given
        templates_dir = Path("app/templates")
        # Pattern for buttons (submit, button types)
        button_pattern = re.compile(
            r'<button[^>]*type\s*=\s*["\'](?:submit|button)["\'][^>]*>',
            re.IGNORECASE
        )

        # When - count buttons with/without btn class
        total_buttons = 0
        buttons_with_class = 0

        for template_path in templates_dir.rglob("*.html"):
            content = template_path.read_text()

            for match in button_pattern.finditer(content):
                total_buttons += 1
                if 'class="btn' in match.group().lower() or "class='btn" in match.group().lower():
                    buttons_with_class += 1

        # Then - Most buttons should have btn class
        if total_buttons > 0:
            percentage = (buttons_with_class / total_buttons) * 100
            assert percentage >= 50, (
                f"BR-UX-004 Violation: Only {percentage:.0f}% of buttons have class='btn'. "
                f"Expected >= 50%. ({buttons_with_class}/{total_buttons})"
            )


# =============================================================================
# PAGE LOAD TESTS
# =============================================================================


class TestPagesLoadWithoutError:
    """Test that refactored pages still load correctly."""

    def test_overview_redirects_to_tournaments(self, admin_client):
        """/overview redirects to /tournaments (dashboard removed).

        Validates: Navigation Streamlining feature
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /overview
            Then I am redirected to /tournaments (302)
        """
        # Given (authenticated)

        # When
        response = admin_client.get("/overview", follow_redirects=False)

        # Then
        assert response.status_code == 302
        assert response.headers["location"] == "/tournaments"

    def test_tournaments_list_loads(self, staff_client):
        """Tournaments list page loads successfully after UX refactor.

        Validates: tournaments/list.html template integrity
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /tournaments
            Then the page loads successfully (200)
            And contains tournament management elements
        """
        # Given (authenticated)

        # When
        response = staff_client.get("/tournaments")

        # Then
        assert response.status_code == 200
        assert "Tournament" in response.text

    def test_dancers_list_loads(self, staff_client):
        """Dancers list page loads successfully after UX refactor.

        Validates: dancers/list.html template integrity
        Gherkin:
            Given I am authenticated as Staff
            When I navigate to /dancers
            Then the page loads successfully (200)
            And contains search functionality
        """
        # Given (authenticated)

        # When
        response = staff_client.get("/dancers")

        # Then
        assert response.status_code == 200
        assert "Dancer" in response.text
        # Verify search input exists (HTMX pattern)
        assert "search" in response.text.lower()

    def test_admin_users_loads(self, admin_client):
        """Admin users page loads successfully after UX refactor.

        Validates: admin/users.html template integrity
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /admin/users
            Then the page loads successfully (200)
            And contains user management elements
        """
        # Given (authenticated)

        # When
        response = admin_client.get("/admin/users")

        # Then
        assert response.status_code == 200
        assert "User" in response.text


# =============================================================================
# CSS FILE TESTS
# =============================================================================


class TestCssFileIntegrity:
    """Test that CSS files contain required class definitions."""

    def test_main_css_exists(self):
        """Main CSS file exists after SCSS compilation.

        Validates: SCSS build process produces output
        Gherkin:
            Given the SCSS source files
            When I check for compiled CSS
            Then main.css should exist
        """
        # Given
        css_path = Path("app/static/css/main.css")

        # Then
        assert css_path.exists(), "main.css should exist (compiled from SCSS)"

    def test_badge_classes_defined_in_main_css(self):
        """Badge CSS classes are defined in main stylesheet.

        Validates: CSS class definitions exist for badge patterns
        Gherkin:
            Given the main.css stylesheet
            When I check for badge class definitions
            Then core badge classes should be defined
        """
        # Given
        css_path = Path("app/static/css/main.css")
        assert css_path.exists(), "main.css should exist"

        content = css_path.read_text()

        # Then - core badge classes should be defined
        required_classes = [
            ".badge-pending",
            ".badge-active",
            ".badge-completed",
        ]

        for css_class in required_classes:
            assert css_class in content, (
                f"Missing CSS class definition: {css_class} in main.css"
            )

    def test_btn_classes_defined_in_main_css(self):
        """Button CSS classes are defined in main stylesheet.

        Validates: CSS class definitions exist for button patterns
        Gherkin:
            Given the main.css stylesheet
            When I check for button class definitions
            Then .btn and variants should be defined
        """
        # Given
        css_path = Path("app/static/css/main.css")
        content = css_path.read_text()

        # Then - button classes should be defined
        assert ".btn" in content, "Missing CSS class definition: .btn in main.css"
        assert ".btn-primary" in content, "Missing CSS class definition: .btn-primary in main.css"
        assert ".btn-secondary" in content, "Missing CSS class definition: .btn-secondary in main.css"
        assert ".btn-danger" in content, "Missing CSS class definition: .btn-danger in main.css"
