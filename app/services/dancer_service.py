"""Dancer service for business operations."""

from datetime import date
from typing import Optional
from uuid import UUID

from app.exceptions import ValidationError
from app.models.dancer import Dancer
from app.repositories.dancer import DancerRepository


class DancerService:
    """Service for dancer business operations.

    Handles dancer CRUD with validation and business rules.
    """

    def __init__(self, dancer_repo: DancerRepository):
        """Initialize dancer service.

        Args:
            dancer_repo: Dancer repository
        """
        self.dancer_repo = dancer_repo

    async def create_dancer(
        self,
        email: str,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        blaze: str,
        country: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dancer:
        """Create dancer with validation.

        Args:
            email: Dancer email (must be unique)
            first_name: First name
            last_name: Last name
            date_of_birth: Date of birth
            blaze: Stage name
            country: Country (optional)
            city: City (optional)

        Returns:
            Created dancer

        Raises:
            ValidationError: If validation fails
        """
        # Email uniqueness validation
        email_lower = email.lower()
        if await self.dancer_repo.email_exists(email_lower):
            raise ValidationError([f"Email '{email}' is already registered"])

        # Age validation (10-100 years)
        age = (date.today() - date_of_birth).days // 365
        if age < 10:
            raise ValidationError(["Dancer must be at least 10 years old"])
        if age > 100:
            raise ValidationError(["Invalid birth date (age exceeds 100 years)"])

        # Create dancer
        dancer = await self.dancer_repo.create_dancer(
            email=email_lower,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            blaze=blaze,
            country=country,
            city=city,
        )

        return dancer

    async def update_dancer(
        self,
        dancer_id: UUID,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        blaze: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dancer:
        """Update dancer with validation.

        Args:
            dancer_id: Dancer UUID
            email: New email (optional)
            first_name: New first name (optional)
            last_name: New last name (optional)
            date_of_birth: New date of birth (optional)
            blaze: New stage name (optional)
            country: New country (optional)
            city: New city (optional)

        Returns:
            Updated dancer

        Raises:
            ValidationError: If validation fails
        """
        # Check dancer exists
        dancer = await self.dancer_repo.get_by_id(dancer_id)
        if not dancer:
            raise ValidationError(["Dancer not found"])

        # Email uniqueness validation if email changed
        if email and email.lower() != dancer.email:
            if await self.dancer_repo.email_exists(email.lower()):
                raise ValidationError([f"Email '{email}' is already registered"])

        # Age validation if date of birth changed
        if date_of_birth and date_of_birth != dancer.date_of_birth:
            age = (date.today() - date_of_birth).days // 365
            if age < 10:
                raise ValidationError(["Dancer must be at least 10 years old"])
            if age > 100:
                raise ValidationError(["Invalid birth date (age exceeds 100 years)"])

        # Build update dict (only include provided fields)
        update_data = {}
        if email is not None:
            update_data["email"] = email.lower()
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if date_of_birth is not None:
            update_data["date_of_birth"] = date_of_birth
        if blaze is not None:
            update_data["blaze"] = blaze
        if country is not None:
            update_data["country"] = country
        if city is not None:
            update_data["city"] = city

        # Update dancer
        updated_dancer = await self.dancer_repo.update(dancer_id, **update_data)
        return updated_dancer

    async def search_dancers(self, query: str) -> list[Dancer]:
        """Search dancers by name, blaze, or email.

        Args:
            query: Search query string

        Returns:
            List of matching dancers
        """
        if not query or not query.strip():
            return await self.dancer_repo.get_all()

        return await self.dancer_repo.search(query.strip())

    async def get_dancer_by_id(self, dancer_id: UUID) -> Dancer:
        """Get dancer by ID.

        Args:
            dancer_id: Dancer UUID

        Returns:
            Dancer instance

        Raises:
            ValidationError: If dancer not found
        """
        dancer = await self.dancer_repo.get_by_id(dancer_id)
        if not dancer:
            raise ValidationError(["Dancer not found"])
        return dancer
