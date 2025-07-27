from contextlib import contextmanager

import pytest
from django.db.models.signals import post_delete, post_save, pre_save

from users.models import Profile, User
from users.signals import (
    create_user_profile,
    delete_avatar_on_delete,
    delete_old_avatar,
)


@pytest.fixture()
def disable_signals_create_user_profile():
    post_save.disconnect(create_user_profile, sender=User)
    yield
    post_save.connect(create_user_profile, sender=User)


@pytest.fixture
def enable_signal():
    signal_map = {
        "post_save": (create_user_profile, post_save, User),
        "pre_save": (delete_old_avatar, pre_save, Profile),
        "post_delete": (delete_avatar_on_delete, post_delete, Profile),
    }

    @contextmanager
    def _enable(signal_name):
        if signal_name not in signal_map:
            raise ValueError(f"Unknown signal: {signal_name}")
        handler, signal, sender = signal_map[signal_name]
        signal.connect(handler, sender=sender)
        try:
            yield
        finally:
            signal.disconnect(handler, sender=sender)

    return _enable
