from __future__ import annotations

from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework import serializers

from .models import Confirmation, Incident


INCIDENT_TTLS = {
  Incident.Type.ACCIDENT: 3,
  Incident.Type.FLOOD: 6,
  Incident.Type.ROAD_CLOSURE: 24,
  Incident.Type.CONSTRUCTION: 24 * 7,
  Incident.Type.POLICE_NAKA: 2,
  Incident.Type.PROTEST: 4,
  Incident.Type.HAZARD: 12,
  Incident.Type.OTHER: 6,
}


class IncidentSerializer(serializers.ModelSerializer):
  lat = serializers.FloatField(write_only=True)
  lng = serializers.FloatField(write_only=True)
  latitude = serializers.FloatField(source="location.y", read_only=True)
  longitude = serializers.FloatField(source="location.x", read_only=True)

  class Meta:
    model = Incident
    fields = [
      "id",
      "reporter",
      "type",
      "severity",
      "description",
      "location",
      "address_text",
      "city",
      "state",
      "photo",
      "status",
      "confidence",
      "confirmation_count",
      "reported_at",
      "expires_at",
      "resolved_at",
      "lat",
      "lng",
      "latitude",
      "longitude",
    ]
    read_only_fields = [
      "reporter",
      "location",
      "status",
      "confidence",
      "confirmation_count",
      "reported_at",
      "expires_at",
      "resolved_at",
    ]

  def create(self, validated_data):
    lat = validated_data.pop("lat")
    lng = validated_data.pop("lng")
    user = self.context["request"].user
    now = timezone.now()

    incident_type = validated_data["type"]
    ttl_hours = INCIDENT_TTLS.get(incident_type, 6)
    expires_at = now + timezone.timedelta(hours=ttl_hours)

    base_confidence = 100 if getattr(user, "role", None) == "AUTHORITY" else 20

    incident = Incident.objects.create(
      reporter=user,
      location=Point(lng, lat, srid=4326),
      confidence=base_confidence,
      status=(
        Incident.Status.ACTIVE
        if base_confidence >= 50
        else Incident.Status.PENDING
      ),
      expires_at=expires_at,
      **validated_data,
    )
    return incident


class ConfirmationSerializer(serializers.ModelSerializer):
  lat = serializers.FloatField(write_only=True)
  lng = serializers.FloatField(write_only=True)

  class Meta:
    model = Confirmation
    fields = ["id", "incident", "confirmer", "location", "confirmed_at", "lat", "lng"]
    read_only_fields = ["id", "incident", "confirmer", "location", "confirmed_at"]

  def create(self, validated_data):
    lat = validated_data.pop("lat")
    lng = validated_data.pop("lng")
    user = self.context["request"].user
    incident = self.context["incident"]
    confirmation = Confirmation.objects.create(
      incident=incident,
      confirmer=user,
      location=Point(lng, lat, srid=4326),
    )
    return confirmation

