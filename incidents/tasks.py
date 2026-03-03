from __future__ import annotations

from django.utils import timezone

from awaaz.celery import app

from .models import Incident


@app.task
def expire_incidents() -> None:
  now = timezone.now()

  Incident.objects.filter(
    status=Incident.Status.ACTIVE,
    expires_at__lt=now,
  ).update(status=Incident.Status.EXPIRED)

  pending_cutoff = now - timezone.timedelta(hours=1)
  Incident.objects.filter(
    status=Incident.Status.PENDING,
    reported_at__lt=pending_cutoff,
  ).update(status=Incident.Status.EXPIRED)

