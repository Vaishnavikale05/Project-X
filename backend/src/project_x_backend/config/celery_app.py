"""Celery application wired to Django settings for infrastructure tasks only."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_x_backend.config.settings.development")

app = Celery("project_x_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["project_x_backend.infrastructure"])
