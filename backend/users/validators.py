from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from typing import List, Callable, Union
from django.core.validators import (
    RegexValidator,
    EmailValidator,
    MinLengthValidator,
    MaxLengthValidator,
)
from datetime import date
import os
import re

# # Accept both class-based and function-based validators
ValidatorType = Union[
    MinLengthValidator,
    MaxLengthValidator,
    RegexValidator,
    EmailValidator,
    Callable[..., None],
]


# *========================================={User Model Validators}======================================================
# * ─────────────── Email Validators ───────────────
# A list of validators to ensure the email is in a proper format.
# Uses Django's built-in EmailValidator.
validate_email: List[EmailValidator] = [
    EmailValidator(message="Enter a valid email address (e.g., user@example.com).")
]
# * ─────────────── Email Validators ───────────────


# * ─────────────── Name Validators ───────────────
def validate_name_strip_whitespace(value: str) -> None:
    """
    Validates that the name does not consist only of whitespace.

    This ensures the name contains actual characters and is not empty
    after stripping spaces. Raises a ValidationError if the value is
    empty or only contains whitespace.
    """
    if not value.strip():
        raise ValidationError("Name cannot be empty or only spaces.")


NAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+$"  # allows accented Letters, spaces, hyphens (-) and apostrophes (').

# * Name (only Letters, spaces, hyphens (-) and apostrophes ('), 2–50 chars)
# - Strips and checks for leading/trailing spaces
# - Must be between 2 and 50 characters
# - Can contain only letters, spaces, hyphens (-), and apostrophes (')
validate_name: List[ValidatorType] = [
    validate_name_strip_whitespace,
    MinLengthValidator(2, message="Name must be at least 2 characters."),
    MaxLengthValidator(50, message="Name cannot exceed 50 characters."),
    RegexValidator(
        regex=NAME_REGEX,
        message="Name can only contain letters, spaces, hyphens (-) and apostrophes (').",
    ),
]
# * ─────────────── Name Validators ───────────────

# * ─────────────── Username Validators ───────────────
USERNAME_REGEX = r"^[a-zA-Z][a-zA-Z0-9._-]+$"  # Starts with a letter, allows only letter, numbers, hyphens (-), Dot (.), Underscore (_).
# A list of validators to enforce rules for the username field.
# - Must be between 3 and 30 characters long.
# - Must start with a letter.
# - Can contain letters, numbers, underscores (_), hyphens (-), and dots (.).
# - Cannot contain consecutive special characters (e.g., "..", "__").
# - Cannot end with a special character.
validate_username: List[ValidatorType] = [
    MinLengthValidator(3, message="Username must be at least 3 characters long."),
    MaxLengthValidator(30, message="Username cannot exceed 30 characters."),
    RegexValidator(
        regex=USERNAME_REGEX,
        message=(
            "Username must start with a letter and can contain letters, numbers, "
            "underscores (_), hyphens (-), and dots (.), without consecutive or trailing special characters."
        ),
    ),
]
# * ─────────────── Username Validators ───────────────

# * ─────────────── Password Validators ───────────────
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[\w@$!%*#?&]+$"


def validate_password(password: str | None) -> None:
    """
    Validates a password according to the following rules:

    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password (str): The password string to validate.

    Raises:
        ValidationError: If the password fails any validation checks.
    """
    errors: List[str] = []

    validators: List[ValidatorType] = [
        MinLengthValidator(8, message="Password must be at least 8 characters long."),
        RegexValidator(
            regex=PASSWORD_REGEX,
            message=(
                "Password must contain at least one uppercase letter, one lowercase letter, "
                "one digit, and one special character."
            ),
        ),
    ]

    for validator in validators:
        try:
            validator(password)
        except ValidationError as e:
            # Collect all messages if multiple exist
            errors.extend(e.messages if hasattr(e, "messages") else [str(e)])

    if errors:
        raise ValidationError(errors)


# * ─────────────── Password Validators ───────────────
# *========================================={User Model Validators}======================================================


# *========================================={Profile Model Validators}===================================================
# * ─────────────── Bio Validators ───────────────
def validate_bio(value: str) -> None:
    """
    Validates that the bio is either empty (optional) or between 2 and 250 characters.

    Args:
        value (str): The biography string to validate.

    Raises:
        ValidationError: If the bio is too short (<2 chars) or too long (>250 chars).
    """
    if not value:
        return  # Allow blank bio (optional field)

    value_length = len(value)

    if value_length < 2:
        raise ValidationError(
            "Your bio is too short. Please enter at least 2 characters."
        )

    if value_length > 250:
        raise ValidationError(
            "Your bio is too long. Please keep it under 250 characters."
        )


def validate_bio_not_numeric_only(value: str) -> None:
    """
    Validates that the biography text is not composed of only numeric characters.

    Args:
        value (str): The biography string to validate.

    Raises:
        ValidationError: If the value contains only digits.
    """
    # Check if the input is a string and contains only digits
    if isinstance(value, str) and re.fullmatch(r"\d+", value):
        raise ValidationError("Bio cannot contain only numbers.")


# * ─────────────── Bio Validators ───────────────


# * ─────────────── Birthday Date Validators ───────────────
def validate_birthday(birthday_date: date) -> None:
    """
    Validates that the given birthday is not in the future and is within a realistic range.

    Args:
        birthday_date (date): The date of birth to validate.

    Raises:
        ValidationError: If the birthday is in the future or unrealistically old (before 1900).
    """
    if birthday_date is None:
        # Skip validation if no date provided (e.g., optional field)
        return

    # Check for unrealistic birthday far in the past
    if birthday_date.year < 1900:
        raise ValidationError("Birthday date is unrealistic — too far in the past.")

    # Ensure birthday is not in the future
    if birthday_date > date.today():
        raise ValidationError("Birthday date cannot be in the future.")


def validate_age_range(birthday_date: date) -> None:
    """
    Validates that the provided birthday indicates an age between 12 and 90 years.

    Args:
        birthday_date (date): The user's date of birth.

    Raises:
        ValidationError: If the age is less than 12 or greater than 90.
    """
    if birthday_date is None:
        # Skip validation if no birthday is provided
        return

    today = date.today()

    # Calculate age accurately by checking if the birthday has occurred this year
    age = (
        today.year
        - birthday_date.year
        - ((today.month, today.day) < (birthday_date.month, birthday_date.day))
    )

    if age < 12:
        raise ValidationError("Too young — must be at least 12 years old.")
    if age > 90:
        raise ValidationError("Too old — must be less than 90 years old.")


# * ─────────────── Birthday Date Validators ───────────────


# * ─────────────── Avatar Validators ───────────────
def validate_image_size(image: UploadedFile) -> None:
    """
    Validates that the uploaded image file does not exceed the maximum allowed size.

    Args:
        image (UploadedFile): The uploaded image file to validate.

    Raises:
        ValidationError: If the image size is missing or exceeds 2MB.
    """
    max_size = 2 * 1024 * 1024  # 2 MB in bytes

    # Ensure image size is present
    if image.size is None:
        raise ValidationError("Avatar file size is missing.")

    # Ensure image size does not exceed 2MB
    if image.size > max_size:
        raise ValidationError("Avatar file size must be under 2MB.")


def validate_image_extension(image: UploadedFile) -> None:
    """
    Validates that the uploaded image has an allowed file extension.

    Allowed extensions:
    - .jpg
    - .jpeg
    - .png

    Args:
        image (UploadedFile): The uploaded image file to validate.

    Raises:
        ValidationError: If the image has no name or has an invalid extension.
    """
    # Ensure the image has a name before checking its extension
    if not image.name:
        raise ValidationError("Image file name is missing.")

    # Extract and normalize the file extension
    ext = os.path.splitext(image.name)[1].lower()

    # List of allowed file extensions
    allowed_extensions = [".jpg", ".jpeg", ".png"]

    if ext not in allowed_extensions:
        raise ValidationError("Only JPG, PNG and JPEG files are allowed.")


# * ─────────────── Avatar Validators ───────────────

# *========================================={Profile Model Validators}===================================================
