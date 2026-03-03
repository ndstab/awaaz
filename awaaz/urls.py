from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
  path("admin/", admin.site.urls),
  path("", include("frontend.urls")),
  path("api/v1/", include("incidents.urls")),
  path("api/v1/auth/", include("users.urls")),
]

if settings.DEBUG:
  urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

