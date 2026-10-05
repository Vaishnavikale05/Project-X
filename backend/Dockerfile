FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY src ./src
COPY tests ./tests
COPY manage.py ./manage.py
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
