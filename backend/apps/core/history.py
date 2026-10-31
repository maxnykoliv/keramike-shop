"""Change author for django-simple-history.

DRF puts the site customer in request.user, but only staff can be authors in the history.
"""

from typing import Any


def staff_history_user(instance: Any = None, request: Any = None, **kwargs: Any):
    from django.contrib.auth import get_user_model

    user = getattr(instance, "_history_user", None) or getattr(request, "user", None)
    if isinstance(user, get_user_model()) and user.is_authenticated:
        return user
    return None
