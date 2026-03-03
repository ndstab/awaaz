from __future__ import annotations

from django.urls import path

from .views import (
  IncidentConfirmView,
  IncidentDetailView,
  IncidentListCreateView,
  IncidentResolveView,
)

urlpatterns = [
  path("incidents/", IncidentListCreateView.as_view(), name="incident-list-create"),
  path("incidents/<uuid:pk>/", IncidentDetailView.as_view(), name="incident-detail"),
  path(
    "incidents/<uuid:pk>/confirm/",
    IncidentConfirmView.as_view(),
    name="incident-confirm",
  ),
  path(
    "incidents/<uuid:pk>/resolve/",
    IncidentResolveView.as_view(),
    name="incident-resolve",
  ),
]

