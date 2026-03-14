from __future__ import annotations

from django.shortcuts import get_object_or_404, render

from incidents.models import Incident


def map_view(request):
  return render(request, "map.html")


def report_view(request):
  return render(request, "report.html")


def login_view(request):
  return render(request, "login.html")


def register_view(request):
  return render(request, "register.html")


def incident_detail_view(request, id):
  incident = get_object_or_404(Incident, pk=id)
  return render(request, "incident.html", {"incident": incident})

