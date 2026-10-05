# Deployment architecture

This is a target topology; only the development services are configured in Phase 2. Compose separates the Vite frontend, Django API, PostgreSQL, Redis, Celery worker, and a liveness-only AI process. Production may serve static React assets through a reverse proxy and may separate hosts based on capacity/security review.

```mermaid
flowchart TB
  Browser[Teacher/Admin browser] --> Vite[React / Vite development frontend]
  Vite -->|/api proxy| API[Django REST API]
  API --> DB[(PostgreSQL private network)]
  API --> Broker[(Redis private network)]
  Broker --> Worker[Celery worker]
  Worker --> CV[Python CV package contract, future processing]
  API --> Files[(Local/file storage volume MVP)]
  Worker --> Files
  API -. future adapter .-> Obj[(Object storage)]
  Worker -. future adapter .-> Obj
  Proxy[Production reverse proxy / TLS] -. production routing .-> Vite
  Proxy -. production routing .-> API
  AIOps[AI service liveness process in Compose] -. no processing integration in Phase 2 .-> CV
  AdminOps[Operations] --> Metrics[Logs / health / metrics]
  API --> Metrics
  Worker --> Metrics
```

Keep DB/broker/storage private; serve media only through authorized application pathways. Credentials come from environment/secret management. Define backups, restore, retention, TLS, firewall, monitoring, and data-residency before production. College network/VMS connectivity is a future deployment-specific boundary and is not depicted as established connectivity.

The `ai` Compose service currently provides liveness only. The Celery worker consumes the independent Python CV package boundary only in a later processing phase; it is not a network processing service today.
