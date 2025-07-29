import graphene
from users.schema.queries import UserQuery


# ─────────────────────────────────────────────
# Root Query: Combine your own queries here.
# ─────────────────────────────────────────────
class Query(UserQuery, graphene.ObjectType):  # type: ignore[misc]
    """
    Root query class.

    You can add your own custom queries here.
    This example uses `pass`, but you should replace it with
    your actual queries (like getting current user profile, etc).
    """

    pass


# ─────────────────────────────────────────────
# GraphQL Schema
# ─────────────────────────────────────────────
schema = graphene.Schema(
    query=Query,  # Root Query
)
