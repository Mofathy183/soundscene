import pytest
from graphql_relay import from_global_id, to_global_id
from uuid import UUID, uuid4
from users.utility import USER_MESSAGES


@pytest.mark.django_db
class TestAllUsersQueries:
    def test_query_all_users_success(self, gql_client, execute_query, user_factory):
        users = user_factory.create_batch(5)
        query = """
            query GetUsers($first: Int) {
              allUsers(first: $first) {
                edges {
                    node {
                        id
                        username
                        profile {
                            bio
                        }
                    }
                }
                pageInfo {
                  hasPreviousPage
                  hasNextPage
                }
              }
            }
        """
        result = execute_query(gql_client, query, {"first": 5})
        edges = result["data"]["allUsers"]["edges"]
        page_info = result["data"]["allUsers"]["pageInfo"]

        # Assert: no errors
        assert "errors" not in result, f"Unexpected errors: {result.get('errors')}"

        assert len(edges) == 5

        sorted_edges = sorted(edges, key=lambda x: x["node"]["username"])
        sorted_users = sorted(users, key=lambda x: x.username)

        for edge, user in zip(sorted_edges, sorted_users):
            node = edge["node"]
            assert node["username"] == user.username
            assert UUID(from_global_id(node["id"])[1]) == user.id
            assert node["profile"]["bio"] == user.profile.bio

        assert "hasPreviousPage" in page_info
        assert "hasNextPage" in page_info

        assert isinstance(page_info["hasPreviousPage"], bool)
        assert isinstance(page_info["hasNextPage"], bool)

    def test_query_all_users_empty(self, gql_client, execute_query):
        query = """
            query GetUsers($first: Int) {
              allUsers(first: $first) {
                edges {
                    node {
                        id
                        username
                        profile {
                            bio
                        }
                    }
                }
                pageInfo {
                  hasPreviousPage
                  hasNextPage
                }
              }
            }
        """
        result = execute_query(gql_client, query, {"first": 5})
        errors = result["errors"][0]["message"]
        all_users = result["data"]["allUsers"]

        assert errors == USER_MESSAGES["list_empty"]
        assert all_users is None

    def test_query_all_users_relay_first_and_after(
        self, gql_client, execute_query, user_factory
    ):
        user_factory.create_batch(5)

        query = """
            query GetUsers($first: Int, $after: String) {
              allUsers(first: $first, after: $after) {
                pageInfo {
                  hasNextPage
                  hasPreviousPage
                  startCursor
                  endCursor
                }
                edges {
                  cursor
                  node {
                    id
                    username
                  }
                }
              }
            }
        """

        # First page
        result1 = execute_query(gql_client, query, {"first": 2, "after": None})
        page1 = result1["data"]["allUsers"]
        edges1 = page1["edges"]

        assert len(edges1) == 2
        assert page1["pageInfo"]["hasNextPage"] is True
        assert page1["pageInfo"]["hasPreviousPage"] is False

        end_cursor = page1["pageInfo"]["endCursor"]

        # Second page using `after`
        result2 = execute_query(gql_client, query, {"first": 3, "after": end_cursor})
        page2 = result2["data"]["allUsers"]
        edges2 = page2["edges"]

        assert len(edges2) == 3
        assert page2["pageInfo"]["hasNextPage"] is False
        assert page2["pageInfo"]["hasPreviousPage"] is False

    def test_query_all_users_relay_last_and_before(
        self, gql_client, execute_query, user_factory
    ):
        user_factory.create_batch(5)

        query = """
            query GetUsers($last: Int, $before: String) {
                allUsers(last: $last, before: $before) {
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                    }
                    edges {
                      cursor
                      node {
                        id
                        username
                      }
                    }
                }
            }
        """

        result1 = execute_query(gql_client, query, {"last": 2, "before": None})

        page1 = result1["data"]["allUsers"]
        edges1 = page1["edges"]

        assert len(edges1) == 2
        assert page1["pageInfo"]["hasNextPage"] is False
        assert page1["pageInfo"]["hasPreviousPage"] is True

        end_cursor = page1["pageInfo"]["endCursor"]

        result2 = execute_query(gql_client, query, {"last": 3, "before": end_cursor})
        page2 = result2["data"]["allUsers"]
        edges2 = page2["edges"]

        assert len(edges2) == 3
        assert page2["pageInfo"]["hasNextPage"] is False
        assert page2["pageInfo"]["hasPreviousPage"] is True

    @pytest.mark.parametrize(
        "field, value",
        [
            ("username", "batman_in_gothom"),
            ("email", "batman3003@gmail.com"),
        ],
    )
    def test_query_all_users_filter_with_unique_fields(
        self, gql_client, execute_query, user_factory, field, value
    ):
        # Dynamically create the user with the param field
        user = user_factory(**{field: value})
        user_factory.create_batch(3)

        query = f'''
            query {{
                allUsers({field}: "{value}") {{
                    pageInfo {{
                        hasPreviousPage
                        hasNextPage
                    }}
                    edges {{
                        node {{
                            id
                            username
                            email
                            name
                        }}
                    }}
                }}
            }}
        '''

        result = execute_query(gql_client, query)
        edges = result["data"]["allUsers"]["edges"]
        page_info = result["data"]["allUsers"]["pageInfo"]
        node = edges[0]["node"]
        assert len(edges) == 1

        _, raw_id = from_global_id(node["id"])

        assert node["username"] == user.username
        assert UUID(raw_id) == user.id
        assert node["email"] == user.email
        assert node["name"] == user.name

        assert page_info["hasPreviousPage"] is False
        assert page_info["hasNextPage"] is False

    @pytest.mark.parametrize(
        "field_db, field_gql,value",
        [
            ("name", "name", "Bruse Wayne"),
            ("is_active", "isActive", False),
        ],
    )
    def test_query_all_users_filter_with_related_fields(
        self, gql_client, execute_query, user_factory, field_db, field_gql, value
    ):
        # Create matching and non-matching users
        user_factory(**{field_db: value})
        user_factory.create_batch(2)  # Random user that should not match

        query = f"""
        query {{
            allUsers({field_gql}: {str(value).lower() if isinstance(value, bool) else f'"{value}"'}) {{
                edges {{
                    node {{
                        id
                        username
                        {field_gql}
                    }}
                }}
            }}
        }}
        """

        result = execute_query(gql_client, query)
        nodes = result["data"]["allUsers"]["edges"]

        assert any(node["node"][field_gql] == value for node in nodes)

    @pytest.mark.parametrize(
        "ordering",
        [
            "name",
            "username",  # ascending
            "created_at",
            "-name",
            "-username",  # descending
            "-created_at",
        ],
    )
    def test_query_all_users_order_by_fields(
        self, gql_client, execute_query, user_factory, ordering
    ):
        users = user_factory.create_batch(3)

        query = """
            query GetUsers($first: Int, $orderBy: String) {
              allUsers(first: $first, orderBy: $orderBy) {
                edges {
                    node {
                        id
                        name
                        email
                        username
                    }
                }
                pageInfo {
                  hasPreviousPage
                  hasNextPage
                }
              }
            }
        """
        result = execute_query(gql_client, query, {"first": 3, "orderBy": ordering})
        edges = result["data"]["allUsers"]["edges"]
        page_info = result["data"]["allUsers"]["pageInfo"]

        sorted_users = sorted(
            users,
            key=lambda x: getattr(x, ordering.lstrip("-")),
            reverse=ordering.startswith("-"),
        )

        for user, edge in zip(sorted_users, edges):
            node = edge["node"]
            _, raw_id = from_global_id(node["id"])
            assert UUID(raw_id) == user.id
            assert node["username"] == user.username
            assert node["email"] == user.email
            assert node["name"] == user.name

        assert page_info["hasPreviousPage"] is False
        assert page_info["hasNextPage"] is False


@pytest.mark.django_db
class TestGetUserByIDQueries:
    def test_query_get_user_by_id_success(
        self, gql_client, execute_query, user_factory
    ):
        user = user_factory()
        query = """
            query GetUserByID($userId: ID!) {
                getUserById(userId: $userId) {
                    id
                    email
                    username
                    name
                }
            }
        """
        user_id = to_global_id("UserNode", user.id)

        result = execute_query(gql_client, query, {"userId": user_id})
        user_data = result["data"]["getUserById"]
        _, raw_id = from_global_id(user_id)

        assert UUID(raw_id) == user.id
        assert user_data["email"] == user.email
        assert user_data["username"] == user.username
        assert user_data["name"] == user.name

    def test_query_get_user_by_id_user_dose_not_exist(self, gql_client, execute_query):
        fake_id = to_global_id("UserNode", uuid4())

        query = """
            query GetUserByID($userId: ID!) {
                getUserById(userId: $userId) {
                    id
                    email
                    username
                    name
                }
            }
        """

        result = execute_query(gql_client, query, {"userId": fake_id})
        error_message = result["errors"][0]["message"]
        all_users_none = result["data"]["getUserById"]

        assert error_message == USER_MESSAGES["not_found"]
        assert all_users_none is None

    def test_query_get_user_by_id_user_have_invalid_type_name(
        self, gql_client, execute_query
    ):
        invalid_type_name = "User"
        fake_id = to_global_id(invalid_type_name, uuid4())

        query = """
            query GetUserByID($userId: ID!) {
                getUserById(userId: $userId) {
                    id
                    email
                    username
                    name
                }
            }
        """

        result = execute_query(gql_client, query, {"userId": fake_id})
        error_message = result["errors"][0]["message"]
        all_users_none = result["data"]["getUserById"]

        assert (
            error_message
            == f"Invalid type: expected 'UserNode', got '{invalid_type_name}'"
        )
        assert all_users_none is None


@pytest.mark.django_db
class TestGetUserByUsernameQueries:
    def test_query_get_user_by_username_success(
        self, gql_client, execute_query, user_factory
    ):
        user = user_factory()

        query = """
            query GetUserByUsername($username: String!) {
                getUserByUsername(username: $username) {
                    id
                    email
                    username
                    name
                }
            }
        """

        result = execute_query(gql_client, query, {"username": user.username})
        user_data = result["data"]["getUserByUsername"]

        _, raw_id = from_global_id(user_data["id"])
        assert UUID(raw_id) == user.id
        assert user_data["username"] == user.username
        assert user_data["email"] == user.email
        assert user_data["name"] == user.name

    def test_query_get_user_by_username_user_dose_not_exist(
        self, gql_client, execute_query
    ):
        fake_id = to_global_id("UserNode", uuid4())

        query = """
            query GetUserByUsername($username: String!) {
                getUserByUsername(username: $username) {
                    id
                    email
                    username
                    name
                }
            }
        """

        result = execute_query(gql_client, query, {"username": fake_id})
        error_message = result["errors"][0]["message"]
        get_user_by_username_none = result["data"]["getUserByUsername"]

        assert error_message == USER_MESSAGES["not_found"]
        assert get_user_by_username_none is None
