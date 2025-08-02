import pytest
from graphql import GraphQLError
from users.models import UserRole
from users.permissions import (
    Permissions,
    admin_required,
    user_required,
    creator_required,
    moderator_required,
    reviewer_required,
    owner_required,
    permission_required,
)


@pytest.mark.django_db
class TestPermissionRequiredDecorator:
    @permission_required(Permissions.VIEW_USER)
    def dummy_resolver(self, info, *args, **kwargs):
        return "permission granted"

    def test_permission_required_permission_granted(
        self, user_with_permissions, graphql_context
    ):
        user = user_with_permissions(Permissions.VIEW_USER)
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_resolver(info)
        assert result == "permission granted"

    def test_permission_required_permission_denied(
        self, user_with_permissions, graphql_context
    ):
        user = user_with_permissions(Permissions.DELETE_USER)
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        with pytest.raises(GraphQLError) as graphql_error:
            self.dummy_resolver(info)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert (
            error
            == f"Access Denied: Missing required permission '{Permissions.VIEW_USER.value}'."
        )
        assert extensions["code"] == "FORBIDDEN"
        assert extensions["required_permission"] == Permissions.VIEW_USER.value

    def test_permission_required_permission_user_has_no_permissions(
        self, user_factory, graphql_context
    ):
        user = user_factory()
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        with pytest.raises(GraphQLError) as graphql_error:
            self.dummy_resolver(info)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert (
            error
            == f"Access Denied: Missing required permission '{Permissions.VIEW_USER.value}'."
        )
        assert extensions["code"] == "FORBIDDEN"
        assert extensions["required_permission"] == Permissions.VIEW_USER.value


@pytest.mark.django_db
class TestRoleBasedAccessDecorators:
    @user_required
    def dummy_user_required_resolver(self, info, *args, **kwargs):
        return "Access granted to USER"

    @reviewer_required
    def dummy_reviewer_required_resolver(self, info, *args, **kwargs):
        return "Access granted to REVIEWER"

    @creator_required
    def dummy_creator_required_resolver(self, info, *args, **kwargs):
        return "Access granted to CREATOR"

    @moderator_required
    def dummy_moderator_required_resolver(self, info, *args, **kwargs):
        return "Access granted to MODERATOR"

    @admin_required
    def dummy_admin_required_resolver(self, info, *args, **kwargs):
        return "Access granted to ADMIN"

    def test_user_required_access_granted(self, user_factory, graphql_context):
        user = user_factory()
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_user_required_resolver(info)
        assert result == "Access granted to USER"

    def test_reviewer_required_access_granted(self, user_factory, graphql_context):
        user = user_factory(role=UserRole.REVIEWER)
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_reviewer_required_resolver(info)
        assert result == "Access granted to REVIEWER"

    def test_creator_required_access_granted(self, user_factory, graphql_context):
        user = user_factory(role=UserRole.CREATOR)
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_creator_required_resolver(info)
        assert result == "Access granted to CREATOR"

    def test_moderator_required_access_granted(self, user_factory, graphql_context):
        user = user_factory(role=UserRole.MODERATOR)
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_moderator_required_resolver(info)
        assert result == "Access granted to MODERATOR"

    def test_admin_required_access_granted(self, user_factory, graphql_context):
        user = user_factory(role=UserRole.ADMIN)
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_admin_required_resolver(info)
        assert result == "Access granted to ADMIN"

    def test_role_required_access_denied(self, user_factory, graphql_context):
        user = user_factory()  # by defualt USER Role
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        with pytest.raises(GraphQLError) as graphql_error:
            self.dummy_admin_required_resolver(info)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions
        expected_error = (
            f"Access denied. Your role '{UserRole.USER.value}' "
            f"is not authorized for this action. Allowed roles: {UserRole.ADMIN.value}."
        )

        assert error == expected_error
        assert extensions["code"] == "FORBIDDEN"
        assert extensions["user_role"] == UserRole.USER.value
        assert extensions["allowed_roles"] == [UserRole.ADMIN.value]

    def test_graphql_login_rquired_access_denied(
        self, unauthenticated_info, graphql_context
    ):
        with pytest.raises(GraphQLError) as graphql_error:
            self.dummy_admin_required_resolver(unauthenticated_info)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions
        assert (
            error
            == "Authentication Required: You must be logged in to perform this action."
        )
        assert extensions["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
class TestOwnerRequiredDecorators:
    @owner_required(lambda self, info, *args, **kwargs: kwargs["user_id"])
    def dummy_resolver(self, info, *args, **kwargs):
        return "Access granted to USER"

    def test_owner_required_access_granted(self, user_factory, graphql_context):
        user = user_factory()
        context = graphql_context(user)
        info = type("Info", (), {"context": context})

        result = self.dummy_resolver(info, None, user_id=user.id)
        assert result == "Access granted to USER"

    def test_owner_required_unauthenticated(
        self, user_factory, unauthenticated_info, graphql_context
    ):
        user = user_factory()
        with pytest.raises(GraphQLError) as graphql_error:
            self.dummy_resolver(unauthenticated_info, None, user_id=user.id)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert (
            error
            == "Authentication Required: You must be logged in to access this resource."
        )
        assert extensions["code"] == "UNAUTHENTICATED"

    def test_owner_required_wrong_user(self, user_factory, graphql_context):
        owner = user_factory()
        other_user = user_factory()

        context = graphql_context(other_user)
        info = type("Info", (), {"context": context})

        with pytest.raises(GraphQLError) as graphql_error:
            self.dummy_resolver(info, None, user_id=owner.id)

        error = graphql_error.value.message
        extensions = graphql_error.value.extensions

        assert (
            error
            == "Access Denied: This resource belongs to another user. You are not authorized to access it."
        )
        assert extensions["code"] == "FORBIDDEN"
        assert extensions["reason"] == "NOT_RESOURCE_OWNER"

    def test_owner_required_admin_bypass(self, user_factory, graphql_context):
        admin = user_factory(role="admin")
        target_user = user_factory()

        context = graphql_context(admin)
        info = type("Info", (), {"context": context})

        result = self.dummy_resolver(info, None, user_id=target_user.id)
        assert result == "Access granted to USER"
