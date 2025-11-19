"""Pydantic schemas for Category entity."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_validator

from app.utils.tournament_calculations import calculate_minimum_performers


class CreateCategorySchema(BaseModel):
    """Schema for creating a category."""

    tournament_id: UUID = Field(..., description="Tournament UUID")
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    is_duo: bool = Field(default=False, description="2v2 category (default: False)")
    groups_ideal: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of pools (FIXED, default: 2)",
    )
    performers_ideal: int = Field(
        default=4,
        ge=2,
        le=20,
        description="Target performers per pool (ADAPTIVE, default: 4)",
    )

    @field_validator("groups_ideal")
    @classmethod
    def validate_groups_ideal(cls, v: int) -> int:
        """Ensure groups_ideal is reasonable."""
        if v < 1:
            raise ValueError("Must have at least 1 pool")
        if v > 10:
            raise ValueError("Maximum 10 pools supported")
        return v

    @field_validator("performers_ideal")
    @classmethod
    def validate_performers_ideal(cls, v: int) -> int:
        """Ensure performers_ideal is reasonable."""
        if v < 2:
            raise ValueError("Must have at least 2 performers per pool")
        if v > 20:
            raise ValueError("Maximum 20 performers per pool")
        return v

    @computed_field
    @property
    def minimum_performers_required(self) -> int:
        """Calculate minimum performers based on business rules.

        Formula: (groups_ideal * 2) + 2

        This is derived from:
        - groups_ideal * 2: minimum pool performers (2 per pool)
        - + 2: minimum elimination requirement
        """
        return calculate_minimum_performers(self.groups_ideal)

    @computed_field
    @property
    def ideal_pool_capacity(self) -> int:
        """Calculate ideal total pool capacity.

        This is the target, not the minimum.
        """
        return self.groups_ideal * self.performers_ideal

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "tournament_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Breaking 1v1",
                "is_duo": False,
                "groups_ideal": 2,
                "performers_ideal": 4,
            }
        }


class UpdateCategorySchema(BaseModel):
    """Schema for updating a category."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_duo: Optional[bool] = None
    groups_ideal: Optional[int] = Field(None, ge=1, le=10)
    performers_ideal: Optional[int] = Field(None, ge=2, le=20)

    @field_validator("groups_ideal")
    @classmethod
    def validate_groups_ideal(cls, v: Optional[int]) -> Optional[int]:
        """Ensure groups_ideal is reasonable if provided."""
        if v is None:
            return v
        if v < 1:
            raise ValueError("Must have at least 1 pool")
        if v > 10:
            raise ValueError("Maximum 10 pools supported")
        return v

    @field_validator("performers_ideal")
    @classmethod
    def validate_performers_ideal(cls, v: Optional[int]) -> Optional[int]:
        """Ensure performers_ideal is reasonable if provided."""
        if v is None:
            return v
        if v < 2:
            raise ValueError("Must have at least 2 performers per pool")
        if v > 20:
            raise ValueError("Maximum 20 performers per pool")
        return v
