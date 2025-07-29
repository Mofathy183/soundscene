from uuid import uuid4

import pytest
from graphql import GraphQLError
from graphql_relay import to_global_id

from users.models import User
from users.services import get_all_users, get_user_by_id, get_user_by_username
from users.utility import USER_MESSAGES


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
