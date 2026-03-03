from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
  class Role(models.TextChoices):
    CIVILIAN = "CIVILIAN", "Civilian"
    AUTHORITY = "AUTHORITY", "Authority"
    ADMIN = "ADMIN", "Admin"

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  email = models.EmailField(unique=True)
  role = models.CharField(max_length=20, choices=Role.choices, default=Role.CIVILIAN)
  verified = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)

  USERNAME_FIELD = "email"
  REQUIRED_FIELDS: list[str] = ["username"]

  def __str__(self) -> str:  # pragma: no cover - trivial
    return self.email

