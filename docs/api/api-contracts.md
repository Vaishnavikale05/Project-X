# API contracts (first draft)

All paths are prefixed `/api/v1`; protected endpoints require a JWT bearer access token. The readiness endpoint, CSRF bootstrap, login, refresh, and logout are explicitly public at the DRF permission layer; refresh/logout/login still require CSRF validation where browser cookies are involved. `ADMIN` means institution-scoped ADMIN. `Assigned teacher` means teacher assigned to that lecture. Error envelope is `{ "error": { "code": "...", "message": "...", "details": {}, "request_id": "..." } }`. Common errors: `400` malformed/validation, `401` unauthenticated, `403` unauthorized/CSRF failure, `404` missing or concealed, `409` state/conflict/idempotency conflict, `413` media too large, `415` unsupported media, `429` throttled, `500/503` sanitized server/dependency failure.

## Endpoint contracts

| Method / endpoint | Purpose and access | Request → response | Validation, errors and dependencies |
|---|---|---|---|
| `GET /auth/csrf/` | Obtain masked CSRF token; public | none → `{csrf_token}` and sets HttpOnly CSRF cookie | Used before login/refresh/logout; same-origin SPA; `200` |
| `POST /auth/login` | Authenticate active account; public, CSRF-protected, rate-limited | `{email,password}` → `{access,user:{id,email,display_name,role,is_active,institution_id}}`; refresh JWT is set only in HttpOnly cookie | Case-insensitive email lookup; generic `401` for unknown/wrong/inactive, `400` malformed, `403` CSRF, `429`; Django hasher, User, Redis throttle cache |
| `POST /auth/refresh` | Rotate refresh credential; public, CSRF-protected, rate-limited | empty JSON `{}` plus HttpOnly refresh cookie → `{access}` and rotated refresh cookie | Old refresh is blacklisted; missing/invalid/expired/reused token `401` and cookie cleared; CSRF `403`; SimpleJWT blacklist tables, Redis throttle cache |
| `POST /auth/logout` | Revoke refresh credential; public, CSRF-protected, idempotent | empty JSON `{}` plus cookie → `204`, clears cookie | Blacklists current refresh; access JWT may remain valid until its ≤5-minute expiry; CSRF `403`; blacklist store |
| `GET /auth/me` | Current principal; authenticated with bearer access token | none → `{id,email,display_name,role,is_active,institution_id}` | `401` invalid/expired/inactive; password/security fields are never returned; User |
| `GET /users` | List institution users; ADMIN | filters/page → user summaries | allow-listed filters; `403`, `400`; User/Institution |
| `POST /users` | Create account; ADMIN | `{email,display_name,role,temporary_password?}` → `201 user` | normalized, globally unique case-insensitive email, allowed role, password policy; `400/409`; User/Auth |
| `PATCH /users/{id}` | Update/deactivate account; ADMIN or self-limited fields | allowed profile/status fields → user | role/scope changes ADMIN-only; `403/404/400`; User/Audit |
| `GET /institutions/` | Read caller institution context; ADMIN/TEACHER | optional `search`, paginated → institution resources | Always scoped to user institution; `401/400` |
| `POST /institutions/` | Denied for institution-scoped ADMIN and TEACHER | no request accepted | Institution is bootstrap-provisioned; `403`; no SUPER_ADMIN in this phase |
| `GET /institutions/{id}/` | Read own institution; ADMIN/TEACHER | UUID → institution | Cross-institution/missing ID `404`; `401` |
| `PATCH /institutions/{id}/` | Update own institution metadata; ADMIN | `name`, `code`, `timezone`, `is_active` → institution | Case-insensitive code unique; valid IANA timezone; active classrooms block deactivation (`409`) |
| `GET /classrooms/` | List own institution classrooms; ADMIN/TEACHER | optional `institution_id`, `is_active`, `search`, `page`, `page_size` → page | Explicit foreign institution filter `403`; scope cannot be widened |
| `POST /classrooms/` | Create physical classroom; ADMIN | `{code,name?,capacity?,is_active?}` → `201` classroom | Institution derived from authenticated user; code case-insensitively unique within institution; positive capacity; client institution assignment rejected |
| `GET /classrooms/{id}/` | Read scoped classroom; ADMIN/TEACHER | UUID → classroom and institution summary | Cross-institution/missing ID `404` |
| `PATCH /classrooms/{id}/` | Update/deactivate scoped classroom; ADMIN | partial `{code,name,capacity,is_active}` → classroom | Active cameras block deactivation (`409`); field duplicate/invalid capacity `400`, uniqueness race `409`; no DELETE |
| `GET /cameras/` | List own institution cameras; ADMIN/TEACHER | optional `classroom_id`, `institution_id`, `status`, `source_type`, `search`, paging → page | Scope resolved through classroom; foreign institution filter `403`; all results paginated |
| `POST /cameras/` | Register metadata; ADMIN | `{classroom_id,code,display_name,source_type?,status?,resolution?,frame_rate?,description?}` → `201` camera | Classroom must be active/in-scope; globally case-insensitive unique code; only `LOCAL_FILE`; arbitrary fields and `source_reference` rejected; field duplicate `400`, uniqueness race `409` |
| `GET /cameras/{id}/` | Read camera metadata; ADMIN/TEACHER | UUID → safe camera resource | Scope resolved through classroom; `source_reference` is not serialized; cross-institution/missing ID `404` |
| `PATCH /cameras/{id}/` | Update/deactivate scoped camera metadata; ADMIN | partial writable metadata/status → camera | Cannot reassign classroom; inactive parent blocks activation (`409`); no credentials/connectivity/upload; no DELETE |
| `GET,POST /subjects` | List/create subject; ADMIN writes | `{code,name}` → subject | institution code unique; `400/409`; Institution |
| `GET,POST /timetable` | Query/create schedule; ADMIN writes | `{classroom_id,subject_id,teacher_id,weekday/effective_date,start_time,end_time,valid_from,valid_to}` → entry | interval, timezone/institution, teacher role, collision policy; `400/409`; User/Classroom/Subject |
| `GET,PATCH /timetable/{id}` | Read/update/deactivate entry; ADMIN writes | filters/patch → entry | scope and active lecture references; `403/404/409`; TimetableEntry |
| `GET,POST /lectures` | List/create occurrence; ADMIN creates; assigned TEACHER reads | `{timetable_entry_id?,classroom_id,subject_id,teacher_id,scheduled_start,end}` → lecture | scope and interval, teacher assignment; `400/409`; schedule/catalog |
| `GET /lectures/{id}` | Lecture context; ADMIN/assigned teacher | none → lecture and status summary | object authorization; `403/404`; Lecture |
| `GET /lectures/{id}/footage` | List assets; ADMIN/assigned teacher (safe metadata only) | none → footage metadata/status | never returns filesystem path; `403/404`; Footage |
| `POST /footage` | Ingest asset; ADMIN | multipart `file` + `lecture_id`,`camera_id`,`recorded_start/end`, `Idempotency-Key`; alternatively provider ref in future | content signature, allowlisted media, size/duration/resolution policy, scope/checksum; `201/202`, `400/413/415/409`; FootageProvider/StorageAdapter |
| `GET /footage/{id}` | Read metadata/status; ADMIN/assigned teacher | none → sanitized footage resource | object scope, no storage path; `403/404`; Footage |
| `POST /footage/{id}/processing` | Queue processing; ADMIN | `{pipeline_version?, options?}` + idempotency key → `202 {job_id,status}` | footage stored and lecture eligible, options allow-listed, duplicate safe; `400/404/409/503`; Footage/Celery |
| `GET /processing/jobs` | Query jobs; ADMIN; teacher constrained to assigned lecture | filters/status/page → job summaries | scoped filters, no sensitive internals; `403/400`; ProcessingJob |
| `GET /processing/jobs/{id}` | Job status; ADMIN/assigned teacher | none → lifecycle, timestamps, safe error code | object scope; `403/404`; ProcessingJob |
| `POST /processing/jobs/{id}/retry` | Retry eligible terminal failure; ADMIN | `{}` + idempotency key → `202 job` | retryable state, max attempts, source exists; `409/404/503`; ProcessingJob/Celery |
| `GET /analytics/lectures/{lecture_id}` | Read latest ready analytics; ADMIN/assigned teacher | optional `run_id` → indicators, coverage, versions, caveats | only completed ready run; `403/404/409`; AnalyticsRun |
| `GET /reports/lectures/{lecture_id}` | Read report; ADMIN/assigned teacher | optional `analytics_run_id` → report snapshot | stale/missing report handled explicitly; `403/404/409`; LectureReport |
| `POST /reports/lectures/{lecture_id}` | Generate report; ADMIN or authorized teacher request (policy to finalize) | `{analytics_run_id}` → `201` or `202` report | run ready; idempotent per version; `403/404/409`; AnalyticsRun |
| `GET /recommendations` | List recommendations; ADMIN/assigned teacher | `lecture_id` + paging → evidence-linked items | required scope; `403/400`; Recommendation/AnalyticsRun |
| `GET /admin/health` | Minimal operational health; ADMIN | none → component status without secret details | role check; `401/403/503`; DB/broker/storage health probes |

## Representative resources

Footage response contains `{id,lecture_id,camera_id,status,recorded_start,recorded_end,duration_ms,size_bytes,media_type,checksum,ingested_at}`; no local path. Job response contains `{id,footage_id,status,attempt_count,created_at,started_at,finished_at,error_code}`; error summary is sanitized. Analytics response includes `{lecture_id,analytics_run_id,rule_set_version,indicators:[{code,value,unit,window_start,window_end,coverage,confidence_summary,sample_count}],limitations:[...]}`. Exact schemas are refined with serializers/OpenAPI in implementation.
