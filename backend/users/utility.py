from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Any, Union
from graphql_jwt.shortcuts import get_token, create_refresh_token
from graphql import GraphQLError, GraphQLResolveInfo
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError as DRFValidationError
import re

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
    # Listing
    "list_success": "Users loaded successfully.",
    "list_empty": "No users found. Try again later.",
    # Retrieval
    "get_success": "User details retrieved successfully.",
    "not_found": "Sorry, we couldn’t find the user you’re looking for.",
    # Creation
    "create_success": "Welcome aboard! Your account has been created successfully.",
    "duplicate": "An account with this email already exists. Please use a different one.",
    # Login
    "login_success": "Welcome back! You’ve logged in successfully.",
    "invalid_credentials": "Invalid email or password. Please try again.",
    "email_with_no_user": "No account found with this email address.",
    "invalid_password": "The password you entered is incorrect.",
    # Update
    "update_success": "Your information was updated successfully.",
    "update_not_found": "Update failed: the specified user doesn’t exist.",
    # Deletion
    "delete_success": "User account has been deleted.",
    "unauthorized_delete": "You don’t have permission to delete this user.",
    # Search
    "search_success": "Users matching your search were found.",
    "search_empty": "No users matched your search. Try adjusting your filters.",
    # Signup
    "signup_success": "Account created! Please check your email to verify and log in.",
    "signup_email_sent": "A confirmation email has been sent. Please check your inbox.",
    # Generic errors (optional)
    "unknown_error": "Something went wrong. Please try again later.",
    "permission_denied": "You don’t have permission to perform this action.",
}

USER_FIELDS: list[str] = [
    "id",
    "name",
    "username",
    "email",
    "profile",
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
    # Retrieval
    "get_success": "Profile loaded successfully.",
    "not_found": "We couldn’t find the profile you’re looking for.",
    # Update
    "update_success": "Your profile has been updated.",
    "update_not_found": "Update failed — the profile doesn’t exist.",
    "unauthorized_update": "You’re not authorized to update this profile.",
    # Avatar
    "avatar_upload_success": "Your avatar was uploaded successfully!",
    "avatar_upload_failed": "Something went wrong while uploading your avatar. Please try again.",
    # Search
    "search_success": "Profiles matching your search were found.",
    "search_empty": "No matching profiles found. Try adjusting your search filters.",
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


# *============================================={Auth Helpers}========================================================
if TYPE_CHECKING:
    from .models import User


def send_cookies(info: GraphQLResolveInfo, user: "User") -> None:
    """
    Assigns JWT access and refresh tokens to the context object so that
    `django-graphql-jwt` can automatically set them as HTTP-only cookies
    when using the `jwt_cookie()` view wrapper.

    This function is safe to use in both production and test environments.
    It checks if the `context` object is writable before assigning tokens.

    Args:
        info (GraphQLResolveInfo): GraphQL resolve info containing the request context.
        user (User): The authenticated user instance for whom tokens are generated.
    """
    context = getattr(info, "context", None)

    # Ensure the context object can accept new attributes
    if context is None or not hasattr(context, "__dict__"):
        return

    # Set tokens on the context to trigger automatic cookie injection
    context.jwt_token = get_token(user)
    context.jwt_refresh_token = create_refresh_token(user)


# *============================================={Auth Helpers}========================================================

# *============================================={Error Formaters}========================================================


def parse_integrity_error(error: IntegrityError) -> Tuple[str, str]:
    """Extract the field and value from IntegrityError message."""
    # Example error message:
    # DETAIL:  Key (email)=(charleslowery@example.com) already exists.
    match = re.search(r"Key \((\w+)\)=\((.+?)\)", str(error))
    if match:
        field, value = match.groups()
        return field, value
    return "unknown", "unknown"


def drf_flatten_errors(
    detail: DRFValidationError,
) -> Dict[str, Union[str, List[str], Dict[str, Any]]]:
    """
    Recursively flattens a Django REST Framework (DRF) ValidationError detail dictionary
    into a dictionary of plain strings or lists of strings.

    This is useful for formatting DRF's complex error structures into a form
    that can be cleanly returned in GraphQL errors, API responses, or logs.

    Example input:
        {
            "email": ["This field is required."],
            "profile": {
                "age": ["Must be over 18."]
            }
        }

    Output:
        {
            "email": ["This field is required."],
            "profile": {
                "age": ["Must be over 18."]
            }
        }
    """

    def flatten(
        value: Union[str, List[Any], Dict[str, Any]],
    ) -> Union[str, List[str], Dict[str, Any]]:
        # If the value is a list (e.g. list of error messages), convert each item to a string
        if isinstance(value, list):
            return [str(item) for item in value]
        # If the value is a dict (e.g. nested serializer errors), recurse on each item
        elif isinstance(value, dict):
            return {k: flatten(v) for k, v in value.items()}
        # Otherwise, just return the string representation (usually a single ErrorDetail)
        return str(value)

    # Apply flattening to each field in the top-level error dictionary
    return {field: flatten(messages) for field, messages in detail.items()}


def format_serializer_validation_error(
    serializer_errors: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """
    Formats DRF serializer errors into a message and GraphQL-style extensions dictionary.

    Args:
        serializer_errors (dict): The `.errors` from a DRF serializer.

    Returns:
        tuple[str, dict]: A tuple containing:
            - message (str): General summary message indicating invalid fields.
            - extensions (dict): Structured data with 'code' and 'errors' keys.
    """

    def flatten(
        value: Union[str, List[Any], Dict[str, Any]],
    ) -> Union[str, List[str], Dict[str, Any]]:
        if isinstance(value, list):
            return [str(v) for v in value]
        elif isinstance(value, dict):
            return {k: flatten(v) for k, v in value.items()}
        return str(value)

    errors = {field: flatten(messages) for field, messages in serializer_errors.items()}

    fields = ", ".join(errors.keys())
    message = f"Invalid input in the following field(s): {fields}."

    return message, {"code": "BAD_USER_INPUT", "errors": errors}


# *============================================={Error Formaters}========================================================
