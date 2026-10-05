# Institution, classroom, and camera workflow

Phase 5 configures physical infrastructure metadata. The college institution is provisioned outside the API; institution admins manage resources inside their own institution. No camera connectivity is attempted.

```mermaid
flowchart TD
  Login[Admin signs in] --> Context[Read own institution context]
  Context --> Classroom[Create or edit physical classroom]
  Classroom --> Scope{Admin scope and validation pass?}
  Scope -->|No| Err[Return safe 400 / 403 / 404 / 409]
  Scope -->|Yes| PersistRoom[(Persist classroom + redacted audit)]
  PersistRoom --> Register[Register camera metadata]
  Register --> Parent{Classroom active and in admin institution?}
  Parent -->|No| Err
  Parent -->|Yes| PersistCam[(Persist camera + redacted audit)]
  PersistCam --> Reload[Reload scoped API data]
  Reload --> Done[Display persisted classroom and camera]
  DeactivateCam[Deactivate camera first] --> DeactivateRoom[Deactivate classroom]
  DeactivateRoom --> HasChildren{Active cameras remain?}
  HasChildren -->|Yes| Err
  HasChildren -->|No| Deactivated[Deactivate classroom and write audit]
```

| Actor/action | API and persisted effect |
|---|---|
| ADMIN views institution | `GET /api/v1/institutions/` returns only the actor's own institution |
| ADMIN creates classroom | `POST /api/v1/classrooms/` derives institution from authenticated user; writes classroom and redacted `AuditEvent` atomically |
| ADMIN registers camera | `POST /api/v1/cameras/` validates active in-scope classroom and `LOCAL_FILE`; writes metadata and audit atomically |
| TEACHER reads resources | GET endpoints expose read-only infrastructure within the user's institution |
| ADMIN deactivates parent | Institution/classroom transition rejects with `409` while active children remain; no child is silently changed |

Audit metadata contains actor/action/resource ID/request ID and changed field names only. It does not copy submitted values, camera source references, passwords, tokens, or secrets. Camera `ACTIVE`/`INACTIVE` describes configured metadata lifecycle, not online connectivity.
