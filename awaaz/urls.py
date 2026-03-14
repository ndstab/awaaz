from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from incidents.feed import AllFeedView, CityFeedView, StateFeedView

urlpatterns = [
  path("admin/", admin.site.urls),
  path("", include("frontend.urls")),
  path("api/v1/", include("incidents.urls")),
  path("api/v1/auth/", include("users.urls")),
  path("feed/all/", AllFeedView.as_view(), name="feed-all-public"),
  path("feed/city/<slug:slug>/", CityFeedView.as_view(), name="feed-city-public"),
  path("feed/state/<slug:slug>/", StateFeedView.as_view(), name="feed-state-public"),
]

if settings.DEBUG:
  urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

