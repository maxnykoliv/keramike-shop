from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from apps.core.exceptions import DomainError
from apps.core.money import format_uah
from apps.orders import services
from apps.orders.models import Order, OrderEvent, OrderItem, OrderSettings
from apps.orders.state import OrderStatus, PaymentStatus, can_transition


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "sku", "qty", "unit", "qty_base", "price_kop", "total_kop", "group_label")
    readonly_fields = ("name", "sku", "unit", "qty_base", "price_kop", "total_kop",
                       "group_label")

    def _editable(self, obj) -> bool:
        return bool(obj) and obj.status == OrderStatus.NEW and (
            obj.payment_status != PaymentStatus.PAID
        )

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return self._editable(obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        return self._editable(obj) and super().has_delete_permission(request, obj)


class OrderEventInline(TabularInline):
    model = OrderEvent
    extra = 0
    can_delete = False
    fields = ("created_at", "from_status", "to_status", "actor", "comment")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False


def _transition_action(target: str, description: str):
    def handler(self, request, object_id):
        try:
            services.transition(int(object_id), target, actor=request.user)
            messages.success(request, f"Статус змінено: {OrderStatus(target).label}")
        except DomainError as exc:
            messages.error(request, exc.message)
        return redirect(reverse("admin:orders_order_change", args=[object_id]))

    # Unfold перевіряє права за іменем функції, тому ім'я задаємо до декорування.
    handler.__name__ = handler.__qualname__ = f"to_{target}"
    return action(description=description, url_path=f"to-{target}",
                  permissions=[f"to_{target}"])(handler)


def _transition_permission(target: str):
    def check(self, request, object_id=None) -> bool:
        if not request.user.has_perm("orders.change_order") or object_id is None:
            return False
        order = Order.objects.filter(pk=object_id).only("status").first()
        return order is not None and can_transition(order.status, target)

    return check


@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ("number", "created_at", "customer_name", "phone", "status",
                    "payment_status", "total", "needs_review")
    list_filter = ("status", "payment_status", "payment_method", "delivery_method",
                   "needs_review")
    search_fields = ("number", "phone", "customer_name", "email")
    date_hierarchy = "created_at"
    raw_id_fields = ("customer",)
    inlines = [OrderItemInline, OrderEventInline]
    readonly_fields = ("number", "status", "payment_status", "subtotal_kop", "total_kop",
                       "weight_kg", "estimate", "paid_at", "confirmed_at", "shipped_at",
                       "completed_at", "cancelled_at", "created_at", "totals")
    fieldsets = (
        (None, {"fields": ("number", "status", "payment_method", "payment_status",
                           "needs_review", "manager", "customer")}),
        ("Клієнт", {"fields": ("customer_name", "phone", "email", "comment")}),
        ("Доставка", {"fields": ("delivery_method", "delivery", "delivery_kop")}),
        ("Суми", {"fields": ("totals", "weight_kg", "estimate")}),
        ("Дати", {"fields": ("created_at", "confirmed_at", "paid_at", "shipped_at",
                             "completed_at", "cancelled_at")}),
    )
    actions_detail = ["to_confirmed", "to_packed", "to_shipped", "to_completed",
                      "to_cancelled"]

    to_confirmed = _transition_action(OrderStatus.CONFIRMED, "Підтвердити")
    to_packed = _transition_action(OrderStatus.PACKED, "Зібрано")
    to_shipped = _transition_action(OrderStatus.SHIPPED, "Відправлено")
    to_completed = _transition_action(OrderStatus.COMPLETED, "Виконано")
    to_cancelled = _transition_action(OrderStatus.CANCELLED, "Скасувати")
    has_to_confirmed_permission = _transition_permission(OrderStatus.CONFIRMED)
    has_to_packed_permission = _transition_permission(OrderStatus.PACKED)
    has_to_shipped_permission = _transition_permission(OrderStatus.SHIPPED)
    has_to_completed_permission = _transition_permission(OrderStatus.COMPLETED)
    has_to_cancelled_permission = _transition_permission(OrderStatus.CANCELLED)

    @admin.display(description="Разом", ordering="total_kop")
    def total(self, obj: Order) -> str:
        return format_uah(obj.total_kop)

    @admin.display(description="Суми")
    def totals(self, obj: Order) -> str:
        delivery = "уточнюється" if obj.delivery_kop is None else format_uah(obj.delivery_kop)
        return (f"Товари: {format_uah(obj.subtotal_kop)}; доставка: {delivery}; "
                f"разом: {format_uah(obj.total_kop)}")

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def save_model(self, request, obj: Order, form, change) -> None:
        super().save_model(request, obj, form, change)
        if change and "delivery_kop" in form.changed_data:
            try:
                services.set_delivery_cost(obj.pk, obj.delivery_kop)
            except DomainError as exc:
                messages.error(request, exc.message)

    def save_formset(self, request, form, formset, change) -> None:
        super().save_formset(request, form, formset, change)
        if formset.model is OrderItem and formset.has_changed():
            try:
                services.reprice(form.instance.pk)
            except DomainError as exc:
                messages.error(request, exc.message)


@admin.register(OrderSettings)
class OrderSettingsAdmin(ModelAdmin):
    def has_add_permission(self, request) -> bool:
        return not OrderSettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
