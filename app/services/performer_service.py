"""Performer service for registration business operations."""

from typing import Optional
from uuid import UUID

from app.exceptions import ValidationError
from app.models.performer import Performer
from app.repositories.category import CategoryRepository
from app.repositories.dancer import DancerRepository
from app.repositories.performer import PerformerRepository


class PerformerService:
    """Service for performer registration operations.

    Handles performer registration with duo pairing support and validation.
    """

    def __init__(
        self,
        performer_repo: PerformerRepository,
        category_repo: CategoryRepository,
        dancer_repo: DancerRepository,
    ):
        """Initialize performer service.

        Args:
            performer_repo: Performer repository
            category_repo: Category repository
            dancer_repo: Dancer repository
        """
        self.performer_repo = performer_repo
        self.category_repo = category_repo
        self.dancer_repo = dancer_repo

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
        performer = await self.performer_repo.create_performer(
            tournament_id=tournament_id,
            category_id=category_id,
            dancer_id=dancer_id,
            duo_partner_id=duo_partner_id,
        )

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
