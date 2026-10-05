FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY src ./src
ENV PYTHONPATH=/app/src
EXPOSE 8010
CMD ["python", "-m", "project_x_ai.health_server"]
