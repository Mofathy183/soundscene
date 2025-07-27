from typing import Any, Dict, Optional, Union

from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from .models import Profile, User
from .validators import (
    validate_age_range,
    validate_bio,
    validate_birthday,
    validate_email,
    validate_image_extension,
    validate_image_size,
    validate_name,
    validate_password,
    validate_username,
)


class UserSerializer(serializers.ModelSerializer):  # type: ignore
    """
    Serializer for the User model used during registration.
    Includes validation for email, username, name, and password.
    """

    email = serializers.EmailField(
        required=True, validators=[validate_email], help_text="User email address."
    )
    username = serializers.CharField(
        required=True,
        validators=[validate_username],
        trim_whitespace=True,
        help_text="Unique username for the user.",
    )
    name = serializers.CharField(
        required=True,
        validators=[validate_name],
        trim_whitespace=True,
        help_text="Full name of the user.",
    )
    password = serializers.CharField(
        required=True,
        validators=[validate_password],
        write_only=True,
        help_text="Password (write-only).",
    )
    confirm_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        write_only=True,
        help_text="Password confirmation (write-only).",
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "name",
            "password",
            "confirm_password",
        ]
        read_only_fields = (
            "id",
            "date_joined",
            "last_login",
            "updated_at",
            "created_at",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the serializer input:
        - Ensure that password and confirm_password match.
        """
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        """
        Create and return a new user after removing confirm_password.
        """
        validated_data.pop("confirm_password", None)
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):  # type: ignore
    """
    Serializer for the Profile model.

    This handles serialization and validation of user profile data,
    including bio, birthday, avatar, and calculated age.
    """

    user = UserSerializer(read_only=True)
    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_bio],
        help_text="A short personal description or introduction.",
        trim_whitespace=True,
    )
    birthday_date = serializers.DateField(
        required=False,
        allow_null=True,
        validators=[validate_birthday, validate_age_range],
        help_text="Date of birth. Must be between 12 and 90 years old.",
    )
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_size, validate_image_extension],
        help_text="JPG or PNG image under 2MB.",
    )
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "bio",
            "birthday_date",
            "avatar",
            "age",
        ]
        read_only_fields = ("id", "age", "user")

    def validate_avatar(
        self, avatar: Union[UploadedFile, None]
    ) -> Union[UploadedFile, None]:
        """
        Validate the uploaded avatar image for size and extension.

        This method ensures that the uploaded file meets the required image size and file format constraints.
        If the validation fails, it raises a `ValidationError`.

        Args:
            avatar (UploadedFile | None): The uploaded avatar file.

        Returns:
            UploadedFile | None: The validated avatar file if valid.

        """
        if avatar is not None:
            # Validate image size and extension
            validate_image_size(avatar)
            validate_image_extension(avatar)

        return avatar

    def get_age(self, obj: Any) -> Optional[int]:
        """
        Return the age of the user based on their birthday date.

        If the user's `birthday_date` is not provided or the `age` attribute
        is not present, this method will return None.

        Args:
            obj (Any): The user instance or object containing the 'age' attribute.

        Returns:
            Optional[int]: The age of the user, or None if not available.

        """
        # Return the age attribute if it exists; otherwise return None
        return getattr(obj, "age", None)
