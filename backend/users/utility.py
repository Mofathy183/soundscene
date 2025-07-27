from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from graphql import GraphQLError

if TYPE_CHECKING:
    from .models import Profile  # or wherever your Profile model is


def profile_avatar_path(instance: "Profile", filename: str) -> str:
    """
    Generate a dynamic upload path for a user's avatar image.

    Args:
        instance (Profile): The Profile instance (used to access the related user's username).
        filename (str): The original uploaded file's name.

    Returns:
        str: A formatted path for storing the avatar.
             Example: "avatars/profile_johndoe/avatar.png"

    """
    return str(Path("avatars") / f"profile_{instance.user.username}" / filename)


USER_MESSAGES: Dict[str, str] = {
    "list_success": "Users loaded successfully.",
    "list_empty": "No users available at the moment.",
    "get_success": "User details retrieved successfully.",
    "not_found": "We couldn't find the user you're looking for.",
    "create_success": "User account created successfully.",
    "duplicate": "A user with this email already exists. Please use a different email.",
    "update_success": "User information updated successfully.",
    "update_not_found": "Update failed: user does not exist.",
    "delete_success": "User account deleted successfully.",
    "unauthorized_delete": "You don't have permission to delete this user.",
    "search_success": "User search completed successfully.",
    "search_empty": "No users matched your search. Try adjusting your filters.",
}

USER_FIELDS: list[str] = [
    "id",
    "name",
    "username",
    "email",
    "date_joined",
    "created_at",
    "is_active",
]

PROFILE_FIELDS: list[str] = [
    "id",
    "bio",
    "birthday_date",
    "age",
    "avatar",
    "created_at",
]

PROFILE_MESSAGES: Dict[str, str] = {
    "get_success": "Profile retrieved successfully.",
    "not_found": "Profile not found.",
    "update_success": "Profile updated successfully.",
    "update_not_found": "Update failed: profile does not exist.",
    "avatar_upload_success": "Avatar uploaded successfully.",
    "avatar_upload_failed": "Failed to upload avatar. Please try again.",
    "search_success": "Profile search completed successfully.",
    "search_empty": "No profiles matched your search. Try refining your criteria.",
    "unauthorized_update": "You don't have permission to update this profile.",
}


# Allowed sort fields from client input mapped to model fields
ALLOWED_SORT_FIELDS = {
    "name": "name",
    "email": "email",
    "username": "username",
    "created_at": "created_at",
    "updated_at": "updated_at",
}


def get_order_by(order_by: Optional[str]) -> List[str]:
    """
    Converts a GraphQL `order_by` input into a Django-compatible list of ordering fields.

    Ensures deterministic pagination by appending the 'id' field as a tiebreaker.

    Args:
        order_by (str): Ordering string (e.g., "-username", "created_at")

    Returns:
        List[str]: Django-style ordering list, e.g., ["-username", "-id"]

    Raises:
        GraphQLError: If the provided field is not in the allowed list.

    """
    if not order_by:
        return ["-created_at", "-id"]

    prefix = "-" if order_by.startswith("-") else ""
    field = order_by[1:] if prefix else order_by

    if field not in ALLOWED_SORT_FIELDS:
        raise GraphQLError(f"Invalid sort field: '{field}'")

    return [
        f"{prefix}{ALLOWED_SORT_FIELDS[field]}",
        f"{prefix}id",  # Always add 'id' as a tiebreaker
    ]
