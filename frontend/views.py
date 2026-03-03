from __future__ import annotations

from django.shortcuts import render


def map_view(request):
  return render(request, "map.html")


def report_view(request):
  return render(request, "report.html")

