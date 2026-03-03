from __future__ import annotations

from django.urls import path

from .feed import AllFeedView, CityFeedView, StateFeedView
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
  path("feed/all/", AllFeedView.as_view(), name="feed-all"),
  path("feed/city/<slug:slug>/", CityFeedView.as_view(), name="feed-city"),
  path("feed/state/<slug:slug>/", StateFeedView.as_view(), name="feed-state"),
]

