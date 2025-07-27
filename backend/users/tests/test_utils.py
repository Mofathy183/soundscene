from pathlib import Path

import pytest
from graphql import GraphQLError

from users.utility import (
    get_order_by,
    profile_avatar_path,
)

from .factories import ProfileFactory


@pytest.mark.skip(reason="Finsh testing")
@pytest.mark.parametrize(
    "username, filename, expected_path",
    [
        ("Bruce", "bat.png", str(Path("avatars") / "profile_Bruce" / "bat.png")),
        (
            "clark_kent",
            "super.png",
            str(Path("avatars") / "profile_clark_kent" / "super.png"),
        ),
        ("Diana", "wonder.jpg", str(Path("avatars") / "profile_Diana" / "wonder.jpg")),
    ],
)
def test_profile_avatar_path(mocker, username, filename, expected_path):
    # Create a mock user with a username
    mock_user_instance = mocker.Mock(username=username)

    # Create a mock profile instance with the mocked user
    mock_profile_instance = mocker.Mock(spec=ProfileFactory, user=mock_user_instance)

    result = profile_avatar_path(mock_profile_instance, filename)

    assert result == expected_path


@pytest.mark.skip(reason="Finsh testing")
class TestGetOrderBy:
    @pytest.mark.parametrize(
        "field, expected",
        [
            ("-created_at", ["-created_at", "-id"]),
            ("username", ["username", "id"]),
        ],
    )
    def test_get_order_by(self, field, expected):
        result = get_order_by(field)
        assert result == expected

    @pytest.mark.parametrize(
        "input_data, expected",
        [
            (None, ["-created_at", "-id"]),  # No order_by input
            ([], ["-created_at", "-id"]),  # Empty list input
        ],
    )
    def test_get_order_by_defaults(self, input_data, expected):
        assert get_order_by(input_data) == expected

    @pytest.mark.parametrize(
        "field", ["is_active", "is_superuser", "is_staff", "date_joined"]
    )
    def test_get_order_by_invalid_sort_field(self, field):
        with pytest.raises(GraphQLError) as graph_error:
            get_order_by(field)

        error = graph_error.value.args[0]
        assert error == f"Invalid sort field: '{field}'"
