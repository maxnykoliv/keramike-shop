from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline

from apps.customers import services
from apps.customers.models import Customer, CustomerAddress, CustomerSession


class AddressInline(TabularInline):
    model = CustomerAddress
    extra = 0
    fields = ("label", "delivery_method", "city_name", "warehouse_name", "address",
              "is_default")


class SessionInline(TabularInline):
    model = CustomerSession
    extra = 0
    fields = ("created_at", "last_used_at", "expires_at", "user_agent", "ip")
    readonly_fields = fields
    verbose_name_plural = "активні сесії (видалення = вихід на пристрої)"

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("phone", "name", "is_master", "telegram_username", "last_login_at",
                    "created_at")
    list_filter = ("is_master", "is_active")
    search_fields = ("phone", "name", "email", "telegram_username")
    readonly_fields = ("master_since", "telegram_user_id", "telegram_username",
                       "last_login_at", "created_at")
    fields = ("phone", "name", "email", "is_master", "master_since", "is_active",
              "telegram_username", "telegram_user_id", "last_login_at", "created_at")
    inlines = [AddressInline, SessionInline]
    actions = ["make_master", "remove_master"]

    def save_model(self, request, obj: Customer, form, change) -> None:
        if change and "is_master" in form.changed_data:
            super().save_model(request, obj, form, change)
            services.set_master(obj, obj.is_master)
            return
        super().save_model(request, obj, form, change)

    @admin.action(description="Надати статус майстра")
    def make_master(self, request, queryset) -> None:
        for customer in queryset:
            services.set_master(customer, True)
        messages.success(request, f"Статус майстра надано: {queryset.count()}")

    @admin.action(description="Зняти статус майстра")
    def remove_master(self, request, queryset) -> None:
        for customer in queryset:
            services.set_master(customer, False)
        messages.success(request, f"Статус майстра знято: {queryset.count()}")
