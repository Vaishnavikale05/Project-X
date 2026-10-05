"""Allow `python -m project_x_backend.config.celery_app` for diagnostics."""

from .celery_app import app

app.start()
