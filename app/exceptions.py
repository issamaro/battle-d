"""Custom exceptions for the application."""


class ValidationError(Exception):
    """Raised when business rule validation fails.

    This is different from Pydantic's ValidationError which is for
    request/response validation. This exception is for domain-specific
    business rules.

    Attributes:
        errors: List of error messages (blocking issues)
        warnings: List of warning messages (non-blocking)

    Examples:
        >>> raise ValidationError(["Insufficient performers"])
        >>> raise ValidationError(
        ...     errors=["Battle not found"],
        ...     warnings=["Scores are low"]
        ... )
    """

    def __init__(self, errors: list[str], warnings: list[str] = None):
        self.errors = errors
        self.warnings = warnings or []
        super().__init__("; ".join(errors))
