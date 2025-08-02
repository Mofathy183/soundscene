from uuid import uuid4

import pytest
from graphql import GraphQLError
from graphql_relay import to_global_id
from rest_framework import serializers

from users.models import User
from users.services import (
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    signup_user,
    login_user,
)
from users.utility import USER_MESSAGES

# *============================================={Queries Services Tests}=================================================


@pytest.mark.django_db
class TestAllUsersLogic:
    def test_get_all_users_no_users_found(self):
        with pytest.raises(GraphQLError) as graphql_error:
            get_all_users(None, "", {})

        error = graphql_error.value.args[0]
        assert error == USER_MESSAGES["list_empty"]

    def test_get_all_users_no_result_from_filter(self, user_factory):
        user_factory.create_batch(5, name="Custom Name")

        with pytest.raises(GraphQLError) as graphql_error:
            get_all_users(None, "", {"name": "Batmen"})

        error = graphql_error.value.args[0]
        assert error == USER_MESSAGES["search_empty"]

    @pytest.mark.parametrize(
        "field_name, order_field, expected_order",
        [
            ("username", "username", ["user_a", "user_b", "user_c"]),
            ("name", "-name", ["user-c", "user-b", "user-a"]),
            ("email", "-email", ["z@example.com", "m@example.com", "a@example.com"]),
        ],
    )
    def test_get_all_users_apply_ordering(
        self, user_factory, field_name, order_field, expected_order
    ):
        # Create users with dynamic field assignment
        for value in expected_order:
            user_factory(**{field_name: value})

        result = get_all_users(info=None, order_by=order_field, filters={})

        # Compare dynamically based on the field being tested
        actual_order = [getattr(user, field_name) for user in result]
        assert actual_order == expected_order

    def test_get_all_users_success(self, user_factory):
        users = user_factory.create_batch(5)

        result = get_all_users(None, "", {})

        assert len(result) == 5

        # Compare by unique field (e.g., username or id)
        created_usernames = {user.username for user in users}
        result_usernames = {user.username for user in result}

        assert all(username in result_usernames for username in created_usernames)


@pytest.mark.django_db
class TestGetUserById:
    def test_get_user_by_id_success(self, user_factory):
        user = user_factory(id=uuid4())
        global_id = to_global_id("UserNode", user.id)

        result = get_user_by_id(None, global_id)

        assert isinstance(result, User)
        assert result.id == user.id
        assert result.email == user.email

    def test_get_user_by_id_use_fake_id(self):
        fake_id = to_global_id("UserNode", uuid4())
        with pytest.raises(GraphQLError) as graphql_error:
            get_user_by_id(None, fake_id)

        error = graphql_error.value.args[0]
        assert error == USER_MESSAGES["not_found"]

    @pytest.mark.parametrize(
        "bad_input",
        [
            315654,  # Not a string
            "   ",  # Blank string
            "",  # Empty string
            None,  # None input
        ],
    )
    def test_resolve_get_user_by_invalid_id(self, bad_input):
        with pytest.raises(GraphQLError) as graphql_error:
            get_user_by_id(info=None, user_id=bad_input)

        error = graphql_error.value.args[0]
        assert (
            error
            == "Oops! It looks like the user ID is missing or invalid. Please try again."
        )


@pytest.mark.django_db
class TestGetUserByUsername:
    def test_get_user_by_username_success(self, user_factory):
        user = user_factory()

        result = get_user_by_username(None, user.username)

        assert isinstance(result, User)
        assert result.id == user.id
        assert result.email == user.email

    def test_get_user_by_username_user_do_not_exist(self):
        with pytest.raises(GraphQLError) as graphql_error:
            get_user_by_username(None, "michaelrodriguez")

        error = graphql_error.value.args[0]
        assert error == USER_MESSAGES["not_found"]

    @pytest.mark.parametrize(
        "username",
        [
            "",  # Empty string
            "  ",  # Only whitespace
            "j",  # Only one character (not matching the + after first char)
            "j  ",  # Only one character*whitespace
            "jj",  # Only two character
            "jj  ",  # Only two character*whitespace
            1255,  # Invalid character (@)
        ],
    )
    def test_resolve_get_user_by_username_invalid_usernames(self, username):
        with pytest.raises(GraphQLError) as graphql_error:
            get_user_by_username(None, username=username)

        error = graphql_error.value.args[0]

        assert error == "Please enter a valid username with at least 3 characters."


# *============================================={Queries Services Tests}=================================================


# *============================================={Mutations Services Tests}===============================================


@pytest.mark.django_db
class TestSignUpUser:
    def test_signup_user_success(self, user_factory):
        user = user_factory.build()

        result = signup_user(
            None,
            user.email,
            user.username,
            user.name,
            user.password,
            user.password,
        )

        assert isinstance(result, User)
        assert result.id is not None
        assert result.email == user.email
        assert result.username == user.username
        assert result.name == user.name

    def test_signup_user_already_exists_duplicate_email(self, user_factory):
        user_password = "PassW0rd122?!"
        user = user_factory(password=user_password)

        with pytest.raises(GraphQLError) as graphql_error:
            signup_user(
                None,
                user.email,
                user.username,
                user.name,
                user_password,
                user_password,
            )

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert error == USER_MESSAGES["duplicate"]
        assert extensions["code"] == "CONFLICT"
        assert extensions["field"] == "email"
        assert extensions["errors"] == {
            "email": f"A user with email '{user.email}' already exists."
        }

    def test_signup_user_already_exists_duplicate_username(self, user_factory):
        user_password = "PassW0rd122?!"
        user = user_factory(password=user_password)
        with pytest.raises(GraphQLError) as graphql_error:
            signup_user(
                None,
                "test123@gmail.com",
                user.username,
                user.name,
                user_password,
                user_password,
            )

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert error == USER_MESSAGES["duplicate"]
        assert extensions["code"] == "CONFLICT"
        assert extensions["field"] == "username"
        assert extensions["errors"] == {
            "username": f"A user with username '{user.username}' already exists."
        }

    def test_signup_user_raises_drf_validation_error_on_save(
        self, monkeypatch, user_factory
    ):
        # Patch the create method to simulate a DRFValidationError at save
        def bad_create(self, validated_data):
            raise serializers.ValidationError(
                {"username": "This username is not allowed."}
            )

        monkeypatch.setattr("users.serializers.UserSerializer.create", bad_create)
        user_password = "PassW0rd122?!"
        user = user_factory.build(password=user_password)
        with pytest.raises(GraphQLError) as graphql_error:
            signup_user(
                None,
                user.email,
                user.username,
                user.name,
                user_password,
                user_password,
            )

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert error == "Error Invalid input during saving."
        assert extensions["code"] == "BAD_USER_INPUT"
        assert extensions["errors"] == {"username": "This username is not allowed."}

    @pytest.mark.parametrize(
        "email, username, name, password, confirm_password, expected_field",
        [
            # Invalid email
            (
                "invalidemail",
                "validuser",
                "Valid Name",
                "PassW0rd122?!",
                "PassW0rd122?!",
                "email",
            ),
            # Empty username
            (
                "test@example.com",
                "",
                "Valid Name",
                "PassW0rd122?!",
                "PassW0rd122?!",
                "username",
            ),
            # Empty name
            (
                "test@example.com",
                "validuser",
                "",
                "PassW0rd122?!",
                "PassW0rd122?!",
                "name",
            ),
        ],
    )
    def test_signup_user_invalid_serializer(
        self, email, username, name, password, confirm_password, expected_field
    ):
        with pytest.raises(GraphQLError) as graphql_error:
            signup_user(
                None,
                email,
                username,
                name,
                password,
                confirm_password,
            )

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert error == f"Invalid input in the following field(s): {expected_field}."
        assert extensions["code"] == "BAD_USER_INPUT"
        assert extensions["errors"] == {
            expected_field: extensions["errors"][expected_field]
        }

    @pytest.mark.parametrize(
        "password, confirm_password, expected_fields",
        [
            # Too short and no complexity
            (
                "short",
                "short",
                ["password", "confirm_password"],
            ),
            # Missing special character
            (
                "Password123",
                "Password123",
                ["password", "confirm_password"],
            ),
            # Mismatched confirmation
            (
                "PassW0rd122?!",
                "Mismatch123?!",
                ["confirm_password"],
            ),
            # Missing uppercase
            (
                "password123?!",
                "password123?!",
                ["password", "confirm_password"],
            ),
            # Missing lowercase
            (
                "PASSWORD123?!",
                "PASSWORD123?!",
                ["password", "confirm_password"],
            ),
            # Missing digit
            (
                "Password?!",
                "Password?!",
                ["password", "confirm_password"],
            ),
        ],
    )
    def test_signup_user_invalid_serializer_for_password_and_confirm_password(
        self, password, confirm_password, expected_fields
    ):
        with pytest.raises(GraphQLError) as graphql_error:
            signup_user(
                info=None,
                email="test@example.com",
                username="validuser",
                name="Valid Name",
                password=password,
                confirm_password=confirm_password,
            )

        extensions = graphql_error.value.extensions
        error = graphql_error.value.message

        assert (
            error
            == f"Invalid input in the following field(s): {', '.join(expected_fields)}."
        )
        assert extensions["code"] == "BAD_USER_INPUT"

        for field in expected_fields:
            assert field in extensions["errors"]

        # Optional: strict field match
        assert sorted(extensions["errors"].keys()) == sorted(expected_fields)


@pytest.mark.django_db
class TestLoginUser:
    def test_login_user_sccess(self, user_factory):
        user_password = "PassW0rd122?!"
        user = user_factory()

        result = login_user(None, user.email, user_password)

        assert isinstance(result, User)
        assert result.id is not None
        assert result.email == user.email
        assert result.username == user.username
        assert result.name == user.name

    @pytest.mark.parametrize(
        "email, password, invalid_field",
        [
            ("batman1936@gmail.com", "", ["password"]),
            ("batman1936_gothom.com", "PassW0rd122?!", ["email"]),
            ("batman1936_gothom.com", "", ["email", "password"]),
        ],
    )
    def test_login_user_invalid_serializer(self, email, password, invalid_field):
        with pytest.raises(GraphQLError) as graphql_error:
            login_user(None, email, password)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert (
            error
            == f"Invalid input in the following field(s): {', '.join(invalid_field)}."
        )
        assert extensions["code"] == "BAD_USER_INPUT"
        for field in invalid_field:
            assert field in extensions["errors"]
            assert isinstance(extensions["errors"][field], list)
            assert len(extensions["errors"][field]) > 0

    def test_login_user_password_not_match(self, user_factory):
        wrong_password = "PassW0rd122?!17771"
        user = user_factory()

        with pytest.raises(GraphQLError) as graphql_error:
            login_user(None, user.email, wrong_password)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert error == USER_MESSAGES["invalid_password"]
        assert extensions["code"] == "UNAUTHENTICATED"
        assert extensions["errors"] == {"password": USER_MESSAGES["invalid_password"]}

    def test_login_user_no_account_found_with_email(self):
        user_email = "batman1936@gmail.com"
        user_password = "PassW0rd122?!"

        with pytest.raises(GraphQLError) as graphql_error:
            login_user(None, user_email, user_password)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert error == USER_MESSAGES["email_with_no_user"]
        assert extensions["code"] == "UNAUTHENTICATED"
        assert extensions["errors"] == {"email": USER_MESSAGES["email_with_no_user"]}


# *============================================={Mutations Services Tests}===============================================
