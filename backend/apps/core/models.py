from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("створено", auto_now_add=True)
    updated_at = models.DateTimeField("оновлено", auto_now=True)

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """Settings the owner edits in the admin. Always a single row with pk=1."""

    objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
