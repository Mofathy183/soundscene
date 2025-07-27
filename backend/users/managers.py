from __future__ import annotations  # Postpone evaluation of annotations

from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from .models import (
        User,
    )  # Only for static type checking (won’t be imported at runtime)


class UserManager(BaseUserManager["User"]):
    """
    Custom user model manager that uses email as the unique identifier
    instead of a traditional username.
    """

    def create_user(
        self,
        email: str,
        username: str,
        name: str,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> User:
        """
        Create and return a regular user with the given email, username, name, and password.

        Args:
            email (str): The user's email address.
            username (str): The user's username.
            name (str): The user's full name.
            password (str, optional): The user's raw password.
            **extra_fields: Any additional fields to include.

        Returns:
            User: The created user instance.

        Raises:
            ValueError: If email is not provided.

        """
        if not email:
            raise ValueError(_("The Email field must be set."))

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            name=name,
            **extra_fields,
        )
        user.set_password(password)  # Hash the password
        user.save(using=self._db)  # Save using the default DB alias
        return user

    def create_superuser(
        self, email: str, username: str, name: str, password: str, **extra_fields: Any
    ) -> User:
        """
        Create and return a superuser with admin privileges.

        Args:
            email (str): The superuser's email address.
            username (str): The superuser's username.
            name (str): The superuser's full name.
            password (str): The superuser's raw password.
            **extra_fields: Additional fields (e.g., is_staff, is_superuser).

        Returns:
            User: The created superuser instance.

        Raises:
            ValueError: If required superuser flags are not set.

        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, username, name, password, **extra_fields)

    def get_by_natural_key(self, email: str | None) -> User:
        """
        Return a user matched by email (case-insensitive),
        allowing it to act as the natural key for authentication.

        Args:
            email (str): The email address used for authentication.

        Returns:
            User: The matched user instance.

        Raises:
            ValueError: If email is not provided.

        """
        if not email:
            raise ValueError(_("The Email field must be set."))

        return self.get(email__iexact=email)
