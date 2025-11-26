"""Pydantic schemas for request/response validation."""

from app.schemas.battle import (
    BattleCreate,
    BattleUpdate,
    BattleScoredOutcome,
    BattleWinDrawLossOutcome,
    BattleTiebreakOutcome,
    BattleWinLossOutcome,
    BattleResponse,
    BattleDetailResponse,
)
from app.schemas.pool import (
    PoolCreate,
    PoolUpdate,
    PoolResponse,
    PoolDetailResponse,
    PoolCreateFromPreselection,
    PoolWinnerSet,
)

__all__ = [
    # Battle schemas
    "BattleCreate",
    "BattleUpdate",
    "BattleScoredOutcome",
    "BattleWinDrawLossOutcome",
    "BattleTiebreakOutcome",
    "BattleWinLossOutcome",
    "BattleResponse",
    "BattleDetailResponse",
    # Pool schemas
    "PoolCreate",
    "PoolUpdate",
    "PoolResponse",
    "PoolDetailResponse",
    "PoolCreateFromPreselection",
    "PoolWinnerSet",
]
