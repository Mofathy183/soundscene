from typing import Any, Dict, List, Optional
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from graphql import GraphQLError, GraphQLResolveInfo
from graphql_relay import from_global_id

from users.models import User
from users.schema.filters import UserFilter
from users.utility import USER_MESSAGES, get_order_by


def get_all_users(
    info: GraphQLResolveInfo,
    order_by: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> QuerySet[User]:
    """
    Fetch a filtered and ordered queryset of users.

    This resolver is designed to be used with DjangoFilterConnectionField,
    which supports Relay-style pagination (first, after, last, before).

    Responsibilities:
    - Load all users from the database
    - Apply filtering via the UserFilter class
    - Convert the client-supplied order_by string using get_order_by utility
    - Apply the ordering to the queryset

    Args:
        info (GraphQLResolveInfo): The resolver context containing request info.
        order_by (Optional[str]): Field name(s) to order by (e.g. "-username").
        filters (Optional[Dict[str, Any]]): Dictionary of filter conditions.

    Returns:
        QuerySet: A filtered and ordered Django QuerySet of User instances.

    Raises:
        GraphQLError: If no users exist, or no users match the given filters.

    """
    # Step 1: Get the base queryset
    queryset: QuerySet[User] = User.objects.all()

    # Raise an error if there are no users at all
    if not queryset.exists():
        raise GraphQLError(USER_MESSAGES["list_empty"])

    # Step 2: Apply filtering based on the provided filter dictionary
    queryset = UserFilter(filters, queryset=queryset).qs

    # Raise an error if filters return no matches
    if not queryset.exists():
        raise GraphQLError(USER_MESSAGES["search_empty"])

    # Step 3: Determine the ordering based on the client's input
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
    if not user_id or not isinstance(user_id, str) or not user_id.strip():
        raise GraphQLError("Requires a valid user UUID.")

    try:
        # Decode the global ID to extract the raw UUID string
        _, user_uuid_str = from_global_id(user_id)

        # Ensure it is a valid UUID format
        user_uuid = UUID(user_uuid_str)
    except Exception:
        raise GraphQLError("Requires a valid user UUID.")

    try:
        # Retrieve user with related profile
        user: User = User.objects.select_related("profile").get(id=user_uuid)
        return user
    except ObjectDoesNotExist:
        raise GraphQLError(USER_MESSAGES["not_found"])
