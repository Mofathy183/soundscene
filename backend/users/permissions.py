from functools import wraps
from typing import (
    Callable,
    Any,
    Protocol,
    TypeVar,
    cast,
    Optional,
)
from enum import Enum
from graphql import GraphQLError
from users.models import UserRole

# Typing for resolver functions
TResolver = TypeVar("TResolver", bound=Callable[..., Any])


def graphql_login_required(func: TResolver) -> TResolver:
    """
    Decorator for GraphQL resolvers that ensures the user is authenticated.

    Raises:
        GraphQLError: If the user is not authenticated.

    Returns:
        Callable: The decorated resolver function.
    """

    @wraps(func)
    def wrapper(self: Any, info: Any, *args: Any, **kwargs: Any) -> Any:
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError(
                "Authentication Required: You must be logged in to perform this action.",
                extensions={"code": "UNAUTHENTICATED"},
            )
        return func(self, info, *args, **kwargs)

    return cast(TResolver, wrapper)


def role_required(*allowed_roles: UserRole) -> Callable[[TResolver], TResolver]:
    """
    Decorator for GraphQL resolvers that checks if the user has one of the allowed roles.

    Args:
        *allowed_roles (UserRole): Allowed roles for the resolver.

    Raises:
        GraphQLError: If the user's role is not among the allowed.

    Returns:
        Callable: The decorated resolver function.
    """
    role_values = [role.value for role in allowed_roles]

    def decorator(func: TResolver) -> TResolver:
        @wraps(func)
        def wrapper(self: Any, info: Any, *args: Any, **kwargs: Any) -> Any:
            user = info.context.user
            user_role: Permissions | str = getattr(user, "role", "Anonymous")

            if user.role not in role_values:
                role_val: str = getattr(user_role, "value", str(user_role))

                raise GraphQLError(
                    f"Access denied. Your role '{role_val}' is not authorized for this action. "
                    f"Allowed roles: {', '.join(role_values)}.",
                    extensions={
                        "code": "FORBIDDEN",
                        "user_role": role_val,
                        "allowed_roles": role_values,
                    },
                )

            return func(self, info, *args, **kwargs)

        return cast(TResolver, wrapper)

    return decorator


def login_and_role_required(
    *allowed_roles: UserRole,
) -> Callable[[TResolver], TResolver]:
    """
    Combines login and role checks into a single decorator.

    Args:
        *allowed_roles (UserRole): Allowed roles for the resolver.

    Returns:
        Callable: A composed decorator that enforces login and role.
    """

    def decorator(func: TResolver) -> TResolver:
        return graphql_login_required(role_required(*allowed_roles)(func))

    return decorator


# * Shortcut decorators for common roles
admin_required: Callable[[TResolver], TResolver] = login_and_role_required(
    UserRole.ADMIN
)
moderator_required: Callable[[TResolver], TResolver] = login_and_role_required(
    UserRole.ADMIN, UserRole.MODERATOR
)
reviewer_required: Callable[[TResolver], TResolver] = login_and_role_required(
    UserRole.ADMIN, UserRole.REVIEWER
)
creator_required: Callable[[TResolver], TResolver] = login_and_role_required(
    UserRole.ADMIN, UserRole.CREATOR
)
user_required: Callable[[TResolver], TResolver] = login_and_role_required(UserRole.USER)


class Permissions(str, Enum):
    """
    Enum containing Django permission codenames for User and Profile models.

    These permissions can be used directly with `user.has_perm(...)`.
    """

    # User permissions
    ADD_USER = "users.add_user"
    CHANGE_USER = "users.change_user"
    DELETE_USER = "users.delete_user"
    VIEW_USER = "users.view_user"

    # Profile permissions
    ADD_PROFILE = "users.add_profile"
    CHANGE_PROFILE = "users.change_profile"
    DELETE_PROFILE = "users.delete_profile"
    VIEW_PROFILE = "users.view_profile"


def permission_required(
    required_perm: Permissions, message: Optional[str] = None
) -> Callable[[TResolver], TResolver]:
    """
    Decorator for checking Django model permissions in GraphQL resolvers.

    Args:
        required_perm (Permissions): The permission codename (e.g., 'users.view_user').
        message (str, optional): Custom error message on failure.

    Raises:
        GraphQLError: If the user does not have the required permission.

    Returns:
        Callable: The decorated resolver function.
    """

    def decorator(func: TResolver) -> TResolver:
        @wraps(func)
        def wrapper(self: Any, info: Any, *args: Any, **kwargs: Any) -> Any:
            user = info.context.user
            if not user.has_perm(required_perm):
                raise GraphQLError(
                    message
                    or f"Access Denied: Missing required permission '{required_perm.value}'.",
                    extensions={
                        "code": "FORBIDDEN",
                        "required_permission": required_perm.value,
                    },
                )
            return func(self, info, *args, **kwargs)

        return cast(TResolver, wrapper)

    return decorator


class GetOwnerIdCallable(Protocol):
    def __call__(self, self_: Any, info: Any, *args: Any, **kwargs: Any) -> int: ...


def owner_required(
    get_owner_id: GetOwnerIdCallable,
) -> Callable[[TResolver], TResolver]:
    """
    Restricts access to resources that must be owned by the authenticated user.

    When to Use:
        Use this when the resource being accessed must belong to the requesting user.
        Typical use cases:
            - Viewing or editing their own profile
            - Accessing their own uploaded audio, scenes, posts, etc.
            - Downloading their own data

    Args:
        get_owner_id (Callable): A function that extracts the expected owner ID
                                 (typically from kwargs like `kwargs["user_id"]`).

    Raises:
        GraphQLError: If the user is unauthenticated or is not the resource owner.

    Returns:
        Callable: The decorated resolver function.
    """

    def decorator(func: TResolver) -> TResolver:
        @wraps(func)
        def wrapper(self: Any, info: Any, *args: Any, **kwargs: Any) -> Any:
            user = info.context.user

            if not user.is_authenticated:
                raise GraphQLError(
                    message="Authentication Required: You must be logged in to access this resource.",
                    extensions={"code": "UNAUTHENTICATED"},
                )

            # Admins bypass ownership check
            if hasattr(user, "role") and user.role == UserRole.ADMIN:
                return func(self, info, *args, **kwargs)

            expected_owner_id = get_owner_id(self, info, *args, **kwargs)

            if user.id != expected_owner_id:
                raise GraphQLError(
                    message="Access Denied: This resource belongs to another user. You are not authorized to access it.",
                    extensions={
                        "code": "FORBIDDEN",
                        "reason": "NOT_RESOURCE_OWNER",
                    },
                )

            return func(self, info, *args, **kwargs)

        return cast(TResolver, wrapper)

    return decorator


# """
#     run example for the permissions flow:
#         # or use any Shortcut decorators
#         @user_required  # 1. Requires authentication and correct role (e.g. UserRole.USER)
#         @permission_required(Permissions.VIEW_PROFILE)  # 2. Requires general permission
#         @owner_required(lambda self, info, *args, **kwargs: kwargs["user_id"])  # 3. Requires ownership of the resource
#         def resolve_user_profile(self, info, user_id):
#             ...
# """
