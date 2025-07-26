from typing import TYPE_CHECKING

# from graphql import GraphQLError
from pathlib import Path

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
