from graphene import ObjectType, Field, ID, String
from graphene_django.filter import DjangoFilterConnectionField
from .types import UserNode
from users.services import get_all_users, get_user_by_id, get_user_by_username


class UserQuery(ObjectType):
    """
    Root GraphQL query class for user-related queries.

    Provides access to:
    - Paginated list of users with filtering and sorting (via `all_users`)
    """

    all_users = DjangoFilterConnectionField(UserNode)

    get_user_by_id = Field(UserNode, user_id=ID(required=True))

    get_user_by_username = Field(UserNode, username=String(required=True))

    def resolve_all_users(self, info, order_by=None, **filters):
        """
        Custom resolver for all_users that:
        - Extracts pagination params (first, after, last, before)
        - Passes filter dict to service layer
        """
        filters = filters or {}

        return get_all_users(
            info=info,
            order_by=order_by,
            filters=filters,
        )

    def resolve_get_user_by_id(self, info, user_id):
        return get_user_by_id(info, user_id)

    def resolve_get_user_by_username(self, info, username):
        return get_user_by_username(info, username)
