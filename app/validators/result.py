"""Validation result data structures."""

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        valid: Whether validation passed
        errors: List of error messages (blocking issues)
        warnings: List of warning messages (non-blocking)

    Examples:
        >>> result = ValidationResult.success()
        >>> if result:
        ...     print("Valid!")

        >>> result = ValidationResult.failure(["Error 1", "Error 2"])
        >>> if not result:
        ...     print(result.errors)
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Allow truthiness checks: if result: ..."""
        return self.valid

    @classmethod
    def success(cls, warnings: list[str] = None) -> "ValidationResult":
        """Create a successful validation result.

        Args:
            warnings: Optional list of warning messages

        Returns:
            ValidationResult with valid=True
        """
        return cls(valid=True, warnings=warnings or [])

    @classmethod
    def failure(
        cls, errors: list[str], warnings: list[str] = None
    ) -> "ValidationResult":
        """Create a failed validation result.

        Args:
            errors: List of error messages
            warnings: Optional list of warning messages

        Returns:
            ValidationResult with valid=False
        """
        return cls(valid=False, errors=errors, warnings=warnings or [])
