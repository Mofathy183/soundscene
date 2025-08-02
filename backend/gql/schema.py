import graphene
from users.schema.queries import UserQuery
from users.schema.mutations import AuthMutation, SignUp, Login


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
# Root Mutation: Collect all GraphQL mutations here.
# ─────────────────────────────────────────────
class Mutation(AuthMutation, graphene.ObjectType):
    """
    Root GraphQL Mutation class.

    This class aggregates all custom mutation fields in the application.
    Each mutation (e.g., SignUp, Login) should be added here
    as a class attribute.

    Example:
        class Mutation(graphene.ObjectType):
            sign_up = SignUp.Field()
            login = Login.Field()
    """

    sign_up = SignUp.Field()  # Register new users
    login = Login.Field()  # Login users


# ─────────────────────────────────────────────
# GraphQL Schema: Register root Query and Mutation classes
# ─────────────────────────────────────────────

schema = graphene.Schema(
    query=Query,  # Root Query class (e.g., user, etc.)
    mutation=Mutation,  # Root Mutation class (e.g., sign up, login, update, etc.)
)
