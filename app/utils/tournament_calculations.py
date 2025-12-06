"""Pure calculation functions for tournament business rules.

These functions implement the core domain logic for calculating
minimum performers, pool structures, and distribution strategies.
All calculations are derived from business rules, not hardcoded constants.
"""


def calculate_minimum_performers(groups_ideal: int) -> int:
    """Calculate minimum performers needed to start tournament.

    Formula: (groups_ideal * 2) + 1

    This ensures:
    - Preselection is always mandatory (registered_performers > pool_performers)
    - At least 2 performers per pool after preselection
    - At least 1 performer eliminated in preselection

    Args:
        groups_ideal: Target number of pools (must be >= 1)

    Returns:
        Minimum number of registered performers required

    Raises:
        ValueError: If groups_ideal < 1

    Examples:
        >>> calculate_minimum_performers(2)
        5  # 2 pools * 2 performers + 1 eliminated = 5 minimum

        >>> calculate_minimum_performers(3)
        7  # 3 pools * 2 performers + 1 eliminated = 7 minimum

        >>> calculate_minimum_performers(4)
        9  # 4 pools * 2 performers + 1 eliminated = 9 minimum
    """
    if groups_ideal < 1:
        raise ValueError("groups_ideal must be at least 1")

    return (groups_ideal * 2) + 1


def calculate_pool_capacity(
    registered_performers: int,
    groups_ideal: int,
    performers_ideal: int = 4,
) -> tuple[int, int, int]:
    """Calculate pool structure ensuring EQUAL pool sizes (BR-POOL-001).

    Business Rule BR-POOL-001: All pools must have EQUAL sizes.
    Pool capacity is calculated as groups_ideal × performers_per_pool
    where performers_per_pool is adaptive but EQUAL across all pools.

    Strategy:
    1. If registered >= ideal_capacity + 1: use ideal capacity
    2. Otherwise: reduce pool size until capacity < registered
    3. This ensures at least 1 performer is eliminated (preselection mandatory)

    Args:
        registered_performers: Number of registered performers
        groups_ideal: Target number of pools (FIXED)
        performers_ideal: Target performers per pool (ADAPTIVE DOWN)

    Returns:
        Tuple of (pool_capacity, performers_per_pool, eliminated_count)
        - pool_capacity: Total performers qualifying for pools
        - performers_per_pool: Size of each pool (EQUAL)
        - eliminated_count: Performers eliminated in preselection

    Raises:
        ValueError: If registered_performers < minimum required

    Examples:
        >>> calculate_pool_capacity(9, 2, 4)
        (8, 4, 1)  # 9 registered, 8 capacity (2×4), 1 eliminated

        >>> calculate_pool_capacity(8, 2, 4)
        (6, 3, 2)  # 8 registered = ideal, must reduce to 2×3=6 to ensure elimination

        >>> calculate_pool_capacity(7, 2, 4)
        (6, 3, 1)  # 7 registered, 6 capacity (2×3), 1 eliminated

        >>> calculate_pool_capacity(12, 2, 4)
        (8, 4, 4)  # 12 registered, 8 capacity (2×4), 4 eliminated

        >>> calculate_pool_capacity(5, 2, 4)
        (4, 2, 1)  # Minimum case: 5 registered, 4 capacity (2×2), 1 eliminated
    """
    min_required = calculate_minimum_performers(groups_ideal)
    if registered_performers < min_required:
        raise ValueError(
            f"Need at least {min_required} performers for {groups_ideal} pools, "
            f"got {registered_performers}"
        )

    ideal_capacity = groups_ideal * performers_ideal

    # Case 1: More performers than ideal + 1 → use ideal capacity
    if registered_performers >= ideal_capacity + 1:
        eliminated = registered_performers - ideal_capacity
        return ideal_capacity, performers_ideal, eliminated

    # Case 2: Need to reduce pool size to ensure elimination
    # Find largest performers_per_pool where (groups × pool_size) < registered
    for pool_size in range(performers_ideal, 1, -1):  # Start from ideal, go down to 2
        capacity = groups_ideal * pool_size
        if capacity < registered_performers:
            eliminated = registered_performers - capacity
            return capacity, pool_size, eliminated

    # Fallback: minimum 2 per pool
    capacity = groups_ideal * 2
    eliminated = registered_performers - capacity
    return capacity, 2, eliminated


def distribute_performers_to_pools(
    pool_capacity: int,
    groups_ideal: int,
) -> list[int]:
    """Distribute performers EQUALLY across pools (BR-POOL-001).

    Business Rule BR-POOL-001: All pools must have EQUAL sizes.
    This function enforces that pool_capacity is evenly divisible by groups_ideal.

    Args:
        pool_capacity: Total performers to distribute (must be divisible by groups_ideal)
        groups_ideal: Number of pools

    Returns:
        List of equal pool sizes (length = groups_ideal)

    Raises:
        ValueError: If pool_capacity is not evenly divisible by groups_ideal
        ValueError: If pool_capacity < groups_ideal * 2 (minimum 2 per pool)

    Examples:
        >>> distribute_performers_to_pools(8, 2)
        [4, 4]  # 8 / 2 = 4 per pool

        >>> distribute_performers_to_pools(6, 2)
        [3, 3]  # 6 / 2 = 3 per pool

        >>> distribute_performers_to_pools(12, 3)
        [4, 4, 4]  # 12 / 3 = 4 per pool

        >>> distribute_performers_to_pools(9, 3)
        [3, 3, 3]  # 9 / 3 = 3 per pool

        >>> distribute_performers_to_pools(9, 2)
        ValueError  # 9 not divisible by 2 - violates BR-POOL-001
    """
    if pool_capacity < groups_ideal * 2:
        raise ValueError(
            f"Need at least {groups_ideal * 2} performers for {groups_ideal} pools "
            f"(minimum 2 per pool), got {pool_capacity}"
        )

    if pool_capacity % groups_ideal != 0:
        raise ValueError(
            f"Pool capacity {pool_capacity} must be evenly divisible by {groups_ideal} pools "
            f"(BR-POOL-001: Equal Pool Sizes). Use calculate_pool_capacity() to get valid capacity."
        )

    pool_size = pool_capacity // groups_ideal
    return [pool_size] * groups_ideal


def calculate_minimum_for_category(
    groups_ideal: int, performers_ideal: int
) -> dict[str, int]:
    """Calculate all relevant metrics for a category configuration.

    Provides a complete picture of what a category configuration means
    in terms of minimum requirements and ideal capacity.

    Args:
        groups_ideal: Target number of pools (FIXED)
        performers_ideal: Target performers per pool (ADAPTIVE)

    Returns:
        Dictionary containing:
        - minimum_required: Minimum performers to start tournament
        - ideal_capacity: Ideal total pool capacity (groups * performers)
        - min_pool_performers: Minimum total in pools (groups * 2)
        - min_eliminated: Minimum eliminated in preselection (always 1)

    Examples:
        >>> calculate_minimum_for_category(2, 4)
        {
            'minimum_required': 5,
            'ideal_capacity': 8,
            'min_pool_performers': 4,
            'min_eliminated': 1
        }

        >>> calculate_minimum_for_category(3, 6)
        {
            'minimum_required': 7,
            'ideal_capacity': 18,
            'min_pool_performers': 6,
            'min_eliminated': 1
        }
    """
    minimum_required = calculate_minimum_performers(groups_ideal)
    ideal_capacity = groups_ideal * performers_ideal
    min_pool_performers = groups_ideal * 2
    min_eliminated = 1

    return {
        "minimum_required": minimum_required,
        "ideal_capacity": ideal_capacity,
        "min_pool_performers": min_pool_performers,
        "min_eliminated": min_eliminated,
    }
