from __future__ import annotations

from django.http import HttpResponse
from django.utils import timezone
from django.views import View
import xml.etree.ElementTree as ET

from .models import Incident


class BaseFeedView(View):
  def get_queryset(self):
    return Incident.objects.filter(
      status=Incident.Status.ACTIVE,
      expires_at__gt=timezone.now(),
    )

  def build_xml(self, incidents):
    root = ET.Element("incidents")
    for incident in incidents:
      elem = ET.SubElement(
        root,
        "incident",
        id=str(incident.id),
        creationtime=incident.reported_at.isoformat(),
        updatetime=(incident.resolved_at or incident.reported_at).isoformat(),
      )
      ET.SubElement(elem, "type").text = incident.type
      ET.SubElement(elem, "severity").text = incident.severity
      loc = ET.SubElement(elem, "location")
      ET.SubElement(loc, "street").text = incident.address_text or ""
      point = incident.location
      ET.SubElement(loc, "polyline").text = f"{point.y},{point.x}"
      ET.SubElement(elem, "active").text = "true"

    xml_bytes = ET.tostring(root, encoding="utf-8")
    return HttpResponse(xml_bytes, content_type="application/xml")


class AllFeedView(BaseFeedView):
  def get(self, request, *args, **kwargs):
    qs = self.get_queryset()
    return self.build_xml(qs)


class CityFeedView(BaseFeedView):
  def get(self, request, slug, *args, **kwargs):
    qs = self.get_queryset().filter(city__iexact=slug)
    return self.build_xml(qs)


class StateFeedView(BaseFeedView):
  def get(self, request, slug, *args, **kwargs):
    qs = self.get_queryset().filter(state__iexact=slug)
    return self.build_xml(qs)

