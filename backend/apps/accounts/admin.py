from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.accounts.models import User

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    ordering = ("email",)
    list_display = ("email", "name", "is_active", "is_superuser", "last_login")
    list_filter = ("is_active", "groups")
    search_fields = ("email", "name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профіль", {"fields": ("name",)}),
        ("Доступ", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Дати", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",),
                             "fields": ("email", "name", "password1", "password2", "groups")}),)
    readonly_fields = ("last_login", "date_joined")


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
