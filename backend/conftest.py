"""
conftest.py for setting up common test configurations and fixtures.

- Registers user and profile factories for pytest-factoryboy.
- Overrides Django settings (e.g., password hasher and media root) for testing.
"""

import tempfile
import shutil
import pytest
from django.conf import settings  # noqa: F401
from typing import Any, Generator

# Register factories for pytest-factoryboy
pytest_plugins = ["pytest_factoryboy"]
# from pytest_factoryboy import register  # noqa: E402 (placed after pytest_plugins for clarity)

# from users.tests.factories import UserFactory, ProfileFactory

# * Register the factories
# register(UserFactory)
# register(ProfileFactory)


@pytest.fixture(autouse=True)
def set_fast_password_hasher(django_settings: Any) -> None:
    """
    Fixture to speed up password hashing during tests.
    Uses MD5 hasher (insecure, but fast), since security is not needed in tests.
    Applied automatically to all tests.
    """
    django_settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


@pytest.fixture(autouse=True, scope="function")
def temp_media_root(django_settings: Any) -> Generator[None, None, None]:
    """
    Fixture to override Django's MEDIA_ROOT to a temporary directory.
    Ensures all uploaded media (e.g. avatars, files) are saved in a temp folder
    and cleaned up after each test.
    """
    temp_dir = tempfile.mkdtemp()
    django_settings.MEDIA_ROOT = temp_dir
    yield
    shutil.rmtree(temp_dir)
