"""Infrastructure-only Celery smoke task; no footage or domain processing."""

from celery import shared_task


@shared_task(name="infrastructure.ping")
def ping() -> dict[str, str]:
    return {"status": "ok"}
