from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.cart.models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product", "qty", "group_label", "estimate")
    can_delete = False


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("id", "created_at", "expires_at", "closed_at")
    readonly_fields = ("token", "expires_at", "closed_at", "created_at")
    inlines = [CartItemInline]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
