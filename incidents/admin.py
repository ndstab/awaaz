from __future__ import annotations

from django.contrib import admin

from .models import Confirmation, Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
  list_display = ("id", "type", "severity", "status", "city", "state", "confidence", "reported_at")
  list_filter = ("type", "severity", "status", "city", "state")
  search_fields = ("description", "address_text", "city", "state")
  readonly_fields = ("reported_at", "resolved_at")
  ordering = ("-reported_at",)


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
  list_display = ("id", "incident", "confirmer", "confirmed_at")
  list_filter = ("confirmed_at",)
  search_fields = ("incident__id", "confirmer__email")
  ordering = ("-confirmed_at",)

