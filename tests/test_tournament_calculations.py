"""Tests for tournament calculation utilities."""

import pytest

from app.utils.tournament_calculations import (
    calculate_minimum_performers,
    calculate_adjusted_minimum,
    calculate_pool_capacity,
    distribute_performers_to_pools,
    calculate_minimum_for_category,
)


class TestCalculateMinimumPerformers:
    """Tests for calculate_minimum_performers function."""

    def test_formula_with_default_config(self):
        """Test minimum calculation with default groups_ideal=2."""
        # Formula: (groups_ideal * 2) + 1
        # (2 * 2) + 1 = 5
        assert calculate_minimum_performers(2) == 5

    def test_formula_with_three_pools(self):
        """Test minimum calculation with 3 pools."""
        # (3 * 2) + 1 = 7
        assert calculate_minimum_performers(3) == 7

    def test_formula_with_four_pools(self):
        """Test minimum calculation with 4 pools."""
        # (4 * 2) + 1 = 9
        assert calculate_minimum_performers(4) == 9

    def test_formula_with_one_pool(self):
        """Test minimum calculation with 1 pool."""
        # (1 * 2) + 1 = 3
        assert calculate_minimum_performers(1) == 3

    def test_invalid_groups_ideal_raises_error(self):
        """Test that groups_ideal < 1 raises ValueError."""
        with pytest.raises(ValueError, match="groups_ideal must be at least 1"):
            calculate_minimum_performers(0)

        with pytest.raises(ValueError, match="groups_ideal must be at least 1"):
            calculate_minimum_performers(-1)


class TestCalculateAdjustedMinimum:
    """Tests for calculate_adjusted_minimum function (BR-GUEST-004).

    Formula: max(2, (groups_ideal * 2) + 1 - guest_count)

    Guest performers reduce the minimum required because they are
    guaranteed to qualify for pools.
    """

    def test_no_guests_equals_standard_minimum(self):
        """Test that zero guests returns standard minimum.

        Validates: BR-GUEST-004 baseline (adjusted minimum = standard minimum when no guests)
        """
        # Standard: (2 * 2) + 1 = 5
        assert calculate_adjusted_minimum(2, guest_count=0) == 5

        # Standard: (3 * 2) + 1 = 7
        assert calculate_adjusted_minimum(3, guest_count=0) == 7

    def test_one_guest_reduces_by_one(self):
        """Test that one guest reduces minimum by 1.

        Validates: BR-GUEST-004 Scenario "Minimum reduced by guest count"
        Gherkin:
            Given a category with groups_ideal = 2
            And the standard minimum is 5 performers
            When I register 1 guest
            Then the adjusted minimum becomes 4 (5 - 1)
        """
        # (2 * 2) + 1 - 1 = 4
        assert calculate_adjusted_minimum(2, guest_count=1) == 4

        # (3 * 2) + 1 - 1 = 6
        assert calculate_adjusted_minimum(3, guest_count=1) == 6

    def test_two_guests_reduces_by_two(self):
        """Test that two guests reduce minimum by 2.

        Validates: BR-GUEST-004 Scenario "Minimum reduced by guest count"
        Gherkin:
            Given a category with groups_ideal = 2
            And the standard minimum is 5 performers
            When I register 2 guests
            Then the adjusted minimum becomes 3 (5 - 2)
        """
        # (2 * 2) + 1 - 2 = 3
        assert calculate_adjusted_minimum(2, guest_count=2) == 3

    def test_floor_at_two(self):
        """Test that minimum never goes below 2.

        Validates: BR-GUEST-004 Scenario "Minimum cannot go below 2"
        Gherkin:
            Given a category with groups_ideal = 2
            And the standard minimum is 5 performers
            When I register 4 guests
            Then the adjusted minimum is 2 (not 1)
        """
        # (2 * 2) + 1 - 3 = 2 (would be 2)
        assert calculate_adjusted_minimum(2, guest_count=3) == 2

        # (2 * 2) + 1 - 4 = 1 → max(2, 1) = 2
        assert calculate_adjusted_minimum(2, guest_count=4) == 2

        # (2 * 2) + 1 - 5 = 0 → max(2, 0) = 2
        assert calculate_adjusted_minimum(2, guest_count=5) == 2

        # Even more guests still floor at 2
        assert calculate_adjusted_minimum(2, guest_count=10) == 2

    def test_with_three_pools(self):
        """Test adjusted minimum with 3 pools (groups_ideal=3)."""
        # Standard: (3 * 2) + 1 = 7
        assert calculate_adjusted_minimum(3, guest_count=0) == 7

        # 1 guest: 7 - 1 = 6
        assert calculate_adjusted_minimum(3, guest_count=1) == 6

        # 2 guests: 7 - 2 = 5
        assert calculate_adjusted_minimum(3, guest_count=2) == 5

        # 5 guests: max(2, 7-5) = max(2, 2) = 2
        assert calculate_adjusted_minimum(3, guest_count=5) == 2

    def test_invalid_groups_ideal_raises_error(self):
        """Test that groups_ideal < 1 raises ValueError."""
        with pytest.raises(ValueError, match="groups_ideal must be at least 1"):
            calculate_adjusted_minimum(0, guest_count=0)

    def test_negative_guest_count_raises_error(self):
        """Test that negative guest count raises ValueError."""
        with pytest.raises(ValueError, match="guest_count cannot be negative"):
            calculate_adjusted_minimum(2, guest_count=-1)

    def test_guest_count_default_is_zero(self):
        """Test that guest_count defaults to 0."""
        # Should work without guest_count
        assert calculate_adjusted_minimum(2) == 5

    def test_real_world_scenario(self):
        """Test real-world scenario from VALIDATION_RULES.md.

        Validates: BR-GUEST-004 Scenario "Phase validation uses adjusted minimum"
        Gherkin:
            Given a category with groups_ideal = 2
            And 2 guests are registered
            And 3 regular performers are registered
            When I attempt to advance to PRESELECTION
            Then the validation passes (5 total >= 3 adjusted minimum + 2 guests)

        Example: 2 pools (groups_ideal=2), 2 guests
        - Standard minimum = (2 × 2) + 1 = 5
        - With 2 guests: 5 - 2 = 3 regulars needed
        - Total: 3 regulars + 2 guests = 5 performers (valid)
        """
        adjusted_min = calculate_adjusted_minimum(2, guest_count=2)
        assert adjusted_min == 3

        # Verify this makes sense:
        # If we have 3 performers total (2 guests + 1 regular), that's >= adjusted_min
        total_performers = 2 + 1  # 2 guests + 1 regular
        assert total_performers >= adjusted_min


class TestCalculatePoolCapacity:
    """Tests for calculate_pool_capacity function implementing BR-POOL-001."""

    def test_minimum_case(self):
        """Test pool capacity with exactly minimum performers.

        5 performers, 2 pools, ideal 4 per pool:
        - ideal_capacity = 8, registered (5) < ideal + 1 (9)
        - Reduce: 2×3=6 > 5, 2×2=4 < 5 ✓
        - Result: (4, 2, 1) - 4 capacity, 2 per pool, 1 eliminated
        """
        capacity, per_pool, eliminated = calculate_pool_capacity(5, 2)
        assert capacity == 4
        assert per_pool == 2
        assert eliminated == 1

    def test_ideal_capacity_case(self):
        """Test pool capacity when registered >= ideal + 1.

        9 performers, 2 pools, ideal 4 per pool:
        - ideal_capacity = 8, registered (9) >= ideal + 1 (9) ✓
        - Result: (8, 4, 1) - use ideal capacity
        """
        capacity, per_pool, eliminated = calculate_pool_capacity(9, 2, 4)
        assert capacity == 8
        assert per_pool == 4
        assert eliminated == 1

    def test_reduce_pool_size_case(self):
        """Test pool capacity when registered = ideal (must reduce).

        8 performers, 2 pools, ideal 4 per pool:
        - ideal_capacity = 8, registered (8) < ideal + 1 (9)
        - Reduce: 2×4=8 NOT < 8, 2×3=6 < 8 ✓
        - Result: (6, 3, 2) - 6 capacity, 3 per pool, 2 eliminated
        """
        capacity, per_pool, eliminated = calculate_pool_capacity(8, 2, 4)
        assert capacity == 6
        assert per_pool == 3
        assert eliminated == 2

    def test_larger_tournament(self):
        """Test pool capacity with many more performers than ideal.

        12 performers, 2 pools, ideal 4 per pool:
        - ideal_capacity = 8, registered (12) >= ideal + 1 (9) ✓
        - Result: (8, 4, 4) - use ideal capacity
        """
        capacity, per_pool, eliminated = calculate_pool_capacity(12, 2, 4)
        assert capacity == 8
        assert per_pool == 4
        assert eliminated == 4

    def test_three_pools(self):
        """Test pool capacity with 3 pools.

        10 performers, 3 pools, ideal 4 per pool:
        - ideal_capacity = 12, registered (10) < ideal + 1 (13)
        - Reduce: 3×4=12 NOT < 10, 3×3=9 < 10 ✓
        - Result: (9, 3, 1)
        """
        capacity, per_pool, eliminated = calculate_pool_capacity(10, 3, 4)
        assert capacity == 9
        assert per_pool == 3
        assert eliminated == 1

    def test_always_equal_pool_sizes(self):
        """Test BR-POOL-001: All pools have EQUAL sizes."""
        test_cases = [
            (5, 2, 4),   # Minimum case
            (8, 2, 4),   # Reduce needed
            (9, 2, 4),   # Ideal capacity
            (12, 2, 4),  # Large tournament
            (10, 3, 4),  # Three pools
            (7, 2, 4),   # 7 performers
        ]

        for registered, groups, ideal in test_cases:
            capacity, per_pool, eliminated = calculate_pool_capacity(registered, groups, ideal)
            # Capacity must be evenly divisible
            assert capacity % groups == 0, (
                f"Capacity {capacity} must be divisible by {groups} pools"
            )
            # Per pool calculation must match
            assert capacity // groups == per_pool

    def test_always_eliminates_at_least_one(self):
        """Test that at least 1 performer is always eliminated."""
        test_cases = [(5, 2), (8, 2), (9, 2), (10, 3), (20, 4)]

        for registered, groups in test_cases:
            _, _, eliminated = calculate_pool_capacity(registered, groups)
            assert eliminated >= 1, (
                f"Must eliminate at least 1 with {registered} registered and {groups} groups"
            )

    def test_insufficient_performers_raises_error(self):
        """Test that insufficient performers raises ValueError."""
        # Need minimum 5 for 2 pools
        with pytest.raises(ValueError, match="Need at least 5 performers"):
            calculate_pool_capacity(4, 2)

        # Need minimum 7 for 3 pools
        with pytest.raises(ValueError, match="Need at least 7 performers"):
            calculate_pool_capacity(6, 3)


class TestDistributePerformersToPoolsS:
    """Tests for distribute_performers_to_pools function implementing BR-POOL-001."""

    def test_equal_distribution_two_pools(self):
        """Test equal distribution with 2 pools (BR-POOL-001)."""
        # 8 performers, 2 pools → [4, 4]
        assert distribute_performers_to_pools(8, 2) == [4, 4]

        # 6 performers, 2 pools → [3, 3]
        assert distribute_performers_to_pools(6, 2) == [3, 3]

        # 4 performers, 2 pools → [2, 2]
        assert distribute_performers_to_pools(4, 2) == [2, 2]

    def test_equal_distribution_three_pools(self):
        """Test equal distribution with 3 pools (BR-POOL-001)."""
        # 12 performers, 3 pools → [4, 4, 4]
        assert distribute_performers_to_pools(12, 3) == [4, 4, 4]

        # 9 performers, 3 pools → [3, 3, 3]
        assert distribute_performers_to_pools(9, 3) == [3, 3, 3]

        # 6 performers, 3 pools → [2, 2, 2]
        assert distribute_performers_to_pools(6, 3) == [2, 2, 2]

    def test_uneven_distribution_raises_error(self):
        """Test BR-POOL-001: Uneven distributions raise ValueError."""
        # 9 performers cannot be evenly split into 2 pools
        with pytest.raises(ValueError, match="BR-POOL-001.*Equal Pool Sizes"):
            distribute_performers_to_pools(9, 2)

        # 7 performers cannot be evenly split into 2 pools
        with pytest.raises(ValueError, match="BR-POOL-001.*Equal Pool Sizes"):
            distribute_performers_to_pools(7, 2)

        # 10 performers cannot be evenly split into 3 pools
        with pytest.raises(ValueError, match="BR-POOL-001.*Equal Pool Sizes"):
            distribute_performers_to_pools(10, 3)

        # 11 performers cannot be evenly split into 3 pools
        with pytest.raises(ValueError, match="BR-POOL-001.*Equal Pool Sizes"):
            distribute_performers_to_pools(11, 3)

    def test_all_pools_have_equal_size(self):
        """Test that all pools have exactly the same size (BR-POOL-001)."""
        test_cases = [
            (4, 2),   # 2 pools of 2
            (6, 2),   # 2 pools of 3
            (8, 2),   # 2 pools of 4
            (6, 3),   # 3 pools of 2
            (9, 3),   # 3 pools of 3
            (12, 3),  # 3 pools of 4
            (8, 4),   # 4 pools of 2
            (12, 4),  # 4 pools of 3
        ]

        for capacity, groups in test_cases:
            result = distribute_performers_to_pools(capacity, groups)
            # All sizes must be identical
            assert len(set(result)) == 1, (
                f"All pools must have equal size, got {result}"
            )
            # Size must equal capacity / groups
            assert result[0] == capacity // groups

    def test_total_performers_matches(self):
        """Test that sum of pool sizes equals total performers."""
        assert sum(distribute_performers_to_pools(8, 2)) == 8
        assert sum(distribute_performers_to_pools(12, 3)) == 12
        assert sum(distribute_performers_to_pools(16, 4)) == 16

    def test_minimum_two_per_pool(self):
        """Test that each pool has at least 2 performers."""
        # Minimum valid: 4 performers, 2 pools → [2, 2]
        result = distribute_performers_to_pools(4, 2)
        assert all(size >= 2 for size in result)

        # Minimum valid: 6 performers, 3 pools → [2, 2, 2]
        result = distribute_performers_to_pools(6, 3)
        assert all(size >= 2 for size in result)

    def test_insufficient_performers_raises_error(self):
        """Test that too few performers raises ValueError."""
        # Need at least 4 for 2 pools (2 per pool)
        with pytest.raises(ValueError, match="minimum 2 per pool"):
            distribute_performers_to_pools(3, 2)

        # Need at least 6 for 3 pools
        with pytest.raises(ValueError, match="minimum 2 per pool"):
            distribute_performers_to_pools(5, 3)


class TestCalculateMinimumForCategory:
    """Tests for calculate_minimum_for_category function."""

    def test_default_configuration(self):
        """Test calculation with default config (2 pools, 4 ideal per pool)."""
        result = calculate_minimum_for_category(2, 4)

        assert result["minimum_required"] == 5  # (2*2) + 1
        assert result["ideal_capacity"] == 8  # 2 * 4
        assert result["min_pool_performers"] == 4  # 2 * 2
        assert result["min_eliminated"] == 1

    def test_larger_configuration(self):
        """Test calculation with larger config (3 pools, 6 ideal per pool)."""
        result = calculate_minimum_for_category(3, 6)

        assert result["minimum_required"] == 7  # (3*2) + 1
        assert result["ideal_capacity"] == 18  # 3 * 6
        assert result["min_pool_performers"] == 6  # 3 * 2
        assert result["min_eliminated"] == 1

    def test_all_keys_present(self):
        """Test that all required keys are present in result."""
        result = calculate_minimum_for_category(2, 4)

        assert "minimum_required" in result
        assert "ideal_capacity" in result
        assert "min_pool_performers" in result
        assert "min_eliminated" in result


class TestBusinessRulesIntegration:
    """Integration tests ensuring business rules are correctly implemented."""

    def test_minimum_five_for_default_config(self):
        """Test that minimum is 5 for default configuration.

        Formula: (groups_ideal * 2) + 1
        For groups_ideal=2: (2 * 2) + 1 = 5
        """
        # Default configuration: groups_ideal=2, performers_ideal=4
        minimum = calculate_minimum_performers(2)

        # Formula yields 5 for groups_ideal=2
        assert minimum == 5, "Minimum should be 5 for groups_ideal=2"

    def test_preselection_always_eliminates(self):
        """Test that preselection always eliminates at least 1 performer."""
        # Test various configurations
        test_cases = [
            (5, 2),  # Minimum case
            (8, 2),
            (10, 3),
            (20, 4),
        ]

        for registered, groups in test_cases:
            _, _, eliminated = calculate_pool_capacity(registered, groups)
            assert eliminated >= 1, (
                f"Must eliminate at least 1 performer "
                f"({registered} performers, {groups} pools)"
            )

    def test_registered_greater_than_pool_performers(self):
        """Test that registered > pool_performers (preselection mandatory)."""
        # Test various configurations
        test_cases = [
            (5, 2),
            (8, 2),
            (10, 3),
            (20, 4),
        ]

        for registered, groups in test_cases:
            pool_capacity, _, _ = calculate_pool_capacity(registered, groups)
            assert registered > pool_capacity, (
                f"Registered ({registered}) must be > pool_capacity ({pool_capacity}) "
                "to ensure preselection is mandatory"
            )

    def test_pool_capacity_workflow(self):
        """Test complete workflow: calculate capacity then distribute.

        BR-POOL-001: Pool capacity from calculate_pool_capacity should
        be directly usable with distribute_performers_to_pools.
        """
        test_cases = [
            (5, 2, 4),   # Minimum case
            (8, 2, 4),   # Reduce needed
            (9, 2, 4),   # Ideal capacity
            (12, 2, 4),  # Large tournament
            (10, 3, 4),  # Three pools
            (7, 3, 4),   # Minimum for 3 pools
        ]

        for registered, groups, ideal in test_cases:
            # Step 1: Calculate pool capacity
            capacity, per_pool, eliminated = calculate_pool_capacity(registered, groups, ideal)

            # Step 2: Distribute to pools - should NOT raise
            pool_sizes = distribute_performers_to_pools(capacity, groups)

            # Verify results
            assert len(pool_sizes) == groups
            assert sum(pool_sizes) == capacity
            assert all(size == per_pool for size in pool_sizes)
            assert registered == capacity + eliminated
