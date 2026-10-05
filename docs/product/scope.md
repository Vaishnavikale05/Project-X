# Scope

## MVP intent

- Process recorded sample videos after a lecture; never perform live monitoring.
- Support one institution deployment with `ADMIN` and `TEACHER` roles and institution-scoped authorization.
- Configure classrooms, cameras, subjects, timetable entries, and lectures.
- Ingest sample footage into local/file storage through a provider abstraction.
- Track footage and asynchronous processing lifecycle in PostgreSQL/Celery.
- Extract structured observable visual features and aggregate them into documented lecture/classroom indicators.
- Provide lecture status, analytics, reports, and rule-based recommendations to authorized teachers.

## Excluded from MVP

- College CCTV/NVR/VMS integration; actual interfaces and access method are unknown.
- Live or real-time monitoring, alerts, or streaming.
- Student identity recognition, face matching, attendance decisions, individual risk scoring, or student profiles.
- Emotion, boredom, interest, motivation, intelligence, or psychological-state inference.
- Automated grading, disciplinary action, or high-stakes decisions.
- Model training, LLM-authored metrics, or autonomous recommendations.
- S3/MinIO/Azure deployment, while preserving a storage-provider boundary.

## Future scope

Approved college source adapter, object-storage adapter, additional roles/tenancy if justified, and optional LLM phrasing constrained to approved metrics and evidence. Each requires a separate decision and privacy/security review.
