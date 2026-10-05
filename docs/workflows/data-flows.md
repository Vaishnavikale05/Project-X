# Data-flow diagrams

## DFD Level 0: context

```mermaid
flowchart LR
  Admin[Admin] -->|configuration, recorded sample footage, processing request| System((Project-X post-lecture analytics system))
  System -->|configuration status, job state, operational summaries| Admin
  Teacher[Teacher] -->|authenticated lecture/report request| System
  System -->|authorized lecture analytics, report, caveats| Teacher
  System <-->|approved recorded asset exchange, future only| CCTV[College CCTV/NVR/VMS source]
```

## DFD Level 1

```mermaid
flowchart LR
  Admin[Admin] --> P1[1. Configure institution and schedule]
  Teacher[Teacher] --> P5[5. Serve authorized results]
  P1 --> D1[(D1 PostgreSQL application metadata)]
  Admin --> P2[2. Ingest and validate recorded footage]
  Source[Sample file / future provider] --> P2
  P2 --> D2[(D2 Local video file storage)]
  P2 --> D1
  P2 --> P3[3. Queue and process asynchronously]
  P3 <--> Q[(Redis/Celery queue)]
  P3 --> CV[4. CV observation extraction]
  D2 --> CV
  CV --> P3
  P3 --> D1
  P3 --> P4[5. Aggregate analytics, reports, recommendations]
  P4 --> D1
  D1 --> P5
  P5 --> Teacher
```

PostgreSQL is D1 (metadata/results), not the video store. D2 contains video bytes. The college source is future-only; no real-time stream path exists.
