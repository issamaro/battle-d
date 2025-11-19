"""Pydantic schemas for Tournament entity."""

from typing import Optional

from pydantic import BaseModel, Field


class CreateTournamentSchema(BaseModel):
    """Schema for creating a tournament."""

    name: str = Field(..., min_length=2, max_length=200, description="Tournament name")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "Battle-D 2024",
            }
        }


class UpdateTournamentSchema(BaseModel):
    """Schema for updating a tournament."""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
