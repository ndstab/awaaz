from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
  DEBUG=(bool, False),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="awaaz-insecure-change-me")
DEBUG = env("DEBUG")

ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
  "django.contrib.admin",
  "django.contrib.auth",
  "django.contrib.contenttypes",
  "django.contrib.sessions",
  "django.contrib.messages",
  "django.contrib.staticfiles",
  "django.contrib.gis",
  "rest_framework",
  "rest_framework_simplejwt",
  "corsheaders",
  "frontend",
  "incidents.apps.IncidentsConfig",
  "users.apps.UsersConfig",
]

MIDDLEWARE = [
  "django.middleware.security.SecurityMiddleware",
  "django.contrib.sessions.middleware.SessionMiddleware",
  "corsheaders.middleware.CorsMiddleware",
  "django.middleware.common.CommonMiddleware",
  "django.middleware.csrf.CsrfViewMiddleware",
  "django.contrib.auth.middleware.AuthenticationMiddleware",
  "django.contrib.messages.middleware.MessageMiddleware",
  "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "awaaz.urls"

TEMPLATES = [
  {
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "frontend" / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
      "context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
      ],
    },
  },
]

WSGI_APPLICATION = "awaaz.wsgi.application"

DATABASES = {
  "default": {
    "ENGINE": "django.contrib.gis.db.backends.postgis",
    "NAME": env("POSTGRES_DB", default="awaaz"),
    "USER": env("POSTGRES_USER", default="awaaz"),
    "PASSWORD": env("POSTGRES_PASSWORD", default="awaaz"),
    "HOST": env("POSTGRES_HOST", default="db"),
    "PORT": env("POSTGRES_PORT", default="5432"),
  }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
  {
    "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
  },
  {
    "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
  },
  {
    "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
  },
  {
    "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
  },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
  "DEFAULT_AUTHENTICATION_CLASSES": (
    "rest_framework_simplejwt.authentication.JWTAuthentication",
  ),
  "DEFAULT_PERMISSION_CLASSES": (
    "rest_framework.permissions.IsAuthenticatedOrReadOnly",
  ),
}

SIMPLE_JWT = {
  "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
  "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/1")

INCIDENT_DEDUP_RADIUS_METERS = 300
INCIDENT_DEDUP_WINDOW_HOURS = 2

CELERY_BEAT_SCHEDULE = {
  "expire-incidents-every-15-minutes": {
    "task": "incidents.tasks.expire_incidents",
    "schedule": timedelta(minutes=15),
  },
}

