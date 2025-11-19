"""Pydantic schemas for User entity."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class CreateUserSchema(BaseModel):
    """Schema for creating a user."""

    email: EmailStr = Field(..., description="User email (must be unique)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    role: UserRole = Field(..., description="User role (ADMIN, STAFF, MC, JUDGE)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "email": "staff@example.com",
                "first_name": "Jane",
                "role": "STAFF",
            }
        }


class UpdateUserSchema(BaseModel):
    """Schema for updating a user."""

    email: Optional[EmailStr] = Field(None, description="User email")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
