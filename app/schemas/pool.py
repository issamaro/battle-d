"""Pydantic schemas for Pool entity."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class PoolCreate(BaseModel):
    """Schema for creating a pool."""

    category_id: UUID = Field(..., description="Category UUID")
    name: str = Field(..., min_length=1, max_length=100, description="Pool name")
    performer_ids: List[UUID] = Field(
        ..., min_length=2, description="List of performer UUIDs (min 2)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "category_id": "223e4567-e89b-12d3-a456-426614174000",
                "name": "Pool A",
                "performer_ids": [
                    "323e4567-e89b-12d3-a456-426614174000",
                    "423e4567-e89b-12d3-a456-426614174000",
                    "523e4567-e89b-12d3-a456-426614174000",
                ],
            }
        }


class PoolUpdate(BaseModel):
    """Schema for updating a pool."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Pool name")
    winner_id: Optional[UUID] = Field(None, description="Winner performer UUID")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "winner_id": "323e4567-e89b-12d3-a456-426614174000",
            }
        }


class PoolResponse(BaseModel):
    """Schema for pool response."""

    id: UUID
    category_id: UUID
    name: str
    winner_id: Optional[UUID]
    performer_count: int
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "623e4567-e89b-12d3-a456-426614174000",
                "category_id": "223e4567-e89b-12d3-a456-426614174000",
                "name": "Pool A",
                "winner_id": "323e4567-e89b-12d3-a456-426614174000",
                "performer_count": 3,
                "created_at": "2024-01-15T10:30:00Z",
            }
        }


class PoolDetailResponse(PoolResponse):
    """Schema for detailed pool response with performers."""

    performer_ids: List[UUID]

    class Config:
        """Pydantic config."""

        from_attributes = True


class PoolCreateFromPreselection(BaseModel):
    """Schema for creating pools from preselection results."""

    category_id: UUID = Field(..., description="Category UUID")
    groups_ideal: int = Field(
        ..., ge=2, le=4, description="Ideal number of pools (2-4)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "category_id": "223e4567-e89b-12d3-a456-426614174000",
                "groups_ideal": 2,
            }
        }


class PoolWinnerSet(BaseModel):
    """Schema for setting pool winner."""

    winner_id: UUID = Field(..., description="Winner performer UUID")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "winner_id": "323e4567-e89b-12d3-a456-426614174000",
            }
        }
