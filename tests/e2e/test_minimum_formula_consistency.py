"""E2E tests for Minimum Performer Formula Consistency.

Verifies BR-MIN-001: Minimum performers = (groups_ideal × 2) + 1
Ensures the same minimum value is shown across all screens.

See: FEATURE_SPEC_2025-12-17_MINIMUM-PERFORMER-FORMULA-INCONSISTENCY.md
"""
import pytest
import re

from tests.e2e import (
    assert_status_ok,
    assert_contains_text,
)


class TestMinimumFormulaConsistency:
    """
    Feature: Consistent minimum performer display
      As an admin
      I want to see the same minimum performer count across all screens
      So that I can accurately plan my tournament registration
    """

    def test_add_category_shows_correct_minimum_initial_value(self, staff_client):
        """Add category form shows correct minimum (5) on page load.

        Validates: feature-spec.md Scenario "Add Category shows correct minimum"
        Gherkin:
            Given I am authenticated as Staff
            And I have created a tournament
            When I navigate to add category page
            Then the initial minimum display shows "5" (not "6")
            And the formula text shows "+ 1 elimination" (not "+ 2")
        """
        # Given - Create tournament
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "Minimum Test Tournament"},
            follow_redirects=True,
        )
        assert_status_ok(response)

        # Extract tournament ID from URL
        tournament_id = re.search(r"/tournaments/([^/]+)", str(response.url)).group(1)

        # When - Navigate to add category
        response = staff_client.get(f"/tournaments/{tournament_id}/add-category")

        # Then - Check initial values (before JS runs)
        assert_status_ok(response)

        # Initial HTML should show "5" not "6"
        # The span with id="min-display" should contain 5
        assert '>5</span>' in response.text, (
            "Initial minimum display should be 5, not 6"
        )

        # Formula should show "+ 1 elimination"
        assert "+ 1 elimination" in response.text, (
            "Formula should show '+ 1 elimination', not '+ 2 elimination'"
        )

    def test_tournament_detail_shows_correct_minimum(self, staff_client):
        """Tournament detail page shows correct minimum (5) for category.

        Validates: feature-spec.md Scenario "Tournament Detail shows correct minimum"
        Gherkin:
            Given I am authenticated as Staff
            And I have created a tournament with a category (groups_ideal=2)
            When I view the tournament detail page
            Then the "Minimum Required" column shows "5"
        """
        # Given - Create tournament
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "Detail Minimum Test Tournament"},
            follow_redirects=True,
        )
        assert_status_ok(response)

        # Extract tournament ID
        tournament_id = re.search(r"/tournaments/([^/]+)", str(response.url)).group(1)

        # Add category with default values (groups_ideal=2, performers_ideal=4)
        staff_client.post(
            f"/tournaments/{tournament_id}/add-category",
            data={
                "name": "Test Category",
                "groups_ideal": "2",
                "performers_ideal": "4",
            },
            follow_redirects=True,
        )

        # When - View tournament detail
        response = staff_client.get(f"/tournaments/{tournament_id}")

        # Then - Minimum Required column should show 5
        assert_status_ok(response)

        # The table should contain "5" in the Minimum Required column
        # For groups_ideal=2: (2 * 2) + 1 = 5
        html = response.text

        # Find the table row with our category and check minimum value
        # The value "5" should appear after "Minimum Required" header
        assert_contains_text(html, "Minimum Required")

        # Check that 5 appears in the appropriate context (not just anywhere)
        # Look for the pattern: <td>5</td> in the categories table
        assert ">5</td>" in html or "> 5</td>" in html or ">5<" in html, (
            f"Minimum Required should be 5, not 6. "
            f"Formula: (groups_ideal=2 * 2) + 1 = 5"
        )

    def test_minimum_formula_examples(self, staff_client):
        """Verify minimum formula for different pool configurations.

        Validates: VALIDATION_RULES.md §3 Minimum Performer Requirements
        Gherkin:
            Given I am authenticated as Staff
            When I create categories with different groups_ideal values
            Then the minimum follows the formula (groups_ideal × 2) + 1:
              | groups_ideal | expected_minimum |
              | 1            | 3                |
              | 2            | 5                |
              | 3            | 7                |
              | 4            | 9                |
        """
        # Given - Create tournament
        response = staff_client.post(
            "/tournaments/create",
            data={"name": "Formula Examples Tournament"},
            follow_redirects=True,
        )
        tournament_id = re.search(r"/tournaments/([^/]+)", str(response.url)).group(1)

        # Test cases: (groups_ideal, expected_minimum)
        test_cases = [
            (1, 3),  # (1 * 2) + 1 = 3
            (2, 5),  # (2 * 2) + 1 = 5
            (3, 7),  # (3 * 2) + 1 = 7
        ]

        for groups_ideal, expected_minimum in test_cases:
            # When - Create category with specific groups_ideal
            staff_client.post(
                f"/tournaments/{tournament_id}/add-category",
                data={
                    "name": f"Test {groups_ideal} pools",
                    "groups_ideal": str(groups_ideal),
                    "performers_ideal": "4",
                },
                follow_redirects=True,
            )

        # Then - Check tournament detail shows correct minimums
        response = staff_client.get(f"/tournaments/{tournament_id}")
        html = response.text

        # Verify each expected minimum appears in the response
        for groups_ideal, expected_minimum in test_cases:
            assert f">{expected_minimum}<" in html or f">{expected_minimum}</td>" in html, (
                f"Category with groups_ideal={groups_ideal} should show "
                f"minimum={expected_minimum}, formula: ({groups_ideal} * 2) + 1"
            )
