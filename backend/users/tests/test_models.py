import factory
import pytest
import os
import uuid
from datetime import datetime, date, timedelta
from django.core.exceptions import ValidationError, PermissionDenied
from users.models import User, Profile
from .factories import UserFactory, ProfileFactory
from django.db.models.signals import post_save
from .testHelper import enable_signal, disable_signals_create_user_profile  # noqa: F401
from users.validators import validate_image_size, validate_image_extension
from django.core.files.uploadedfile import SimpleUploadedFile

TODAY = date.today()


@pytest.fixture
def user():
    return UserFactory()


@pytest.mark.skip(reason="Finsh testing")
@pytest.mark.usefixtures("disable_signals_create_user_profile")
@pytest.mark.django_db
class TestUserModel:
    def test_user_creation_for_uuid_is_generate(self, user):
        assert isinstance(user.id, uuid.UUID)

    def test_user_creation_for_username_is_unique(self, user):
        user_two = UserFactory.build(username=user.username)
        with pytest.raises(ValidationError):
            user_two.validate_unique()

    def test_user_password_is_hashed_not_plain(self, user):
        assert user.password != "PassW0rd122?!"
        assert user.check_password("PassW0rd122?!")

    def test_user_name_is_str(self, user):
        assert isinstance(user.name, str)

    def test_user_default_flags(self, user):
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active

    def test_user_timestamps_are_set(self, user):
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_str_returns_username(self, user):
        assert str(user) == user.username


@pytest.fixture()
def profile():
    with factory.django.mute_signals(post_save):
        return ProfileFactory()


@pytest.mark.skip(reason="Finsh testing")
@pytest.mark.django_db
@pytest.mark.usefixtures("disable_signals_create_user_profile")
class TestProfileModel:
    def test_profile_creation_for_uuid_is_generate(self, profile):
        assert profile.id is not None
        assert isinstance(profile.id, uuid.UUID)

    def test_profile_creation_for_profile_have_user(self, profile):
        assert profile.user is not None
        assert isinstance(profile.user, User)

    def test_profile_birthday_date_and_age(self, profile):
        assert isinstance(profile.birthday_date, date)
        assert isinstance(profile.age, int)
        assert 12 <= profile.age <= 90

    def test_profile_bio_is_string(self, profile):
        assert isinstance(profile.bio, str)
        assert len(profile.bio) > 0

    def test_profile_timestamps_are_set(self, profile):
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)

    def test_profile_str_returns_username(self, profile):
        assert str(profile) == f"{profile.user.name}'s profile"

    def test_signal_creates_profile_for_user(self, enable_signal):  # noqa: F811
        with enable_signal("post_save"):
            user = UserFactory()

        assert hasattr(user, "profile")
        assert isinstance(user.profile, Profile)

    def test_delete_user_profile_without_delete_user(self, enable_signal):  # noqa: F811
        with enable_signal("post_save"):
            user = UserFactory()

        with pytest.raises(PermissionDenied) as e:
            user.profile.delete()

        assert (
            str(e.value)
            == "You cannot delete a profile directly. Delete the user instead."
        )

    def test_delete_avatar_file_on_delete_profile_by_singals_post_delete(
        self,
        enable_signal,  # noqa: F811
    ):
        avatar = SimpleUploadedFile(
            "avatar.jpg", b"avatar-data", content_type="image/jpeg"
        )

        with enable_signal("post_save"):
            user = UserFactory()

        profile = user.profile
        profile.avatar = avatar
        profile.save()

        avatar_path = profile.avatar.path
        assert os.path.isfile(avatar_path)

        with enable_signal("post_delete"):  # ✅ corrected from "pre_delete"
            user.delete()

        assert not os.path.isfile(avatar_path)

        with pytest.raises(Profile.DoesNotExist):
            Profile.objects.get(id=profile.id)

    def test_delete_old_avatar_file_on_update_to_new_avatar(self, enable_signal):  # noqa: F811
        avatar1 = SimpleUploadedFile(
            "avatar1.jpg", b"first-avatar", content_type="image/jpeg"
        )

        with enable_signal("post_save"):
            user = UserFactory()

        profile = user.profile
        profile.avatar = avatar1
        profile.save()

        old_avatar_path = profile.avatar.path
        assert os.path.isfile(old_avatar_path)

        avatar2 = SimpleUploadedFile(
            "avatar2.jpg", b"second-avatar", content_type="image/jpeg"
        )
        profile.avatar = avatar2

        with enable_signal("pre_save"):  # ✅ corrected from "post_delete"
            profile.save()

        new_avatar_path = profile.avatar.path

        assert not os.path.isfile(old_avatar_path)
        assert os.path.isfile(new_avatar_path)


# *===================================={Test Model-Level Validators}================================================


@pytest.mark.skip(reason="Finsh testing")
@pytest.mark.usefixtures("disable_signals_create_user_profile")
@pytest.mark.django_db
class TestUserModelLevelValidation:
    # # * PASSWORD
    # @pytest.mark.parametrize(
    #     "password, is_valid",
    #     [
    #         ("PassW0rd!", True),
    #         ("password", False),
    #         ("PASSWORD", False),
    #         ("pass1234", False),
    #         ("P@ss", False),
    #     ],
    # )
    # def test_password_validation(self, password, is_valid):
    #     user = UserFactory.create_with_raw_password(password)
    #     if is_valid:
    #         try:
    #             user.full_clean()
    #         except ValidationError as e:
    #             pytest.fail(f"Expected valid, but got ValidationError: {e}")
    #     else:
    #         with pytest.raises(ValidationError):
    #             user.full_clean()
    #
    # @pytest.mark.parametrize(
    #     "password, expected_fragments",
    #     [
    #         (
    #             "short",  # < 8 chars, missing everything
    #             [
    #                 "at least 8 characters",
    #             ],
    #         ),
    #         (
    #             "longpassword",  # no digits, uppercase, or special char
    #             [
    #                 "uppercase letter",
    #                 "number",
    #                 "special character",
    #             ],
    #         ),
    #         (
    #             "LONGPASSWORD",  # no digits, uppercase, or special char
    #             [
    #                 "lowercase letter",
    #                 "number",
    #                 "special character",
    #             ],
    #         ),
    #         (
    #             "Password123",  # missing special character
    #             [
    #                 "special character",
    #             ],
    #         ),
    #     ],
    # )
    # def test_invalid_password_fails_validation(self, password, expected_fragments):
    #     with pytest.raises(ValidationError) as exc:
    #         user = UserFactory.create_with_raw_password(password)
    #         user.full_clean()
    #
    #     errors = exc.value.error_dict
    #     password_errors = errors.get("password", [])[0]
    #     messages = [error for error in password_errors]
    #
    #     for fragment in expected_fragments:
    #         assert any(fragment in msg for msg in messages), (
    #             f"Missing: {fragment} in password."
    #         )

    # * USEERNAME
    @pytest.mark.parametrize(
        "username, is_valid",
        [
            ("us", False),  # too short
            ("user", True),  # valid
            ("Sol.man", True),  # valid: includes dot
            ("Sol-man", True),  # valid: includes hyphen
            ("Sol_man", True),  # valid: includes underscore
            ("sol!man", False),  # invalid: exclamation mark
            ("user@name", False),  # invalid: @ not allowed
            ("a" * 31, False),  # too long
            ("a" * 30, True),  # max valid length
        ],
    )
    def test_username_validation(self, username, is_valid):
        user = UserFactory.create_with_username(username)

        if is_valid:
            try:
                user.full_clean()
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                user.full_clean()

    @pytest.mark.parametrize(
        "username, expected_fragments",
        [
            # Too short
            ("ab", ["at least 3 characters"]),
            # Too long (31 characters)
            ("a" * 31, ["cannot exceed 30 characters"]),
            # Starts with number
            ("1username", ["must start with a letter"]),
            # Starts with underscore
            ("_username", ["must start with a letter"]),
            # Starts with hyphen
            ("-username", ["must start with a letter"]),
            # Invalid character (e.g. space, @)
            ("user name", ["must start with a letter", "can contain letters, numbers"]),
            ("user@name", ["can contain letters, numbers"]),
        ],
    )
    def test_invalid_username_fails_validation(self, username, expected_fragments):
        with pytest.raises(ValidationError) as exc:
            user = UserFactory.create_with_username(username)
            user.full_clean()

        errors = exc.value.error_dict
        username_errors = errors.get("username", [])[0]
        messages = [error for error in username_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in username."
            )

    # * NAME
    @pytest.mark.parametrize(
        "name, is_valid",
        [
            # * Valid names
            ("John", True),
            ("Anne-Marie", True),
            ("O'Connor", True),
            ("José", True),
            ("Élise", True),
            ("A B", True),
            ("Jean-Paul Sartre", True),
            ("A" * 50, True),  # Exactly 50 chars
            #! Invalid names
            ("J", False),  # Too short
            ("A" * 51, False),  # Too long
            ("John123", False),  # Contains digits
            ("John_Doe", False),  # Contains underscore
            ("John@", False),  # Special character not allowed
            ("", False),  # Empty string
            ("    ", False),  # Only spaces
        ],
    )
    def test_name_validation(self, name, is_valid):
        user = UserFactory.create_with_name(name)

        if is_valid:
            try:
                user.full_clean()
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                user.full_clean()

    @pytest.mark.parametrize(
        "name, expected_fragments",
        [
            ("J", ["at least 2 characters"]),
            ("A" * 51, ["cannot exceed 50 characters"]),
            ("John123", ["can only contain letters"]),
            ("John@", ["can only contain letters"]),
            ("", ["This field cannot be blank."]),
            ("    ", ["Name cannot be empty or only spaces."]),
        ],
    )
    def test_invalid_name_fails_validation(self, name, expected_fragments):
        with pytest.raises(ValidationError) as exc:
            user = UserFactory.create_with_name(name)
            user.full_clean()

        errors = exc.value.error_dict
        name_errors = errors.get("name", [])[0]
        messages = [error for error in name_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in name."
            )

    @pytest.mark.parametrize(
        "email, is_valid",
        [
            # ✅ Valid emails
            ("user@example.com", True),
            ("user.name@example.co.uk", True),
            ("user_name@example.io", True),
            ("user-name@example.org", True),
            ("user+alias@example.com", True),
            ("u123@example.dev", True),
            ("USER@EXAMPLE.COM", True),
            # ❌ Invalid emails
            ("", False),  # Empty
            ("plainaddress", False),  # No domain
            ("@example.com", False),  # No local part
            ("user@", False),  # No domain part
            ("user@.com", False),  # Invalid domain
            ("user@com", False),  # Missing dot
            ("user@.com.", False),  # Ends with dot
            ("user@-example.com", False),  # Domain starts with dash
            ("user@exam_ple.com", False),  # Underscore in domain
            ("user@ example .com", False),  # Spaces
        ],
    )
    def test_email_validation(self, email, is_valid):
        user = UserFactory.create_with_email(email)

        if is_valid:
            try:
                user.full_clean()
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                user.full_clean()

    @pytest.mark.parametrize(
        "email, expected_fragments",
        [
            ("plainaddress", ["Enter a valid email address"]),
            ("@missingusername.com", ["Enter a valid email address"]),
            ("username@.com", ["Enter a valid email address"]),
            ("username@com", ["Enter a valid email address"]),
            ("username@.com.com", ["Enter a valid email address"]),
            ("username@domain", ["Enter a valid email address"]),
            ("username@domain..com", ["Enter a valid email address"]),
            ("", ["This field cannot be blank."]),
            ("   ", ["Enter a valid email address"]),
        ],
    )
    def test_email_validation_fails_validation(self, email, expected_fragments):
        with pytest.raises(ValidationError) as exc:
            user = UserFactory.create_with_email(email)
            user.full_clean()

        errors = exc.value.error_dict
        email_errors = errors.get("email", [])[0]
        messages = [error for error in email_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in email."
            )


@pytest.mark.skip(reason="Finsh testing")
@pytest.mark.usefixtures("disable_signals_create_user_profile")
@pytest.mark.django_db
class TestProfileModelLevelValidation:
    @pytest.mark.parametrize(
        "bio, is_valid",
        [
            # * Valid bios
            ("This is a valid bio", True),
            ("AA", True),
            ("A" * 250, True),
            ("", True),
            #! Invalid bios
            ("A", False),
            ("A" * 251, False),
        ],
    )
    def test_bio_validation(self, bio, is_valid):
        profile = ProfileFactory.create_with_bio(bio=bio)

        if is_valid:
            try:
                profile.full_clean()
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                profile.full_clean()

    @pytest.mark.parametrize(
        "bio, expected_fragments",
        [
            #! One character (too short)
            ("A", ["at least 2 characters", "too short"]),
            #! Over the max limit (251 chars)
            ("A" * 251, ["under 250 characters", "too long"]),
            #! Non-string value (optional edge case)
            (123, ["cannot contain only numbers"]),
        ],
    )
    def test_invalid_bio_fails_validation(self, bio, expected_fragments):
        with pytest.raises(ValidationError) as exc:
            profile = ProfileFactory.create_with_bio(bio=bio)
            profile.full_clean()

        errors = exc.value.error_dict
        bio_errors = errors.get("bio", [])[0]
        messages = [error for error in bio_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in bio."
            )

    @pytest.mark.parametrize(
        "birthday_date, is_valid",
        [
            (None, True),  # Optional field
            (TODAY, False),  # Edge case: today
            (TODAY + timedelta(days=1), False),  # Future birthday
            (date(TODAY.year - 11, TODAY.month, TODAY.day), False),  # Too young
            (date(TODAY.year - 12, TODAY.month, TODAY.day), True),  # Exactly 12
            (date(TODAY.year - 90, TODAY.month, TODAY.day), True),  # Exactly 90
            (date(TODAY.year - 91, TODAY.month, TODAY.day), False),  # Too old
            (date(TODAY.year - 30, TODAY.month, TODAY.day), True),  # Valid age
        ],
    )
    def test_birthday_date_and_age_validation(self, birthday_date, is_valid):
        profile = ProfileFactory.create_with_birthday_date(birthday_date=birthday_date)

        if is_valid:
            try:
                profile.full_clean()
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                profile.full_clean()

    @pytest.mark.parametrize(
        "birthday_date, expected_fragments",
        [
            #! Invalid type
            ("not-a-date", ["invalid date format", "YYYY-MM-DD"]),
            #! Unrealistic year
            (date(1800, 1, 1), ["unrealistic", "too far in the past"]),
            #! Future date
            (TODAY + timedelta(days=1), ["cannot be in the future"]),
            #! Too young (exactly 11 years old)
            (
                date(TODAY.year - 11, TODAY.month, TODAY.day),
                ["Too Young", "at least 12 years old"],
            ),
            #! Too young (11 years and 364 days)
            (
                TODAY.replace(year=TODAY.year - 12) + timedelta(days=1),
                ["Too Young", "at least 12 years old"],
            ),
            #! Too old (exactly 91 years old)
            (
                date(TODAY.year - 91, TODAY.month, TODAY.day),
                ["Too Old", "less than 90 years old"],
            ),
            #! Too old (91 years and 1 day)
            (
                TODAY.replace(year=TODAY.year - 91) - timedelta(days=1),
                ["Too Old", "less than 90 years old"],
            ),
        ],
    )
    def test_invalid_birthday_date_and_age_range_validation(
        self, birthday_date, expected_fragments
    ):
        with pytest.raises(ValidationError) as exc:
            profile = ProfileFactory.create_with_birthday_date(
                birthday_date=birthday_date
            )
            profile.full_clean()

        birthday_date_errors = None

        if hasattr(exc.value, "error_list"):
            birthday_date_errors = exc.value.error_list[0]

        elif hasattr(exc.value, "error_dict"):
            birthday_date_errors = exc.value.error_dict.get("birthday_date", [])[0]

        messages = [error for error in birthday_date_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in birthday_date."
            )

    @pytest.mark.parametrize(
        "size, is_valid",
        [
            (1024 * 1024, True),  # * 1 MB → valid
            (2 * 1024 * 1024, True),  # * Exactly 2 MB → valid
            (2 * 1024 * 1024 + 1, False),  #! Just over 2 MB → invalid
        ],
    )
    def test_avatar_validation(self, size, is_valid):
        image = SimpleUploadedFile(
            "avatar.jpg", b"\x00" * size, content_type="image/jpeg"
        )

        if is_valid:
            try:
                validate_image_size(image)
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                validate_image_size(image)

    @pytest.mark.parametrize(
        "size, expected_fragments",
        [
            ((2 * 1024 * 1024) + 1, ["under 2MB", "file size"]),
            ((2 * 1024 * 1024) + 1024, ["under 2MB", "file size"]),
        ],
    )
    def test_invalid_avatar_validation(self, size, expected_fragments):
        with pytest.raises(ValidationError) as exc:
            image = SimpleUploadedFile(
                "avatar.jpg", b"\x00" * size, content_type="image/jpeg"
            )
            validate_image_size(image)

        errors = exc.value.error_list
        avatar_errors = errors[0]
        messages = [error for error in avatar_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in avatar."
            )

    @pytest.mark.parametrize(
        "file_extension, is_valid",
        [
            ("avatar.jpg", True),
            ("avatar.jpeg", True),
            ("avatar.png", True),
            ("avatar.gif", False),
            ("avatar.exe", False),
        ],
    )
    def test_avatar_extension_validation(self, file_extension, is_valid):
        image = SimpleUploadedFile(
            file_extension, b"dummy data", content_type="image/jpeg"
        )

        if is_valid:
            try:
                validate_image_extension(image)
            except ValidationError as e:
                pytest.fail(f"Expected valid, but got ValidationError: {e}")
        else:
            with pytest.raises(ValidationError):
                validate_image_extension(image)

    @pytest.mark.parametrize(
        "file_extension, expected_fragments",
        [
            ("avatar.gif", ["Only JPG", "PNG", "and JPEG"]),
            ("avatar.webp", ["Only JPG", "PNG", "and JPEG"]),
            ("avatar.bmp", ["Only JPG", "PNG", "and JPEG"]),
            ("avatar.exe", ["Only JPG", "PNG", "and JPEG"]),
        ],
    )
    def test_invalid_avatar_extension_validation(
        self, file_extension, expected_fragments
    ):
        with pytest.raises(ValidationError) as exc:
            image = SimpleUploadedFile(
                file_extension, b"dummy data", content_type="image/jpeg"
            )
            validate_image_extension(image)

        errors = exc.value.error_list
        avatar_errors = errors[0]
        messages = [error for error in avatar_errors]

        for fragment in expected_fragments:
            assert any(fragment in msg for msg in messages), (
                f"Missing: {fragment} in avatar."
            )


# *===================================={Test Model-Level Validatores}================================================
