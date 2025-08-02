from typing import Any, Dict, List, Optional
from uuid import UUID

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from graphql import GraphQLError, GraphQLResolveInfo
from graphql_relay import from_global_id

from users.models import User
from users.serializers import UserSerializer, LoginSerializer
from users.schema.filters import UserFilter
from users.utility import (
    USER_MESSAGES,
    get_order_by,
    USER_FIELDS,
    parse_integrity_error,
    drf_flatten_errors,
    format_serializer_validation_error,
)


# *============================================={Queries Services}=======================================================


def get_all_users(
    info: GraphQLResolveInfo,
    order_by: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> QuerySet[User]:
    """
    Retrieve a filtered and ordered queryset of users with related profile data.

    This function is designed for use with DjangoFilterConnectionField,
    enabling Relay-style pagination and advanced filtering.

    Responsibilities:
    - Load all users from the database with profile using select_related
    - Defer unnecessary fields using only(USER_FIELDS) for performance
    - Apply dynamic filtering using the UserFilter class
    - Convert order_by input into Django-compatible ordering via get_order_by
    - Raise appropriate errors if no data is found

    Args:
        info (GraphQLResolveInfo): Context information from the GraphQL resolver.
        order_by (Optional[str]): A comma-separated string of fields to order by (e.g. "-created_at,username").
        filters (Optional[Dict[str, Any]]): A dictionary of filter conditions passed from the client.

    Returns:
        QuerySet[User]: A Django QuerySet of User instances with filtering and ordering applied.

    Raises:
        GraphQLError: If no users exist, or the applied filters return an empty result set.
    """

    # Step 1: Get base queryset including related profile to reduce queries
    queryset: QuerySet[User] = User.objects.select_related("profile").only(*USER_FIELDS)

    # Early check: if no users exist at all
    if not queryset.exists():
        raise GraphQLError(USER_MESSAGES["list_empty"])

    # Step 2: Apply filters if provided
    if filters:
        queryset = UserFilter(filters, queryset=queryset).qs

        # Error if filters exclude all users
        if not queryset.exists():
            raise GraphQLError(USER_MESSAGES["search_empty"])

    # Step 3: Apply ordering if specified
    if order_by:
        ordering: List[str] = get_order_by(order_by)
        queryset = queryset.order_by(*ordering)

    return queryset


def get_user_by_id(info: GraphQLResolveInfo, user_id: str) -> User:
    """
    Retrieve a single user instance by its Relay-style global ID.

    Args:
        info (GraphQLResolveInfo): The resolver context with request information.
        user_id (str): A Relay global ID representing the user.

    Returns:
        User: A User instance with its related profile.

    Raises:
        GraphQLError: If the user ID is invalid or the user does not exist.

    """
    # Validate the user_id string is a non-empty UUID
    if not isinstance(user_id, str) or not user_id.strip() or len(user_id) <= 2:
        raise GraphQLError(
            "Oops! It looks like the user ID is missing or invalid. Please try again."
        )

    try:
        # Step 2: Decode the global Relay ID (format: type:id)
        type_name, raw_id = from_global_id(user_id)
    except Exception:
        raise GraphQLError(
            "We couldn't read the user ID format. Please double-check and try again."
        )

    # Ensure the type name is 'User' to avoid mismatches
    if type_name != "UserNode":
        raise GraphQLError(f"Invalid type: expected 'UserNode', got '{type_name}'")

    try:
        # Step 3: Parse the raw ID to ensure it's a valid UUID
        user_uuid = UUID(raw_id)
    except ValueError:
        raise GraphQLError("The user ID format is not valid. Please try again.")

    try:
        # Step 4: Fetch the user including the related profile using select_related
        return User.objects.select_related("profile").get(id=user_uuid)
    except ObjectDoesNotExist:
        raise GraphQLError(USER_MESSAGES["not_found"])


def get_user_by_username(info: GraphQLResolveInfo, username: str) -> User:
    """
    Retrieve a single User instance by their username.

    Args:
        info (GraphQLResolveInfo): The resolver context with request information.
        username (str): The username of the user to retrieve.

    Returns:
        User: The corresponding User instance with its related Profile.

    Raises:
        GraphQLError: If the username is invalid or the user does not exist.
    """
    # Validate input
    if (
        not isinstance(username, str)
        or not username.strip()
        or len(username.strip()) <= 2
    ):
        raise GraphQLError("Please enter a valid username with at least 3 characters.")

    try:
        # Fetch the user with related profile
        return User.objects.select_related("profile").get(username=username.strip())
    except ObjectDoesNotExist:
        raise GraphQLError(USER_MESSAGES["not_found"])


# *============================================={Queries Services}=======================================================


# *============================================={Mutations Services}=====================================================


def signup_user(
    info: GraphQLResolveInfo,
    email: str,
    username: str,
    name: str,
    password: str,
    confirm_password: str,
    **kwargs: Any,
) -> User:
    # * validate the user data with serializers
    data = {
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": confirm_password,
        "name": name,
    }

    serializer = UserSerializer(data=data)

    if not serializer.is_valid(raise_exception=False):
        message, extensions = format_serializer_validation_error(serializer.errors)
        raise GraphQLError(message, extensions=extensions)

    try:
        with transaction.atomic():
            user: User = serializer.save()
    except IntegrityError as duplicate_error:
        field, value = parse_integrity_error(duplicate_error)

        raise GraphQLError(
            USER_MESSAGES["duplicate"],
            extensions={
                "code": "CONFLICT",
                "field": field,
                "errors": {field: f"A user with {field} '{value}' already exists."},
            },
        )
    except DRFValidationError as e:
        raise GraphQLError(
            "Error Invalid input during saving.",
            extensions={
                "code": "BAD_USER_INPUT",
                "errors": drf_flatten_errors(e.detail),
            },
        )

    return user


def login_user(info: GraphQLResolveInfo, email: str, password: str) -> User:
    """
    Authenticates a user using email and password.

    Args:
        info (GraphQLResolveInfo): GraphQL context info.
        email (str): User's email.
        password (str): User's plaintext password.

    Returns:
        User: Authenticated user object.

    Raises:
        GraphQLError: If serializer validation fails, user not found, or credentials are invalid.
    """

    # Validate basic input structure using serializer
    serializer = LoginSerializer(data={"email": email, "password": password})
    if not serializer.is_valid(raise_exception=False):
        message, extensions = format_serializer_validation_error(serializer.errors)
        raise GraphQLError(message, extensions=extensions)

    # Check if user exists
    try:
        user = User.objects.select_related("profile").get(email=email)
    except ObjectDoesNotExist:
        raise GraphQLError(
            USER_MESSAGES["email_with_no_user"],
            extensions={
                "code": "UNAUTHENTICATED",
                "errors": {
                    "email": USER_MESSAGES["email_with_no_user"],
                },
            },
        )

    # Validate password
    if not user.check_password(password):
        raise GraphQLError(
            USER_MESSAGES["invalid_password"],
            extensions={
                "code": "UNAUTHENTICATED",
                "errors": {
                    "password": USER_MESSAGES["invalid_password"],
                },
            },
        )

    return user


# *============================================={Mutations Services}=====================================================
