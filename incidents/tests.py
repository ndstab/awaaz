from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APITestCase

from incidents.models import Incident


User = get_user_model()


class IncidentApiTests(APITestCase):
  def setUp(self):
    self.civilian = User.objects.create_user(
      email="civilian@test.local",
      username="civilian",
      password="demo1234",
    )
    self.authority = User.objects.create_user(
      email="authority@test.local",
      username="authority",
      password="demo1234",
      role=User.Role.AUTHORITY,
      verified=True,
    )

  def auth(self, user):
    resp = self.client.post(
      "/api/v1/auth/login/",
      {"email": user.email, "password": "demo1234"},
      format="json",
    )
    self.assertEqual(resp.status_code, status.HTTP_200_OK)
    token = resp.data["access"]
    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

  def test_create_incident_creates_record(self):
    self.auth(self.civilian)
    payload = {
      "type": "ACCIDENT",
      "severity": "LOW",
      "description": "Test incident",
      "lat": 12.9716,
      "lng": 77.5946,
      "city": "bangalore",
      "state": "karnataka",
      "address_text": "Somewhere",
    }
    resp = self.client.post("/api/v1/incidents/", payload, format="json")
    self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    self.assertEqual(Incident.objects.count(), 1)

  def test_civilian_starts_pending(self):
    self.auth(self.civilian)
    payload = {
      "type": "ACCIDENT",
      "severity": "LOW",
      "description": "Civilian report",
      "lat": 12.9716,
      "lng": 77.5946,
      "city": "bangalore",
      "state": "karnataka",
    }
    resp = self.client.post("/api/v1/incidents/", payload, format="json")
    self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    inc = Incident.objects.get()
    self.assertEqual(inc.status, Incident.Status.PENDING)

  def test_authority_starts_active(self):
    self.auth(self.authority)
    payload = {
      "type": "ACCIDENT",
      "severity": "LOW",
      "description": "Authority report",
      "lat": 12.9716,
      "lng": 77.5946,
      "city": "bangalore",
      "state": "karnataka",
    }
    resp = self.client.post("/api/v1/incidents/", payload, format="json")
    self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    inc = Incident.objects.get()
    self.assertEqual(inc.status, Incident.Status.ACTIVE)

  def test_confirm_increases_confidence(self):
    self.auth(self.civilian)
    payload = {
      "type": "ACCIDENT",
      "severity": "LOW",
      "description": "Needs confirms",
      "lat": 12.9716,
      "lng": 77.5946,
      "city": "bangalore",
      "state": "karnataka",
    }
    resp = self.client.post("/api/v1/incidents/", payload, format="json")
    self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    inc_id = resp.data["id"]
    inc = Incident.objects.get(pk=inc_id)
    base_conf = inc.confidence

    self.client.credentials()
    self.auth(self.authority)
    confirm_payload = {"lat": 12.9716, "lng": 77.5946}
    resp2 = self.client.post(
      f"/api/v1/incidents/{inc_id}/confirm/",
      confirm_payload,
      format="json",
    )
    self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
    inc.refresh_from_db()
    self.assertGreater(inc.confidence, base_conf)

  def test_feed_all_returns_xml(self):
    now = timezone.now()
    Incident.objects.create(
      reporter=self.authority,
      type=Incident.Type.ACCIDENT,
      severity=Incident.Severity.LOW,
      description="For feed",
      location=Point(77.5946, 12.9716, srid=4326),
      address_text="",
      city="bangalore",
      state="karnataka",
      status=Incident.Status.ACTIVE,
      confidence=100,
      reported_at=now,
      expires_at=now + timezone.timedelta(hours=3),
    )

    resp = self.client.get("/feed/all/")
    self.assertEqual(resp.status_code, status.HTTP_200_OK)
    self.assertTrue(resp["Content-Type"].startswith("application/xml"))
    self.assertTrue(resp.content.strip().startswith(b"<incidents"))

