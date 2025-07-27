import uuid
from datetime import date
from typing import Dict, Optional, Tuple

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone

from .managers import UserManager
from .utility import profile_avatar_path
from .validators import (
    validate_age_range,
    validate_bio,
    validate_bio_not_numeric_only,
    validate_birthday,
    validate_email,
    validate_image_extension,
    validate_image_size,
    validate_name,
    validate_username,
)


class UserRole(models.TextChoices):
    """
    Enum-like class defining the various user roles in the system.

    This class is based on Django's `TextChoices`, which allows storing string-based
    values in the database while using Python enums for cleaner logic in code.
    """

    USER = "user", "User"  # Regular user with basic access and permissions.
    CREATOR = (
        "creator",
        "Creator",
    )  # Content creator role with permissions to upload or manage their own content.
    REVIEWER = (
        "reviewer",
        "Reviewer",
    )  # Role for users who can review and give feedback on content.
    MODERATOR = (
        "moderator",
        "Moderator",
    )  # Moderator role with elevated permissions to manage user-generated content.
    ADMIN = (
        "admin",
        "Admin",
    )  # Full admin privileges, typically for managing the platform.

    # You can access the values like:
    # - UserRole.ADMIN (enum)
    # - UserRole.ADMIN.label -> "Admin"
    # - UserRole.ADMIN.value -> "admin"


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email as the unique identifier
    instead of username. Includes roles, timestamps, and indexing
    for performance optimization.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Primary key: Unique user ID as UUID",
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name="Email Address",
        validators=validate_email,
        help_text="User's unique email address",
    )

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=validate_username,
        verbose_name="Username",
        help_text="Unique username for login and display",
    )

    name = models.CharField(
        max_length=50,
        validators=validate_name,
        verbose_name="Full Name",
        help_text="User's full display name",
    )

    password = models.CharField(
        max_length=100, verbose_name="Password", help_text="Hashed user password"
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        help_text="Role assigned to the user",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Set to False to deactivate the account instead of deleting it",
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff Status",
        help_text="Designates whether the user can access the admin site",
    )

    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date Joined",
        help_text="Timestamp when the user joined",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        null=True,
        blank=True,
        help_text="Timestamp of user creation",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        null=True,
        blank=True,
        help_text="Timestamp of last update",
    )

    # Set the custom manager
    objects = UserManager()

    # Authentication configuration
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]

    def __str__(self) -> str:
        """String representation of the user instance."""
        return f"{self.username}"

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["name", "id"]),
            models.Index(fields=["email", "id"]),
            models.Index(fields=["username", "id"]),
            models.Index(fields=["created_at", "id"]),
        ]


class Profile(models.Model):
    """
    Stores additional user-related information beyond the base `User` model.
    This includes bio, avatar, birthday, and computed age. Each Profile is linked
    to a single User through a one-to-one relationship.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Universally unique identifier for the profile.",
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="User",
        help_text="The user associated with this profile.",
    )

    bio = models.TextField(
        blank=True,
        default="",
        verbose_name="Biography",
        help_text="A short personal description or introduction.",
        validators=[validate_bio, validate_bio_not_numeric_only],
    )

    birthday_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Birthday",
        help_text="User's date of birth (optional).",
        validators=[validate_birthday, validate_age_range],
    )

    avatar = models.ImageField(
        upload_to=profile_avatar_path,
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Optional user profile image (JPG, PNG).",
        validators=[validate_image_size, validate_image_extension],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        null=True,
        blank=True,
        help_text="Timestamp when the profile was created.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        null=True,
        blank=True,
        help_text="Timestamp when the profile was last updated.",
    )

    def delete(
        self, using: Optional[str] = None, keep_parents: bool = False
    ) -> Tuple[int, Dict[str, int]]:
        """
        Prevent direct deletion of a profile instance.
        Users should be deleted instead, which cascades to the profile.
        """
        raise PermissionDenied(
            "You cannot delete a profile directly. Delete the user instead."
        )

    @property
    def age(self) -> Optional[int]:
        """
        Calculate the age of the user based on their birthday.

        Returns:
            int: User's age if birthday is set, else None.

        """
        if not self.birthday_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birthday_date.year
            - (
                (today.month, today.day)
                < (self.birthday_date.month, self.birthday_date.day)
            )
        )

    def __str__(self) -> str:
        """
        String representation of the Profile model.

        Returns:
            str: User's full name with "'s profile".

        """
        return f"{self.user.name}'s profile"

    class Meta:
        db_table = "profile"
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["created_at", "id"]),
            models.Index(fields=["birthday_date", "id"]),
            models.Index(fields=["updated_at", "id"]),
        ]
