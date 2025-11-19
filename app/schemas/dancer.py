"""Pydantic schemas for Dancer entity."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateDancerSchema(BaseModel):
    """Schema for creating a dancer."""

    email: EmailStr = Field(..., description="Dancer email (must be unique)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    date_of_birth: date = Field(..., description="Date of birth")
    blaze: str = Field(..., min_length=1, max_length=100, description="Stage name")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    city: Optional[str] = Field(None, max_length=100, description="City")

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Ensure dancer age is between 10-100 years."""
        today = date.today()
        age = (today - v).days // 365

        if age < 10:
            raise ValueError("Dancer must be at least 10 years old")
        if age > 100:
            raise ValueError("Invalid birth date (age exceeds 100 years)")

        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "email": "bboy@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "2000-01-01",
                "blaze": "B-Boy Storm",
                "country": "France",
                "city": "Paris",
            }
        }


class UpdateDancerSchema(BaseModel):
    """Schema for updating a dancer."""

    email: Optional[EmailStr] = Field(None, description="Dancer email")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    blaze: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: Optional[date]) -> Optional[date]:
        """Ensure dancer age is between 10-100 years if provided."""
        if v is None:
            return v

        today = date.today()
        age = (today - v).days // 365

        if age < 10:
            raise ValueError("Dancer must be at least 10 years old")
        if age > 100:
            raise ValueError("Invalid birth date (age exceeds 100 years)")

        return v
