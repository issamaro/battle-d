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
) -> tuple[int, int]:
    """Calculate pool structure ensuring preselection eliminates performers.

    Strategy:
    - Eliminate performers to reach pool capacity
    - Ensure at least 1 eliminated (preselection mandatory)
    - Ensure at least 2 per pool after elimination

    Args:
        registered_performers: Number of registered performers
        groups_ideal: Target number of pools

    Returns:
        Tuple of (pool_performers, eliminated_count)
        - pool_performers: Total performers qualifying for pools
        - eliminated_count: Performers eliminated in preselection

    Raises:
        ValueError: If registered_performers < minimum required

    Examples:
        >>> calculate_pool_capacity(7, 2)
        (6, 1)  # Eliminate 1, create 2 pools of 3 each

        >>> calculate_pool_capacity(9, 2)
        (8, 1)  # Eliminate 1, create 2 pools of 4 each

        >>> calculate_pool_capacity(20, 2)
        (16, 4)  # Eliminate 4, create 2 pools of 8 each

        >>> calculate_pool_capacity(5, 2)
        (4, 1)  # Minimum case: eliminate 1, create 2 pools of 2 each
    """
    min_required = calculate_minimum_performers(groups_ideal)
    if registered_performers < min_required:
        raise ValueError(
            f"Need at least {min_required} performers for {groups_ideal} pools, "
            f"got {registered_performers}"
        )

    # Calculate elimination target (dynamic based on registrations, minimum 1)
    elimination_target = max(1, int(registered_performers * 0.25))
    pool_performers = registered_performers - elimination_target

    # Ensure minimum 2 per pool
    min_pool_performers = groups_ideal * 2
    if pool_performers < min_pool_performers:
        pool_performers = min_pool_performers

    eliminated = registered_performers - pool_performers
    return pool_performers, eliminated


def distribute_performers_to_pools(
    performer_count: int,
    groups_ideal: int,
) -> list[int]:
    """Calculate even distribution of performers across pools.

    Strategy:
    - Distribute as evenly as possible
    - Pool sizes differ by at most 1
    - Larger pools come first

    Args:
        performer_count: Number of performers to distribute
        groups_ideal: Number of pools

    Returns:
        List of pool sizes (length = groups_ideal)

    Raises:
        ValueError: If performer_count < groups_ideal * 2 (minimum 2 per pool)

    Examples:
        >>> distribute_performers_to_pools(8, 2)
        [4, 4]  # Even distribution

        >>> distribute_performers_to_pools(9, 2)
        [5, 4]  # 5 in first pool, 4 in second

        >>> distribute_performers_to_pools(10, 3)
        [4, 3, 3]  # 4 in first, 3 in others

        >>> distribute_performers_to_pools(11, 3)
        [4, 4, 3]  # Two pools get 4, one gets 3
    """
    if performer_count < groups_ideal * 2:
        raise ValueError(
            f"Need at least {groups_ideal * 2} performers for {groups_ideal} pools "
            f"(minimum 2 per pool), got {performer_count}"
        )

    base_size = performer_count // groups_ideal
    remainder = performer_count % groups_ideal

    # First 'remainder' pools get one extra performer
    pool_sizes = []
    for i in range(groups_ideal):
        size = base_size + (1 if i < remainder else 0)
        pool_sizes.append(size)

    return pool_sizes


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
