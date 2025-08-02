"""
conftest.py for setting up common test configurations and fixtures.

- Registers user and profile factories for pytest-factoryboy.
- Overrides Django settings (e.g., password hasher and media root) for testing.
"""

import shutil
import tempfile
import json
from collections.abc import Generator
from typing import Any, Dict, Callable
from types import SimpleNamespace
import pytest
from django.conf import settings  # noqa: F401
from django.test import Client as DjangoClient


from users.models import User
from django.contrib.auth.models import Permission
from users.permissions import Permissions as EnumPermissions
from users.tests.factories import ProfileFactory, UserFactory
from gql.schema import schema
from graphene.test import Client
from pytest_factoryboy import (
    register,
)

# Register factories for pytest-factoryboy
pytest_plugins = ["pytest_factoryboy"]

# * Register the factories
register(UserFactory)
register(ProfileFactory)


@pytest.fixture
def unauthenticated_info():
    """
    Fixture that returns a mock GraphQL `info` object for an unauthenticated user.

    Useful for testing authentication guards like `graphql_login_required`,
    where the user must be logged in.

    Returns:
        info (object): A dummy GraphQL resolve info with an unauthenticated user.
    """

    class AnonymousUser:
        is_authenticated = False
        role = None  # Optional: Only needed if role-based checks exist

    class DummyContext:
        user = AnonymousUser()

    info = SimpleNamespace(context=DummyContext())
    return info


@pytest.fixture
def user_with_permissions(db) -> Callable[[EnumPermissions], User]:
    """
    Returns a callable that creates a user with the specified permission.

    Args:
        permission (EnumPermissions): A value from the Permissions enum.

    Returns:
        User: A user instance with the specified permission.
    """

    def _make(permission: EnumPermissions) -> User:
        user = UserFactory()
        app_label, codename = permission.value.split(".")
        perm = Permission.objects.get(
            content_type__app_label=app_label, codename=codename
        )
        user.user_permissions.add(perm)
        return user

    return _make


@pytest.fixture
def graphql_context() -> Callable[[User], Dict[str, Any]]:
    """
    Returns a simulated GraphQL context object for a given user.
    Usage:
        context = graphql_context(user)
        info = type("Info", (), {"context": context})
    """

    def _make(user: User) -> Any:
        class DummyContext:
            def __init__(self, user: User):
                self.user = user

        return DummyContext(user)

    return _make


@pytest.fixture
def gql_client():
    return Client(schema)


@pytest.fixture
def execute_query():
    def _execute(client, query, variables=None):
        return client.execute(query, variables=variables)

    return _execute


@pytest.fixture
def graphql_post():
    """
    A reusable fixture to execute a GraphQL POST request using Django's test client.
    Returns a function that accepts query and variables.
    """
    client = DjangoClient()

    def _post(query: str, variables: Dict) -> any:
        response = client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": variables}),
            content_type="application/json",
        )
        return response

    return _post


@pytest.fixture(autouse=True)
def set_fast_password_hasher(settings: Any) -> None:  # noqa: F811
    """
    Fixture to speed up password hashing during tests.
    Uses MD5 hasher (insecure, but fast), since security is not needed in tests.
    Applied automatically to all tests.
    """
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


@pytest.fixture(autouse=True, scope="function")
def temp_media_root(settings: Any) -> Generator[None, None, None]:  # noqa: F811
    """
    Fixture to override Django's MEDIA_ROOT to a temporary directory.
    Ensures all uploaded media (e.g. avatars, files) are saved in a temp folder
    and cleaned up after each test.
    """
    temp_dir = tempfile.mkdtemp()
    settings.MEDIA_ROOT = temp_dir
    yield
    shutil.rmtree(temp_dir)
