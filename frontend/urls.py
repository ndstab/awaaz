from __future__ import annotations

from django.urls import path

from .views import (
  incident_detail_view,
  login_view,
  map_view,
  register_view,
  report_view,
)

urlpatterns = [
  path("", map_view, name="map"),
  path("report/", report_view, name="report"),
  path("login/", login_view, name="login"),
  path("register/", register_view, name="register"),
  path("incident/<uuid:id>/", incident_detail_view, name="incident-detail"),
]

