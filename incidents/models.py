from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models


class Incident(models.Model):
  class Type(models.TextChoices):
    ACCIDENT = "ACCIDENT", "Accident"
    FLOOD = "FLOOD", "Flood"
    ROAD_CLOSURE = "ROAD_CLOSURE", "Road closure"
    CONSTRUCTION = "CONSTRUCTION", "Construction"
    POLICE_NAKA = "POLICE_NAKA", "Police naka"
    PROTEST = "PROTEST", "Protest"
    HAZARD = "HAZARD", "Hazard"
    OTHER = "OTHER", "Other"

  class Severity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"

  class Status(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    RESOLVED = "RESOLVED", "Resolved"
    EXPIRED = "EXPIRED", "Expired"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  reporter = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="incidents",
  )
  type = models.CharField(max_length=32, choices=Type.choices)
  severity = models.CharField(max_length=16, choices=Severity.choices)
  description = models.TextField(blank=True, max_length=500)
  location = gis_models.PointField(geography=True, srid=4326)
  address_text = models.CharField(max_length=255, blank=True)
  city = models.CharField(max_length=100)
  state = models.CharField(max_length=100)
  photo = models.CharField(max_length=255, blank=True)
  status = models.CharField(
    max_length=16,
    choices=Status.choices,
    default=Status.PENDING,
  )
  confidence = models.IntegerField(default=20)
  confirmation_count = models.IntegerField(default=0)
  reported_at = models.DateTimeField(auto_now_add=True)
  expires_at = models.DateTimeField()
  resolved_at = models.DateTimeField(null=True, blank=True)

  def __str__(self) -> str:  # pragma: no cover - trivial
    return f"{self.type} @ {self.city}, {self.state}"


class Confirmation(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  incident = models.ForeignKey(
    Incident,
    on_delete=models.CASCADE,
    related_name="confirmations",
  )
  confirmer = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="confirmations",
  )
  location = gis_models.PointField(geography=True, srid=4326)
  confirmed_at = models.DateTimeField(auto_now_add=True)

  def __str__(self) -> str:  # pragma: no cover - trivial
    return f"Confirmation for {self.incident_id}"

