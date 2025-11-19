"""Pydantic schemas for Performer entity."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RegisterPerformerSchema(BaseModel):
    """Schema for registering a performer."""

    tournament_id: UUID = Field(..., description="Tournament UUID")
    category_id: UUID = Field(..., description="Category UUID")
    dancer_id: UUID = Field(..., description="Dancer UUID")
    duo_partner_id: Optional[UUID] = Field(
        None, description="Duo partner UUID (required for 2v2 categories)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "tournament_id": "123e4567-e89b-12d3-a456-426614174000",
                "category_id": "223e4567-e89b-12d3-a456-426614174000",
                "dancer_id": "323e4567-e89b-12d3-a456-426614174000",
                "duo_partner_id": None,
            }
        }
