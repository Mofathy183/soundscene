import pytest
from users.utility import USER_MESSAGES


@pytest.mark.django_db
class TestSignUpMutation:
    def test_signup_success(self, gql_client, execute_query, user_factory):
        user_password = "PassW0rd122?!"
        user = user_factory.build()
        query = """
            mutation SignUp(
                $email: String!, 
                $username: String!,
                $name: String!,
                $password: String!,
                $confirm_password: String! 
            ) {
                signUp(
                    email: $email,
                    username: $username,
                    name: $name,
                    password: $password,
                    confirmPassword: $confirm_password
                ) {
                    user {
                        id
                        email
                        username
                        name
                        profile {
                            bio
                        }
                    }
                    success 
                    message
                }
            }
        """

        result = execute_query(
            gql_client,
            query,
            {
                "email": user.email,
                "username": user.username,
                "name": user.name,
                "password": user_password,
                "confirm_password": user_password,
            },
        )

        user_signed = result["data"]["signUp"]["user"]
        success = result["data"]["signUp"]["success"]
        message = result["data"]["signUp"]["message"]

        assert user_signed["id"] is not None
        assert user_signed["email"] == user.email
        assert user_signed["username"] == user.username
        assert user_signed["name"] == user.name
        # if the user have profile after sign him up
        assert isinstance(user_signed["profile"], dict)
        assert "bio" in user_signed["profile"]

        assert success is True
        assert message == USER_MESSAGES["signup_success"]

    @pytest.mark.parametrize(
        "missing_field", ["email", "username", "password", "confirm_password", "name"]
    )
    def test_signup_missing_required_field(
        self, gql_client, execute_query, user_factory, missing_field
    ):
        user_password = "PassW0rd122?!"
        user = user_factory.build()
        variables = {
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "password": user_password,
            "confirm_password": user_password,
        }
        variables.pop(missing_field)

        query = """
            mutation SignUp(
                $email: String, 
                $username: String,
                $name: String,
                $password: String,
                $confirm_password: String 
            ) {
                signUp(
                    email: $email,
                    username: $username,
                    name: $name,
                    password: $password,
                    confirmPassword: $confirm_password
                ) {
                    user {
                        id
                        email
                        username
                        name
                        profile {
                            bio
                        }
                    }
                    success 
                    message
                }
            }
        """

        result = execute_query(gql_client, query)

        assert "errors" in result
        assert any(missing_field in err["message"] for err in result["errors"])

    def test_signup_send_access_and_refresh_token_via_cookies(
        self, graphql_post, user_factory
    ):
        user_password = "PassW0rd122?!"
        user = user_factory.build()

        query = """
            mutation SignUp(
                $email: String!, 
                $username: String!,
                $name: String!,
                $password: String!,
                $confirm_password: String! 
            ) {
                signUp(
                    email: $email,
                    username: $username,
                    name: $name,
                    password: $password,
                    confirmPassword: $confirm_password
                ) {
                    user {
                        id
                        email
                        username
                        name
                        profile {
                            bio
                        }
                    }
                    success 
                    message
                }
            }
        """

        variables = {
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "password": user_password,
            "confirm_password": user_password,
        }

        response = graphql_post(query, variables)
        cookies = response.cookies

        assert "access_token" in cookies, "access_token cookie not found in response"
        assert "refresh_token" in cookies, "refresh_token cookie not found in response"
        assert "csrftoken" in cookies, "csrftoken cookie not found in response"


@pytest.mark.django_db
class TestLoginMutation:
    def test_login_success(self, gql_client, execute_query, user_factory):
        user_password = "PassW0rd122?!"
        user = user_factory()

        query = """
           mutation LoginUser($email: String!, $password: String!) {
              login(
                email:$email,
                password:$password
              ){
                user{ 
                    id
                    name
                    username
                    email
                    profile{
                        bio
                    }
                }
                message
                success
              }
            }
        """

        result = execute_query(
            gql_client, query, {"email": user.email, "password": user_password}
        )

        user_login = result["data"]["login"]["user"]
        message = result["data"]["login"]["message"]
        success = result["data"]["login"]["success"]

        assert user_login["id"] is not None
        assert user_login["email"] == user.email
        assert user_login["username"] == user.username
        assert user_login["name"] == user.name

        assert isinstance(user_login["profile"], dict)
        assert "bio" in user_login["profile"]

        assert success is True
        assert message == USER_MESSAGES["login_success"]

    @pytest.mark.parametrize("missing_field", ["email", "password"])
    def test_login_missing_field(
        self, gql_client, execute_query, user_factory, missing_field
    ):
        user_password = "PassW0rd122?!"
        user = user_factory.build()
        variables = {
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "password": user_password,
            "confirm_password": user_password,
        }
        variables.pop(missing_field)

        query = """
           mutation LoginUser($email: String!, $password: String!) {
              login(
                email:$email,
                password:$password
              ){
                user{ 
                    id
                    name
                    username
                    email
                    profile{
                        bio
                    }
                }
                message
                success
              }
            }
        """

        result = execute_query(gql_client, query, variables)

        assert "errors" in result
        assert any(missing_field in err["message"] for err in result["errors"])

    def test_login_send_access_and_refresh_token_via_cookies(
        self, graphql_post, user_factory
    ):
        user_password = "PassW0rd122?!"
        user = user_factory()

        query = """
           mutation LoginUser($email: String!, $password: String!) {
              login(
                email:$email,
                password:$password
              ){
                user{ 
                    id
                    name
                    username
                    email
                    profile{
                        bio
                    }
                }
                message
                success
              }
            }
        """

        variables = {
            "email": user.email,
            "password": user_password,
        }

        response = graphql_post(query, variables)
        cookies = response.cookies

        assert "access_token" in cookies, "access_token cookie not found in response"
        assert "refresh_token" in cookies, "refresh_token cookie not found in response"
        assert "csrftoken" in cookies, "csrftoken cookie not found in response"
