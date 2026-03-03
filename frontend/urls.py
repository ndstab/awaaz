from __future__ import annotations

from django.urls import path

from .views import map_view, report_view

urlpatterns = [
  path("", map_view, name="map"),
  path("report/", report_view, name="report"),
]

