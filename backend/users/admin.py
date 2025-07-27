from typing import Any, Optional

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.http import HttpRequest
from django.utils.html import format_html

from .models import Profile, User
from .validators import validate_password


class CustomUserCreationForm(forms.ModelForm):  # type: ignore
    """
    A custom form for creating new users with password validation.

    This form includes:
    - Email, username, and name fields (from the User model).
    - Password and confirm password fields.
    - Validation for matching passwords and password strength.
    """

    password: forms.CharField = forms.CharField(
        label="Password", widget=forms.PasswordInput
    )
    confirm_password: forms.CharField = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("email", "username", "name")

    def clean_confirm_password(self) -> str | None:
        """
        Ensure the two password fields match.

        Raises:
            ValidationError: if passwords do not match.

        Returns:
            str: The confirmed password.

        """
        password: str | None = self.cleaned_data.get("password")
        confirm_password: str | None = self.cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password

    def clean_password(self) -> str | None:
        """
        Run Django's built-in password validators.

        Returns:
            str: The validated password.

        """
        password: str | None = self.cleaned_data.get("password")
        validate_password(password)
        return password

    def save(self, commit: bool = True) -> User:
        """
        Save the user instance with a hashed password.

        Args:
            commit (bool): Whether to save the instance to the database.

        Returns:
            User: The saved user instance.

        """
        user: User = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):  # type: ignore
    """
    A custom form used in the admin interface to update existing users.

    This form:
    - Displays a read-only hash of the user's password (not editable).
    - Allows updating email, username, name, is_active, and is_staff fields.
    """

    password: ReadOnlyPasswordHashField = ReadOnlyPasswordHashField(
        label="Password",
        help_text=(
            "Raw passwords are not stored, so there is no way to see this user’s password, "
            'but you can change the password using <a href="../password/">this form</a>.'
        ),
    )

    class Meta:
        model = User
        fields = ("email", "username", "name", "password", "is_active", "is_staff")

    def clean_password(self) -> str | Any:
        """
        Return the initial password value regardless of what the user submits.

        This prevents the hashed password from being changed through the form.

        Returns:
            str: The initial password hash.

        """
        return self.initial["password"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):  # type: ignore
    """
    Custom admin interface for the User model.

    This admin:
    - Uses custom forms for user creation and update.
    - Configures list display, filters, field grouping, and ordering.
    """

    form = CustomUserChangeForm  # Used when updating a user
    add_form = CustomUserCreationForm  # Used when creating a new user

    # Fields to display in the user list in admin panel
    list_display = ("email", "username", "name", "is_staff", "is_active")

    # Filters shown in the right sidebar
    list_filter = ("is_staff", "is_active")

    # Field layout when viewing/updating a user in admin
    fieldsets = (
        (None, {"fields": ("email", "username", "name", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    # Field layout when adding a new user via the admin
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),  # Adds wider layout styling
                "fields": (
                    "email",
                    "username",
                    "name",
                    "password",
                    "confirm_password",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    search_fields = ("email", "username")  # Fields searchable in admin
    ordering = ("email",)  # Default ordering in list view


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):  # type: ignore
    """
    Custom admin interface for managing Profile instances.
    """

    # Fields to display in the list view
    list_display = (
        "user_email",
        "user_username",
        "avatar_preview",
        "birthday_date",
        "created_at",
        "updated_at",
    )

    # Enable search by related user fields
    search_fields = ("user__email", "user__username", "user__name")

    # Make fields read-only
    readonly_fields = ("avatar_preview", "created_at", "updated_at")

    @admin.display(description="User Email")
    def user_email(self, obj: Profile) -> str:
        """
        Display user's email in the list view.

        :param obj: Profile instance
        :return: Email of the related user
        """
        return obj.user.email

    @admin.display(description="Username")
    def user_username(self, obj: Profile) -> str:
        """
        Display user's username in the list view.

        :param obj: Profile instance
        :return: Username of the related user
        """
        return obj.user.username

    @admin.display(description="Avatar")
    def avatar_preview(self, obj: Profile) -> str:
        """
        Display a small circular preview of the avatar image.

        :param obj: Profile instance
        :return: HTML string with the avatar or a dash if not available
        """
        if obj.avatar:
            return format_html(
                '<img src="{}" style="'
                "height: 32px; "
                "width: 32px; "
                "object-fit: cover; "
                "border-radius: 50%; "
                'box-shadow: 0 0 2px #888;" '
                "/>",
                obj.avatar.url,
            )
        return "-"

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Profile] = None
    ) -> bool:
        """
        Disable delete functionality from the admin interface.

        :param request: Admin request
        :param obj: Optional Profile object
        :return: Always False to disable deletion
        """
        return False

    def get_actions(self, request: HttpRequest):  # type: ignore
        """
        Remove the 'delete selected' action from the admin list view.

        :param request: HttpRequest object from the admin interface
        :return: A dictionary of remaining available admin actions
        """
        actions = super().get_actions(request)

        if "delete_selected" in actions:
            del actions["delete_selected"]

        return actions
