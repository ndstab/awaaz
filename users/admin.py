from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
  list_display = ("email", "username", "role", "verified", "is_active", "is_staff")
  list_filter = ("role", "verified", "is_active", "is_staff")
  search_fields = ("email", "username")
  ordering = ("email",)

  fieldsets = (
    (None, {"fields": ("email", "password")}),
    ("Personal info", {"fields": ("username",)}),
    ("Awaaz role", {"fields": ("role", "verified")}),
    (
      "Permissions",
      {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
    ),
    ("Important dates", {"fields": ("last_login", "date_joined", "created_at")}),
  )

  add_fieldsets = (
    (
      None,
      {
        "classes": ("wide",),
        "fields": ("email", "username", "password1", "password2", "role", "verified"),
      },
    ),
  )
