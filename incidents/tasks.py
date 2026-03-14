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

  active_incidents = Incident.objects.filter(status=Incident.Status.ACTIVE)
  for incident in active_incidents:
    ttl = incident.expires_at - incident.reported_at
    if ttl.total_seconds() <= 0:
      continue

    last_confirmation = incident.confirmations.order_by("-confirmed_at").first()
    if not last_confirmation:
      continue

    if last_confirmation.confirmed_at < now - 2 * ttl:
      incident.status = Incident.Status.EXPIRED
      incident.save(update_fields=["status"])

