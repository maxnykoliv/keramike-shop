"""Staff roles. The setup_roles command creates the groups."""

OWNER_GROUP = "Власник"
MANAGER_GROUP = "Менеджер"


def is_owner(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=OWNER_GROUP).exists()
