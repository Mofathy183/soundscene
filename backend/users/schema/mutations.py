import graphene
import graphql_jwt
from .types import UserNode
from users.services import signup_user, login_user
from users.utility import USER_MESSAGES, send_cookies


class AuthMutation(graphene.ObjectType):
    # Login (Obtain both access and refresh tokens)
    access_token = graphql_jwt.ObtainJSONWebToken.Field()

    # Refresh access token using refresh token cookie
    refresh_token = graphql_jwt.Refresh.Field()

    # Optional: Revoke refresh tokens (logout)
    revoke_token = graphql_jwt.Revoke.Field()

    # Optional: Verify the validity of a token
    verify_token = graphql_jwt.Verify.Field()


class SignUp(graphene.Mutation):
    """
    GraphQL mutation for signing up a new user.

    This mutation handles user registration, including input validation,
    creation of the user, and setting authentication cookies using JWT tokens.

    Returns:
        - user (UserNode): The newly created user instance.
        - success (bool): Indicates if the signup was successful.
        - message (str): A success message or error feedback.
    """

    # Output fields returned by the mutation
    user = graphene.Field(UserNode)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        # Required input arguments for user signup
        email = graphene.String(required=True)
        username = graphene.String(required=True)
        name = graphene.String(required=True)
        password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)

    def mutate(self, info, email, username, name, password, confirm_password, **kwargs):
        """
        Handles the mutation logic for user signup.

        Validates the input data, creates a new user, and sends JWT tokens
        via cookies for authentication.

        Args:
            info: GraphQL execution context.
            email (str): User's email address.
            username (str): Chosen username.
            name (str): Full name.
            password (str): Password.
            confirm_password (str): Password confirmation.
            **kwargs: Any additional fields (optional).

        Returns:
            SignUp: An instance of the mutation with the created user,
                    success flag, and a user-friendly message.
        """
        # Create user using signup service logic (includes validation)
        user = signup_user(
            info=info,
            email=email,
            username=username,
            name=name,
            password=password,
            confirm_password=confirm_password,
            **kwargs,
        )

        # Set authentication cookies using JWT tokens
        send_cookies(info, user)

        # Return mutation response with user info and success message
        return SignUp(user=user, success=True, message=USER_MESSAGES["signup_success"])


class Login(graphene.Mutation):
    """
    GraphQL mutation for user login.

    This mutation authenticates a user with email and password credentials,
    issues secure authentication cookies (e.g., JWT), and returns basic user data.

    Returns:
        - user (UserNode): The authenticated user instance.
        - success (bool): Indicates if the login was successful.
        - message (str): A human-readable login success message.
    """

    # Output fields returned by the mutation
    user = graphene.Field(UserNode)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        # Required input arguments for user login
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        """
        Handles the login mutation logic.

        Authenticates the user using provided credentials. On success,
        authentication tokens are issued via HTTP-only cookies.

        Args:
            info: GraphQL resolve info/context (contains request metadata).
            email (str): User's email address.
            password (str): User's plain-text password.

        Returns:
            Login: An instance of the mutation containing the user,
                   a success flag, and a success message.
        """
        # Attempt to authenticate the user
        user = login_user(info, email, password)

        # On successful login, send JWT auth tokens via cookies
        send_cookies(info, user)

        # Return the mutation response with user info and message
        return Login(
            user=user,
            success=True,
            message=USER_MESSAGES["login_success"],
        )