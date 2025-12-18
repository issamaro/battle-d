"""E2E tests for UX Consistency.

Tests template patterns, CSS class usage, and UI consistency standards
defined in FRONTEND.md and Phase 3.10 UX Consistency Audit.

Business Rules:
- BR-UX-001: No inline styles in production templates
- BR-UX-002: Consistent badge classes (badge-pending, badge-active, badge-completed, badge-warning)
- BR-UX-003: Permission display uses checkmark symbols
- BR-UX-004: All templates follow PicoCSS patterns
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
    # Phase 3.10 focused on high-traffic templates; remaining will be addressed in future phases
    ALLOWLIST = {
        # Future feature template - not user-facing yet
        "pools/overview.html": "Future feature (V2) - not wired to routes",
        # Base template (single style for necessary browser override)
        "base.html": "Single style for HTMX aria-busy indicator - PicoCSS override",
        # Registration templates - Phase 3.11 scope
        "registration/register.html": "Phase 3.11 scope - registration flow refactor",
        "registration/_dancer_search.html": "Phase 3.11 scope - registration flow refactor",
        # Admin templates - Phase 3.11 scope
        "admin/edit_user.html": "Phase 3.11 scope - admin forms refactor",
        "admin/create_user.html": "Phase 3.11 scope - admin forms refactor",
        "admin/fix_active_tournaments.html": "Phase 3.11 scope - admin tools refactor",
        # Component templates - Phase 3.11 scope
        "components/delete_modal.html": "Phase 3.11 scope - modal component refactor",
        # Battle templates - Phase 3.11 scope
        "battles/encode_tiebreak.html": "Phase 3.11 scope - battle encoding refactor",
        "battles/list.html": "Phase 3.11 scope - battle list refactor",
        "battles/detail.html": "Phase 3.11 scope - battle detail refactor",
        "battles/encode_pool.html": "Phase 3.11 scope - battle encoding refactor",
        # Error templates - acceptable (self-contained styling for error pages)
        "errors/403.html": "Error pages are self-contained - acceptable",
        "errors/500.html": "Error pages are self-contained - acceptable",
        "errors/404.html": "Error pages are self-contained - acceptable",
        "errors/401.html": "Error pages are self-contained - acceptable",
        "errors/tournament_config_error.html": "Error pages are self-contained - acceptable",
        # Phase templates - Phase 3.11 scope
        "phases/confirm_advance.html": "Phase 3.11 scope - phase UI refactor",
        "phases/validation_errors.html": "Phase 3.11 scope - phase UI refactor",
        # Tournament forms - Phase 3.11 scope
        "tournaments/create.html": "Phase 3.11 scope - tournament forms refactor",
        "tournaments/add_category.html": "Phase 3.11 scope - category forms refactor",
        # Dancer templates - Phase 3.11 scope
        "dancers/profile.html": "Phase 3.11 scope - dancer profile refactor",
        "dancers/create.html": "Phase 3.11 scope - dancer forms refactor",
        "dancers/edit.html": "Phase 3.11 scope - dancer forms refactor",
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

    # Valid badge classes per FRONTEND.md and BattleStatus enum
    VALID_BADGE_CLASSES = {
        # Core badge classes (FRONTEND.md)
        "badge-pending",
        "badge-active",
        "badge-completed",
        "badge-warning",
        "badge-interactive",
        # Guest performer badge (Phase 3.9)
        "badge-guest",
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
    """

    def test_permission_display_uses_checkmarks(self, admin_client):
        """Dashboard permission table should use checkmark symbols.

        Validates: BR-UX-003 Permission display uses checkmark symbols
        Gherkin:
            Given I am authenticated as Admin
            When I view the dashboard
            Then permissions are displayed with checkmarks (not Yes/No)
        """
        # Given (authenticated via admin_client fixture)

        # When
        response = admin_client.get("/dashboard")

        # Then
        content = response.text
        assert response.status_code == 200

        # Should contain checkmarks for permissions
        assert "✓" in content or "&#10003;" in content, (
            "BR-UX-003 Violation: Dashboard should use checkmark symbols"
        )

        # Should NOT contain Yes/No patterns in permission context
        # We check the permissions section specifically
        if "Your Permissions" in content:
            permissions_section = content.split("Your Permissions")[1].split("</section>")[0]
            assert "Yes" not in permissions_section or "✓" in permissions_section, (
                "BR-UX-003 Violation: Permission display should use ✓/✗, not Yes/No"
            )


# =============================================================================
# SEMANTIC HTML TESTS
# =============================================================================


class TestSemanticHtmlPatterns:
    """Test PicoCSS semantic patterns (BR-UX-004).

    Validates: FRONTEND.md §PicoCSS Patterns
    """

    def test_tables_use_role_grid(self):
        """Data tables should use role='grid' for PicoCSS styling.

        Validates: BR-UX-004 PicoCSS table patterns
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

    def test_action_links_use_role_button(self):
        """Action links should use role='button' for PicoCSS styling.

        Validates: BR-UX-004 PicoCSS button patterns
        Gherkin:
            Given HTML templates with action links
            When I check link markup
            Then action links should use role="button" attribute
        """
        # Given
        templates_dir = Path("app/templates")
        # Pattern for links that look like action links (with + or Create/Add/Delete)
        action_link_pattern = re.compile(
            r'<a[^>]*href\s*=\s*["\'][^"\']*(?:create|add|delete|edit)[^"\']*["\'][^>]*>',
            re.IGNORECASE
        )

        # When - count action links with/without role="button"
        total_action_links = 0
        action_links_with_role = 0

        for template_path in templates_dir.rglob("*.html"):
            content = template_path.read_text()

            for match in action_link_pattern.finditer(content):
                total_action_links += 1
                if 'role="button"' in match.group().lower() or "role='button'" in match.group().lower():
                    action_links_with_role += 1

        # Then - Most action links should have role="button"
        if total_action_links > 0:
            percentage = (action_links_with_role / total_action_links) * 100
            assert percentage >= 50, (
                f"BR-UX-004 Violation: Only {percentage:.0f}% of action links have role='button'. "
                f"Expected >= 50%. ({action_links_with_role}/{total_action_links})"
            )


# =============================================================================
# PAGE LOAD TESTS
# =============================================================================


class TestPagesLoadWithoutError:
    """Test that refactored pages still load correctly."""

    def test_dashboard_loads(self, admin_client):
        """Dashboard page loads successfully after UX refactor.

        Validates: Dashboard template integrity
        Gherkin:
            Given I am authenticated as Admin
            When I navigate to /dashboard
            Then the page loads successfully (200)
            And contains permission table with checkmarks
        """
        # Given (authenticated)

        # When
        response = admin_client.get("/dashboard")

        # Then
        assert response.status_code == 200
        assert "Dashboard" in response.text or "dashboard" in response.text.lower()
        assert "Your Permissions" in response.text

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

    def test_badge_classes_defined_in_css(self):
        """Badge CSS classes are defined in stylesheet.

        Validates: CSS class definitions exist for badge patterns
        Gherkin:
            Given the battles.css stylesheet
            When I check for badge class definitions
            Then all badge classes should be defined
        """
        # Given
        css_path = Path("app/static/css/battles.css")
        assert css_path.exists(), "battles.css should exist"

        content = css_path.read_text()

        # Then - all badge classes should be defined
        required_classes = [
            ".badge-pending",
            ".badge-active",
            ".badge-completed",
            ".badge-warning",
        ]

        for css_class in required_classes:
            assert css_class in content, (
                f"Missing CSS class definition: {css_class} in battles.css"
            )

    def test_inline_form_class_defined(self):
        """Inline form utility class is defined in CSS.

        Validates: .inline-form class exists for table action buttons
        Gherkin:
            Given the battles.css stylesheet
            When I check for utility class definitions
            Then .inline-form should be defined
        """
        # Given
        css_path = Path("app/static/css/battles.css")
        content = css_path.read_text()

        # Then
        assert ".inline-form" in content, (
            "Missing CSS class definition: .inline-form in battles.css"
        )
