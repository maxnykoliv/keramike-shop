import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

CART_TTL = timedelta(days=30)


def new_token() -> str:
    return secrets.token_urlsafe(24)


def default_expiry():
    return timezone.now() + CART_TTL


class Cart(TimeStampedModel):
    token = models.CharField(max_length=64, unique=True, default=new_token, editable=False)
    expires_at = models.DateTimeField(default=default_expiry)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "кошик"
        verbose_name_plural = "кошики"

    def __str__(self) -> str:
        return f"Кошик {self.pk}"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="+")
    qty = models.PositiveIntegerField("кількість")
    estimate = models.ForeignKey("calc.Estimate", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="+")
    group_label = models.CharField("група", max_length=100, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["cart", "product", "group_label"],
                                    name="unique_cart_product_group"),
            models.CheckConstraint(condition=models.Q(qty__gt=0), name="cart_item_qty_positive"),
        ]
