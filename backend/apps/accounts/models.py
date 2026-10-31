from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra):
        if not email:
            raise ValueError("Email обов'язковий")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.update(is_staff=True, is_superuser=True)
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Лише персонал магазину. Клієнти працюють без реєстрації."""

    username = None  # type: ignore[assignment, misc]
    email = models.EmailField("email", unique=True)
    name = models.CharField("ім'я", max_length=150, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore[assignment, misc]

    class Meta:
        verbose_name = "користувач"
        verbose_name_plural = "користувачі"

    def __str__(self) -> str:
        return self.name or self.email
