# Authorization and permission matrix

Authentication establishes the active user; reusable DRF role permissions establish coarse `ADMIN`/`TEACHER` capability. Phase 5 infrastructure endpoints additionally use reusable institution-scoped query policies for institutions, classrooms, and cameras. System workers use service identities/scoped internal permissions, never an interactive user's token.

| Module/resource | ADMIN | TEACHER |
|---|---|---|
| Own profile/auth | Read/update self; manage institution accounts per policy | Read/update self; login/logout |
| Users and roles | Create/read/update/deactivate within institution | Read self only |
| Institution | Read and update own metadata; cannot provision institutions | Read own institution context |
| Classroom | Read/create/update/deactivate in own institution | Read within own institution; no mutations |
| Cameras | Read/register/update/deactivate in own institution | Read within own institution; no mutations |
| Subject | Future: manage within institution | Future: read as authorized |
| Timetable/lectures | Manage within institution | Read assigned lectures; no reassignment |
| Footage | Ingest/list/read status/manage retention within institution | Read status only through assigned lecture; no direct file download by default |
| Processing jobs/logs | Create/retry/cancel/review scoped jobs and safe logs | Read status for assigned lectures; no raw diagnostic logs |
| Analytics/reports/recommendations | Read scoped outputs; no changes to finalized metrics | Read outputs only for assigned lectures |
| System monitoring | Read service/job health; no secret/raw-frame access | None |

All accesses must enforce object-level policies before serialization and in background task dispatch/results. Denied operations are auditable where appropriate. ADMIN is institution-scoped; whether an unscoped deployment operator role is needed is open, not assumed.

Phase 4 authorization foundation: unauthenticated requests receive `401`; authenticated users with a denied role receive `403`. `IsAdminRole`, `IsTeacherRole`, and `IsAdminOrTeacherRole` are reusable. Phase 5 infrastructure queries are scoped by `user.institution_id`; inaccessible detail IDs return `404`, and an explicitly mismatched institution filter returns `403`. Camera scope resolves through classroom to institution. Classroom/lecture assignment and all other resource policies remain future work; frontend guards never substitute for backend checks.
