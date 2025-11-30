"""Flash message utilities for user feedback."""

from typing import Literal
from fastapi import Request

FlashCategory = Literal["success", "error", "warning", "info"]


def add_flash_message(
    request: Request, message: str, category: FlashCategory = "info"
) -> None:
    """Add flash message to session.

    Args:
        request: FastAPI request object
        message: Message to display to user
        category: Message category (success, error, warning, info)
    """
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []
    request.session["flash_messages"].append({"message": message, "category": category})


def get_flash_messages(request: Request) -> list[dict[str, str]]:
    """Get and clear flash messages from session.

    Args:
        request: FastAPI request object

    Returns:
        List of flash message dictionaries with 'message' and 'category' keys
    """
    return request.session.pop("flash_messages", [])
