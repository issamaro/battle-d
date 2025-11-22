"""Tests for tournament calculation utilities."""

import pytest

from app.utils.tournament_calculations import (
    calculate_minimum_performers,
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


class TestCalculatePoolCapacity:
    """Tests for calculate_pool_capacity function."""

    def test_minimum_case(self):
        """Test pool capacity with exactly minimum performers."""
        # 5 performers, 2 pools → eliminate 1, keep 4 (2 per pool)
        pool_performers, eliminated = calculate_pool_capacity(5, 2)
        assert pool_performers == 4
        assert eliminated == 1

    def test_standard_case(self):
        """Test pool capacity with 8 performers."""
        # 8 performers → eliminate 2 → keep 6
        pool_performers, eliminated = calculate_pool_capacity(8, 2)
        assert pool_performers == 6
        assert eliminated == 2

    def test_larger_tournament(self):
        """Test pool capacity with 20 performers."""
        # 20 performers → eliminate 5 → keep 15
        # Ensure at least 2 per pool minimum
        pool_performers, eliminated = calculate_pool_capacity(20, 2)
        assert pool_performers == 15  # Eliminate 5
        assert eliminated == 5

    def test_three_pools(self):
        """Test pool capacity with 3 pools."""
        # 10 performers, 3 pools → minimum is 7
        # Eliminate 2 → keep 8
        pool_performers, eliminated = calculate_pool_capacity(10, 3)
        assert pool_performers == 8
        assert eliminated == 2

    def test_always_eliminates_at_least_one(self):
        """Test that at least 1 performer is always eliminated."""
        # Edge case: exactly minimum (5 performers, 2 pools)
        pool_performers, eliminated = calculate_pool_capacity(5, 2)
        assert eliminated >= 1

    def test_insufficient_performers_raises_error(self):
        """Test that insufficient performers raises ValueError."""
        # Need minimum 5 for 2 pools
        with pytest.raises(ValueError, match="Need at least 5 performers"):
            calculate_pool_capacity(4, 2)

        # Need minimum 7 for 3 pools
        with pytest.raises(ValueError, match="Need at least 7 performers"):
            calculate_pool_capacity(6, 3)


class TestDistributePerformersToPoolsS:
    """Tests for distribute_performers_to_pools function."""

    def test_even_distribution(self):
        """Test even distribution of performers."""
        # 8 performers, 2 pools → [4, 4]
        assert distribute_performers_to_pools(8, 2) == [4, 4]

        # 12 performers, 3 pools → [4, 4, 4]
        assert distribute_performers_to_pools(12, 3) == [4, 4, 4]

    def test_uneven_distribution_two_pools(self):
        """Test uneven distribution with 2 pools."""
        # 9 performers, 2 pools → [5, 4]
        assert distribute_performers_to_pools(9, 2) == [5, 4]

        # 7 performers, 2 pools → [4, 3]
        assert distribute_performers_to_pools(7, 2) == [4, 3]

    def test_uneven_distribution_three_pools(self):
        """Test uneven distribution with 3 pools."""
        # 10 performers, 3 pools → [4, 3, 3]
        assert distribute_performers_to_pools(10, 3) == [4, 3, 3]

        # 11 performers, 3 pools → [4, 4, 3]
        assert distribute_performers_to_pools(11, 3) == [4, 4, 3]

    def test_minimum_two_per_pool(self):
        """Test that each pool has at least 2 performers."""
        # 6 performers, 2 pools → [3, 3]
        result = distribute_performers_to_pools(6, 2)
        assert all(size >= 2 for size in result)

        # 6 performers, 3 pools → [2, 2, 2]
        result = distribute_performers_to_pools(6, 3)
        assert all(size >= 2 for size in result)

    def test_pool_sizes_differ_by_max_one(self):
        """Test that pool sizes differ by at most 1."""
        # Various cases
        for performers in range(6, 20):
            for pools in range(1, 5):
                if performers >= pools * 2:  # Valid configuration
                    result = distribute_performers_to_pools(performers, pools)
                    assert max(result) - min(result) <= 1

    def test_total_performers_matches(self):
        """Test that sum of pool sizes equals total performers."""
        assert sum(distribute_performers_to_pools(8, 2)) == 8
        assert sum(distribute_performers_to_pools(10, 3)) == 10
        assert sum(distribute_performers_to_pools(15, 4)) == 15

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
            _, eliminated = calculate_pool_capacity(registered, groups)
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
            pool_performers, _ = calculate_pool_capacity(registered, groups)
            assert registered > pool_performers, (
                f"Registered ({registered}) must be > pool_performers ({pool_performers}) "
                "to ensure preselection is mandatory"
            )
