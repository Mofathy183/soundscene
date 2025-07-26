from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import User, Profile
from django.core.exceptions import ObjectDoesNotExist
import os
from typing import Any
from django.db.models import Model


@receiver(post_save, sender=User)
def create_user_profile(
    sender: type[Model], instance: User, created: bool, **kwargs: Any
) -> None:
    """
    Signal handler that automatically creates a Profile instance
    when a new User instance is created.

    Args:
        sender (type[Model]): The model class (User) that sent the signal.
        instance (User): The instance of the User that was saved.
        created (bool): A boolean indicating if the instance was created.
        **kwargs (Any): Additional keyword arguments passed by the signal dispatcher.
    """
    if created:
        # Automatically create a one-to-one Profile for the new User
        Profile.objects.create(user=instance)


@receiver(pre_save, sender=Profile)
def delete_old_avatar(sender: type[Profile], instance: Profile, **kwargs: Any) -> None:
    """
    Signal handler to delete the old avatar file from storage
    when a Profile instance is updated with a new avatar.

    Args:
        sender (type[Model]): The model class that triggered the signal (Profile).
        instance (Profile): The instance of Profile being saved.
        **kwargs (Any): Additional keyword arguments provided by the signal dispatcher.
    """
    # Skip if the instance is new (has no ID yet)
    if not instance.id:
        return

    try:
        # Fetch the existing avatar from the database before updating
        old_avatar = sender.objects.get(id=instance.id).avatar
    except ObjectDoesNotExist:
        return

    new_avatar = instance.avatar

    # Delete the old avatar if it's changed and exists on disk
    if (
        old_avatar
        and old_avatar.name != new_avatar.name
        and hasattr(old_avatar, "path")
        and os.path.isfile(old_avatar.path)
    ):
        os.remove(old_avatar.path)


@receiver(post_delete, sender=Profile)
def delete_avatar_on_delete(
    sender: type[Model], instance: Profile, **kwargs: Any
) -> None:
    """
    Signal handler to delete the avatar file from storage when a Profile instance is deleted.

    Args:
        sender (type[Model]): The model class that sent the signal (Profile).
        instance (Profile): The instance of Profile that was deleted.
        **kwargs (Any): Additional keyword arguments passed by the signal dispatcher.
    """
    avatar = instance.avatar

    # Check if the avatar exists and has a valid file path
    if avatar and hasattr(avatar, "path") and os.path.isfile(avatar.path):
        # Remove the avatar file from the filesystem
        os.remove(avatar.path)
