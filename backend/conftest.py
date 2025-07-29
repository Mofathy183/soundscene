"""
conftest.py for setting up common test configurations and fixtures.

- Registers user and profile factories for pytest-factoryboy.
- Overrides Django settings (e.g., password hasher and media root) for testing.
"""

import shutil
import tempfile
from collections.abc import Generator
from typing import Any
import pytest
from django.conf import settings  # noqa: F401
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
def gql_client():
    return Client(schema)


@pytest.fixture
def execute_query():
    def _execute(client, query, variables=None):
        return client.execute(query, variables=variables)

    return _execute


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
