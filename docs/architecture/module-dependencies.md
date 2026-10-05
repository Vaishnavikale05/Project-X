# Module dependencies

Arrows mean “depends on / consumes interface of.” Domain ownership remains with the source module; clients must not write another module's tables directly.

```mermaid
flowchart TD
  Access[User & Access] --> Institution[Institution / Classroom]
  Institution --> Camera[Camera Management]
  Institution --> Operations[Operations / redacted audit service]
  Camera --> Operations
  Operations --> Audit[(AuditEvent)]
  Institution --> Schedule[Timetable & Lecture]
  Camera --> Schedule
  Schedule --> Ingest[Footage Ingestion]
  Storage[Storage Adapter] --> Ingest
  Provider[FootageProvider] --> Ingest
  Ingest --> Jobs[Processing Orchestration]
  Storage --> Jobs
  Jobs --> CV[CV Layer]
  CV --> Analytics[Engagement Analytics]
  Schedule --> Analytics
  Analytics --> Reports[Reports]
  Analytics --> Recommendations[Recommendation Rules]
  Access --> Institution
  Access --> Schedule
  Access --> Ingest
  Access --> Jobs
  Access --> Analytics
  Access --> Reports
  Access --> Recommendations
  Reports --> UI[Teacher/Admin Dashboard]
  Recommendations --> UI
  Jobs --> Monitoring[Administration / Monitoring]
  Storage --> Monitoring
```

Phase 5 implements institution-context, classroom, and camera APIs/services plus transactional audit writes. The remaining module boundaries shown here are planned; the operations dependency is limited to safe mutation audit metadata.

Cross-module communication uses application services, REST contracts, and domain events/tasks. No module imports another module's private persistence internals. CV has no dependency on Django models, user roles, or recommendation rules. React depends on public API contracts only.
