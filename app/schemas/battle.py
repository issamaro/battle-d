"""Pydantic schemas for Battle entity."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.battle import BattlePhase, BattleStatus, BattleOutcomeType


class BattleCreate(BaseModel):
    """Schema for creating a battle."""

    category_id: UUID = Field(..., description="Category UUID")
    phase: BattlePhase = Field(..., description="Battle phase")
    outcome_type: BattleOutcomeType = Field(..., description="Outcome type")
    performer_ids: List[UUID] = Field(
        ..., min_length=2, description="List of performer UUIDs (min 2)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "category_id": "223e4567-e89b-12d3-a456-426614174000",
                "phase": "preselection",
                "outcome_type": "scored",
                "performer_ids": [
                    "323e4567-e89b-12d3-a456-426614174000",
                    "423e4567-e89b-12d3-a456-426614174000",
                ],
            }
        }


class BattleUpdate(BaseModel):
    """Schema for updating a battle."""

    status: Optional[BattleStatus] = Field(None, description="Battle status")
    winner_id: Optional[UUID] = Field(None, description="Winner performer UUID")
    outcome: Optional[Dict[str, Any]] = Field(None, description="Battle outcome data")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "status": "completed",
                "outcome": {
                    "323e4567-e89b-12d3-a456-426614174000": 8.5,
                    "423e4567-e89b-12d3-a456-426614174000": 7.2,
                },
            }
        }


class BattleScoredOutcome(BaseModel):
    """Schema for scored outcome (preselection)."""

    scores: Dict[UUID, float] = Field(
        ..., description="Performer ID to score mapping (0-10)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "scores": {
                    "323e4567-e89b-12d3-a456-426614174000": 8.5,
                    "423e4567-e89b-12d3-a456-426614174000": 7.2,
                }
            }
        }


class BattleWinDrawLossOutcome(BaseModel):
    """Schema for win/draw/loss outcome (pools)."""

    winner_id: Optional[UUID] = Field(None, description="Winner UUID (None if draw)")
    is_draw: bool = Field(False, description="Whether battle was a draw")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {"winner_id": "323e4567-e89b-12d3-a456-426614174000", "is_draw": False}
        }


class BattleTiebreakOutcome(BaseModel):
    """Schema for tiebreak outcome."""

    judge_votes: Dict[str, UUID] = Field(..., description="Judge ID to performer ID votes")
    winner_ids: List[UUID] = Field(..., description="List of winner performer UUIDs")
    n_participants: int = Field(..., description="Number of tied participants")
    p_winners_needed: int = Field(..., description="Number of winners needed")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "judge_votes": {
                    "judge1_round1": "323e4567-e89b-12d3-a456-426614174000",
                    "judge2_round1": "323e4567-e89b-12d3-a456-426614174000",
                },
                "winner_ids": ["323e4567-e89b-12d3-a456-426614174000"],
                "n_participants": 2,
                "p_winners_needed": 1,
            }
        }


class BattleWinLossOutcome(BaseModel):
    """Schema for win/loss outcome (finals)."""

    winner_id: UUID = Field(..., description="Winner performer UUID")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {"winner_id": "323e4567-e89b-12d3-a456-426614174000"}
        }


class BattleResponse(BaseModel):
    """Schema for battle response."""

    id: UUID
    category_id: UUID
    phase: BattlePhase
    status: BattleStatus
    outcome_type: BattleOutcomeType
    winner_id: Optional[UUID]
    outcome: Optional[Dict[str, Any]]
    performer_count: int
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "523e4567-e89b-12d3-a456-426614174000",
                "category_id": "223e4567-e89b-12d3-a456-426614174000",
                "phase": "preselection",
                "status": "completed",
                "outcome_type": "scored",
                "winner_id": None,
                "outcome": {
                    "323e4567-e89b-12d3-a456-426614174000": 8.5,
                    "423e4567-e89b-12d3-a456-426614174000": 7.2,
                },
                "performer_count": 2,
                "created_at": "2024-01-15T10:30:00Z",
            }
        }


class BattleDetailResponse(BattleResponse):
    """Schema for detailed battle response with performers."""

    performer_ids: List[UUID]

    class Config:
        """Pydantic config."""

        from_attributes = True
