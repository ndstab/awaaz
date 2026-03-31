from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from incidents.models import Incident


User = get_user_model()


class Command(BaseCommand):
  help = "Seed demo users and incidents for Awaaz"

  def handle(self, *args, **options):
    civilian, _ = User.objects.get_or_create(
      email="civilian@awaaz.demo",
      defaults={
        "username": "civilian",
      },
    )
    if not civilian.has_usable_password():
      civilian.set_password("demo1234")
      civilian.save()

    authority, _ = User.objects.get_or_create(
      email="authority@awaaz.demo",
      defaults={
        "username": "authority",
        "role": User.Role.AUTHORITY,
        "verified": True,
      },
    )
    authority.role = User.Role.AUTHORITY
    authority.verified = True
    if not authority.has_usable_password():
      authority.set_password("demo1234")
    authority.save()

    now = timezone.now()

    samples = [
      # Bangalore
      {
        "key": ("BLR-ACCIDENT", "bangalore", "karnataka"),
        "type": Incident.Type.ACCIDENT,
        "severity": Incident.Severity.HIGH,
        "lat": 12.9716,
        "lng": 77.5946,
        "city": "bangalore",
        "state": "karnataka",
        "description": "Accident near MG Road",
      },
      {
        "key": ("BLR-FLOOD", "bangalore", "karnataka"),
        "type": Incident.Type.FLOOD,
        "severity": Incident.Severity.MEDIUM,
        "lat": 12.98,
        "lng": 77.6,
        "city": "bangalore",
        "state": "karnataka",
        "description": "Waterlogging reported after heavy rain",
      },
      # Mumbai
      {
        "key": ("MUM-CLOSURE", "mumbai", "maharashtra"),
        "type": Incident.Type.ROAD_CLOSURE,
        "severity": Incident.Severity.HIGH,
        "lat": 19.076,
        "lng": 72.8777,
        "city": "mumbai",
        "state": "maharashtra",
        "description": "Road closure near CST",
      },
      {
        "key": ("MUM-CONSTRUCTION", "mumbai", "maharashtra"),
        "type": Incident.Type.CONSTRUCTION,
        "severity": Incident.Severity.LOW,
        "lat": 19.09,
        "lng": 72.88,
        "city": "mumbai",
        "state": "maharashtra",
        "description": "Construction work on service road",
      },
      {
        "key": ("MUM-HAZARD", "mumbai", "maharashtra"),
        "type": Incident.Type.HAZARD,
        "severity": Incident.Severity.MEDIUM,
        "lat": 19.1,
        "lng": 72.87,
        "city": "mumbai",
        "state": "maharashtra",
        "description": "Debris on highway",
      },
    ]

    for sample in samples:
      code, city, state = sample["key"]
      incident, created = Incident.objects.get_or_create(
        reporter=authority,
        city=city,
        state=state,
        description=sample["description"],
        defaults={
          "type": sample["type"],
          "severity": sample["severity"],
          "location": Point(sample["lng"], sample["lat"], srid=4326),
          "address_text": "",
          "status": Incident.Status.ACTIVE,
          "confidence": 100,
          "reported_at": now,
          "expires_at": now + timezone.timedelta(hours=3),
        },
      )
      if not created:
        incident.type = sample["type"]
        incident.severity = sample["severity"]
        incident.location = Point(sample["lng"], sample["lat"], srid=4326)
        incident.status = Incident.Status.ACTIVE
        incident.confidence = 100
        incident.expires_at = now + timezone.timedelta(hours=3)
        incident.save()

    self.stdout.write(self.style.SUCCESS("Demo users and incidents seeded."))

