from __future__ import annotations

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from awaaz.settings import INCIDENT_DEDUP_RADIUS_METERS, INCIDENT_DEDUP_WINDOW_HOURS

from .models import Confirmation, Incident
from .serializers import ConfirmationSerializer, IncidentSerializer


class IncidentListCreateView(generics.ListCreateAPIView):
  serializer_class = IncidentSerializer
  permission_classes = [permissions.IsAuthenticatedOrReadOnly]

  def get_queryset(self):
    qs = Incident.objects.filter(
      status__in=[Incident.Status.ACTIVE, Incident.Status.PENDING],
    )
    city = self.request.query_params.get("city")
    state = self.request.query_params.get("state")
    types = self.request.query_params.get("type")
    severities = self.request.query_params.get("severity")
    bbox = self.request.query_params.get("bbox")

    if city:
      qs = qs.filter(city__iexact=city)
    if state:
      qs = qs.filter(state__iexact=state)
    if types:
      type_values = [t.strip() for t in types.split(",") if t.strip()]
      if type_values:
        qs = qs.filter(type__in=type_values)
    if severities:
      severity_values = [s.strip() for s in severities.split(",") if s.strip()]
      if severity_values:
        qs = qs.filter(severity__in=severity_values)
    if bbox:
      parts = [p.strip() for p in bbox.split(",")]
      if len(parts) == 4:
        try:
          south, west, north, east = map(float, parts)
          envelope = Polygon.from_bbox((west, south, east, north))
          envelope.srid = 4326
          qs = qs.filter(location__intersects=envelope)
        except ValueError:
          pass
    return qs

  def perform_create(self, serializer):
    user = self.request.user
    lat = float(self.request.data.get("lat"))
    lng = float(self.request.data.get("lng"))
    point = Point(lng, lat, srid=4326)
    now = timezone.now()

    recent_window = now - timezone.timedelta(hours=INCIDENT_DEDUP_WINDOW_HOURS)

    existing = (
      Incident.objects.annotate(distance=Distance("location", point))
      .filter(
        type=self.request.data.get("type"),
        status__in=[Incident.Status.ACTIVE, Incident.Status.PENDING],
        reported_at__gte=recent_window,
        distance__lte=INCIDENT_DEDUP_RADIUS_METERS,
      )
      .first()
    )

    if existing:
      existing.confirmation_count += 1
      existing.confidence = min(existing.confidence + 15, 100)
      if existing.confidence >= 50 and existing.status == Incident.Status.PENDING:
        existing.status = Incident.Status.ACTIVE
      existing.save(update_fields=["confirmation_count", "confidence", "status"])
      self.existing_incident = existing
      return

    serializer.save()

  def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)

    if hasattr(self, "existing_incident"):
      data = IncidentSerializer(self.existing_incident).data
      return Response(
        {
          "detail": "Someone already reported this. Your confirmation has been added.",
          "incident": data,
        },
        status=status.HTTP_200_OK,
      )

    headers = self.get_success_headers(serializer.data)
    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class IncidentDetailView(generics.RetrieveAPIView):
  queryset = Incident.objects.all()
  serializer_class = IncidentSerializer
  permission_classes = [permissions.AllowAny]


class IncidentConfirmView(APIView):
  permission_classes = [permissions.IsAuthenticated]

  def post(self, request, pk):
    try:
      incident = Incident.objects.get(pk=pk)
    except Incident.DoesNotExist:
      return Response(status=status.HTTP_404_NOT_FOUND)

    try:
      lat = float(request.data.get("lat"))
      lng = float(request.data.get("lng"))
    except (TypeError, ValueError):
      return Response(
        {"detail": "lat and lng are required."},
        status=status.HTTP_400_BAD_REQUEST,
      )

    point = Point(lng, lat, srid=4326)
    distance_m = incident.location.distance(point)
    if distance_m is None or distance_m > 5000:
      return Response(
        {"detail": "You are too far from this incident to confirm it."},
        status=status.HTTP_400_BAD_REQUEST,
      )

    already = Confirmation.objects.filter(
      incident=incident,
      confirmer=request.user,
    ).exists()
    if already:
      return Response(
        {"detail": "You already confirmed this incident."},
        status=status.HTTP_400_BAD_REQUEST,
      )

    serializer = ConfirmationSerializer(
      data=request.data,
      context={"request": request, "incident": incident},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    incident.confirmation_count += 1
    incident.confidence = min(incident.confidence + 15, 100)
    if incident.confidence >= 50 and incident.status == Incident.Status.PENDING:
      incident.status = Incident.Status.ACTIVE
    incident.save(update_fields=["confirmation_count", "confidence", "status"])

    return Response(status=status.HTTP_201_CREATED)


class IncidentResolveView(APIView):
  permission_classes = [permissions.IsAuthenticated]

  def post(self, request, pk):
    try:
      incident = Incident.objects.get(pk=pk)
    except Incident.DoesNotExist:
      return Response(status=status.HTTP_404_NOT_FOUND)

    user = request.user
    if getattr(user, "role", None) not in {"AUTHORITY", "ADMIN"}:
      return Response(status=status.HTTP_403_FORBIDDEN)

    incident.status = Incident.Status.RESOLVED
    incident.resolved_at = timezone.now()
    incident.save(update_fields=["status", "resolved_at"])
    return Response(status=status.HTTP_200_OK)

