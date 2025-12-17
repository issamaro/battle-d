"""Performer service for registration business operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.exceptions import ValidationError
from app.models.performer import Performer
from app.models.tournament import TournamentPhase
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository
from app.repositories.tournament import TournamentRepository


class PerformerService:
    """Service for performer registration operations.

    Handles performer registration with duo pairing support and validation.
    Also handles guest performer registration per BR-GUEST-* rules.
    """

    def __init__(
        self,
        performer_repo: PerformerRepository,
        category_repo: CategoryRepository,
        dancer_repo: DancerRepository,
        tournament_repo: Optional[TournamentRepository] = None,
    ):
        """Initialize performer service.

        Args:
            performer_repo: Performer repository
            category_repo: Category repository
            dancer_repo: Dancer repository
            tournament_repo: Tournament repository (optional, required for guest operations)
        """
        self.performer_repo = performer_repo
        self.category_repo = category_repo
        self.dancer_repo = dancer_repo
        self.tournament_repo = tournament_repo

    async def register_performer(
        self,
        tournament_id: UUID,
        category_id: UUID,
        dancer_id: UUID,
        duo_partner_id: Optional[UUID] = None,
    ) -> Performer:
        """Register performer with duo pairing support.

        Args:
            tournament_id: Tournament UUID
            category_id: Category UUID
            dancer_id: Dancer UUID
            duo_partner_id: Duo partner dancer UUID (optional, required for 2v2)

        Returns:
            Created performer

        Raises:
            ValidationError: If validation fails
        """
        # Validate category exists
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise ValidationError(["Category not found"])

        # Validate category belongs to tournament
        if category.tournament_id != tournament_id:
            raise ValidationError(["Category does not belong to this tournament"])

        # Validate duo/solo match
        if duo_partner_id and not category.is_duo:
            raise ValidationError(
                [
                    f"Cannot register duo in solo category '{category.name}'. "
                    "This is a 1v1 category."
                ]
            )
        if not duo_partner_id and category.is_duo:
            raise ValidationError(
                [
                    f"Category '{category.name}' is 2v2. "
                    "Must provide duo partner to register."
                ]
            )

        # Validate dancer exists
        dancer = await self.dancer_repo.get_by_id(dancer_id)
        if not dancer:
            raise ValidationError(["Dancer not found"])

        # Check dancer not already registered in this tournament
        if await self.performer_repo.dancer_registered_in_tournament(
            dancer_id, tournament_id
        ):
            raise ValidationError(
                [f"Dancer '{dancer.full_name}' is already registered in this tournament"]
            )

        # Validate duo partner if provided
        if duo_partner_id:
            # Check partner exists
            partner = await self.dancer_repo.get_by_id(duo_partner_id)
            if not partner:
                raise ValidationError(["Duo partner not found"])

            # Check partner not already registered
            if await self.performer_repo.dancer_registered_in_tournament(
                duo_partner_id, tournament_id
            ):
                raise ValidationError(
                    [
                        f"Duo partner '{partner.full_name}' is already registered "
                        "in this tournament"
                    ]
                )

            # Check not registering with self
            if dancer_id == duo_partner_id:
                raise ValidationError(["Cannot register dancer as their own duo partner"])

        # Create performer
        try:
            performer = await self.performer_repo.create_performer(
                tournament_id=tournament_id,
                category_id=category_id,
                dancer_id=dancer_id,
                duo_partner_id=duo_partner_id,
            )
        except IntegrityError as e:
            # Handle unique constraint violations (race conditions)
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)

            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                raise ValidationError([
                    f"Dancer '{dancer.full_name}' is already registered in this tournament. "
                    "This may have occurred due to a concurrent registration."
                ])
            else:
                # Re-raise other integrity errors
                raise ValidationError(["Database integrity error during registration"])

        return performer

    async def unregister_performer(self, performer_id: UUID) -> bool:
        """Unregister performer from tournament.

        Args:
            performer_id: Performer UUID

        Returns:
            True if unregistered successfully

        Raises:
            ValidationError: If performer not found
        """
        # Check performer exists
        performer = await self.performer_repo.get_by_id(performer_id)
        if not performer:
            raise ValidationError(["Performer not found"])

        # Delete performer
        success = await self.performer_repo.delete(performer_id)
        if not success:
            raise ValidationError(["Failed to unregister performer"])

        return True

    async def get_performers_by_category(self, category_id: UUID) -> list[Performer]:
        """Get all performers registered in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of performers with dancer info
        """
        return await self.performer_repo.get_by_category(category_id)

    async def get_performers_by_tournament(self, tournament_id: UUID) -> list[Performer]:
        """Get all performers registered in a tournament.

        Args:
            tournament_id: Tournament UUID

        Returns:
            List of performers
        """
        return await self.performer_repo.get_by_tournament(tournament_id)

    # ========== Guest Performer Methods (BR-GUEST-*) ==========

    async def register_guest_performer(
        self,
        tournament_id: UUID,
        category_id: UUID,
        dancer_id: UUID,
    ) -> Performer:
        """Register a guest performer with automatic top score.

        Implements BR-GUEST-001 (timing), BR-GUEST-002 (score assignment).

        Guest performers:
        - Skip preselection battles
        - Receive automatic 10.0 preselection score
        - Are guaranteed to qualify for pools
        - Can only be registered during Registration phase

        Args:
            tournament_id: Tournament UUID
            category_id: Category UUID
            dancer_id: Dancer UUID

        Returns:
            Created guest performer with preselection_score=10.0

        Raises:
            ValidationError: If validation fails
        """
        # BR-GUEST-001: Validate tournament is in Registration phase
        if self.tournament_repo is None:
            raise ValidationError(["Tournament repository not configured for guest operations"])

        tournament = await self.tournament_repo.get_by_id(tournament_id)
        if not tournament:
            raise ValidationError(["Tournament not found"])

        if tournament.phase != TournamentPhase.REGISTRATION:
            raise ValidationError([
                "Guests can only be added during Registration phase. "
                f"Tournament is currently in {tournament.phase.value} phase."
            ])

        # Validate category exists and belongs to tournament
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise ValidationError(["Category not found"])

        if category.tournament_id != tournament_id:
            raise ValidationError(["Category does not belong to this tournament"])

        # Guests cannot be registered in duo categories
        if category.is_duo:
            raise ValidationError([
                f"Category '{category.name}' is 2v2. "
                "Guests cannot be registered in duo categories."
            ])

        # Validate dancer exists
        dancer = await self.dancer_repo.get_by_id(dancer_id)
        if not dancer:
            raise ValidationError(["Dancer not found"])

        # Check dancer not already registered in this tournament
        if await self.performer_repo.dancer_registered_in_tournament(
            dancer_id, tournament_id
        ):
            raise ValidationError(
                [f"Dancer '{dancer.full_name}' is already registered in this tournament"]
            )

        # BR-GUEST-002: Create guest performer with automatic 10.0 score
        try:
            performer = await self.performer_repo.create_guest_performer(
                tournament_id=tournament_id,
                category_id=category_id,
                dancer_id=dancer_id,
            )
        except IntegrityError as e:
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)

            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                raise ValidationError([
                    f"Dancer '{dancer.full_name}' is already registered in this tournament. "
                    "This may have occurred due to a concurrent registration."
                ])
            else:
                raise ValidationError(["Database integrity error during guest registration"])

        return performer

    async def convert_to_guest(
        self,
        performer_id: UUID,
    ) -> Performer:
        """Convert a regular performer to guest.

        Implements BR-GUEST-001 (timing), BR-GUEST-002 (score assignment).

        Args:
            performer_id: Performer UUID to convert

        Returns:
            Updated performer with is_guest=True and preselection_score=10.0

        Raises:
            ValidationError: If validation fails
        """
        # Get performer with category and tournament info
        performer = await self.performer_repo.get_with_dancer(performer_id)
        if not performer:
            raise ValidationError(["Performer not found"])

        # Already a guest?
        if performer.is_guest:
            raise ValidationError(["Performer is already a guest"])

        # BR-GUEST-001: Validate tournament is in Registration phase
        if self.tournament_repo is None:
            raise ValidationError(["Tournament repository not configured for guest operations"])

        tournament = await self.tournament_repo.get_by_id(performer.tournament_id)
        if not tournament:
            raise ValidationError(["Tournament not found"])

        if tournament.phase != TournamentPhase.REGISTRATION:
            raise ValidationError([
                "Guests can only be designated during Registration phase. "
                f"Tournament is currently in {tournament.phase.value} phase."
            ])

        # Get category to check if duo
        category = await self.category_repo.get_by_id(performer.category_id)
        if category and category.is_duo:
            raise ValidationError([
                f"Cannot convert to guest in duo category '{category.name}'"
            ])

        # Convert to guest
        return await self.performer_repo.convert_to_guest(performer_id)

    async def get_guest_count(self, category_id: UUID) -> int:
        """Get count of guest performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            Number of guest performers
        """
        return await self.performer_repo.get_guest_count(category_id)

    async def get_regular_performers(self, category_id: UUID) -> list[Performer]:
        """Get non-guest performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of regular (non-guest) performers
        """
        return await self.performer_repo.get_regular_performers(category_id)

    async def get_guests(self, category_id: UUID) -> list[Performer]:
        """Get guest performers in a category.

        Args:
            category_id: Category UUID

        Returns:
            List of guest performers
        """
        return await self.performer_repo.get_guests(category_id)
