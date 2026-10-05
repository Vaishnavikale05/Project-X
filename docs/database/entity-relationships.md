# Entity relationships and domain class diagram

This diagram reflects the Django domain models after Phase 5. Timetable entries are recurring plans; lectures are actual occurrences. Footage rows hold external storage references and metadata only. Processing jobs have many attempts/logs and may produce versioned CV runs. CV observations are observables; analytics aggregates are separate business-layer output. Track references are scoped to a CV run and do not identify a student. Camera identifiers are globally case-insensitively unique; classroom codes are unique within institution.

## ERD

```mermaid
erDiagram
  INSTITUTION ||--o{ USER : scopes
  INSTITUTION ||--o{ CLASSROOM : contains
  INSTITUTION ||--o{ SUBJECT : defines
  INSTITUTION ||--o{ TIMETABLE_ENTRY : schedules
  INSTITUTION ||--o{ LECTURE : owns
  INSTITUTION o|--o{ AUDIT_EVENT : scopes
  CLASSROOM ||--o{ CAMERA : has
  CLASSROOM ||--o{ TIMETABLE_ENTRY : hosts
  SUBJECT ||--o{ TIMETABLE_ENTRY : describes
  USER ||--o{ TIMETABLE_ENTRY : teaches
  TIMETABLE_ENTRY o|--o{ LECTURE : may_instantiate
  CLASSROOM ||--o{ LECTURE : hosts
  SUBJECT ||--o{ LECTURE : covers
  USER ||--o{ LECTURE : teaches
  LECTURE ||--o{ FOOTAGE : records
  CAMERA ||--o{ FOOTAGE : captures
  FOOTAGE ||--o{ PROCESSING_JOB : processed_by
  PROCESSING_JOB ||--o{ PROCESSING_LOG : records
  PROCESSING_JOB ||--o{ CV_RUN : produces
  CV_RUN ||--o{ CV_OBSERVATION : contains
  LECTURE ||--o{ ANALYTICS_RUN : has
  PROCESSING_JOB ||--o{ ANALYTICS_RUN : triggers
  CV_RUN ||--o{ ANALYTICS_RUN : informs
  ANALYTICS_RUN ||--o{ INDICATOR_AGGREGATE : contains
  LECTURE ||--o{ LECTURE_SUMMARY : snapshots
  ANALYTICS_RUN ||--o| LECTURE_SUMMARY : source_for
  LECTURE ||--o{ LECTURE_REPORT : has
  ANALYTICS_RUN ||--o{ LECTURE_REPORT : renders
  LECTURE ||--o{ RECOMMENDATION : has
  ANALYTICS_RUN ||--o{ RECOMMENDATION : supports
  USER o|--o{ AUDIT_EVENT : performs
```

## Class diagram

```mermaid
classDiagram
  class Institution { UUID id; string name; string code; string timezone; bool is_active }
  class User { UUID id; email email; string display_name; Role role; bool is_active }
  class Classroom { UUID id; string code; string name; int capacity; bool is_active }
  class Camera { UUID id; string identifier; string source_type; string status; JSON metadata }
  class Subject { UUID id; string code; string name; string department; bool is_active }
  class TimetableEntry { UUID id; int weekday; time start_time; time end_time; date valid_from; date valid_to; bool is_active }
  class Lecture { UUID id; string status; datetime scheduled_start; datetime scheduled_end; datetime actual_start; datetime actual_end }
  class Footage { UUID id; string storage_provider; string storage_key; bigint size_bytes; string media_format; string media_type; int width; int height; decimal frame_rate; bigint duration_ms; string status }
  class ProcessingJob { UUID id; string idempotency_key; string status; int attempt_count; int max_attempts; datetime queued_at; datetime started_at; datetime completed_at }
  class ProcessingLog { UUID id; int attempt_number; string level; string event_code; datetime occurred_at }
  class CVRun { UUID id; string contract_version; string pipeline_version; JSON model_versions; JSON coverage; string status }
  class CVObservation { UUID id; bigint window_start_ms; bigint window_end_ms; string track_ref; bool face_visible; decimal head_yaw_deg; decimal head_pitch_deg; string eye_state; JSON quality_flags }
  class AnalyticsRun { UUID id; string rule_set_version; string status; JSON limitations; datetime generated_at }
  class IndicatorAggregate { UUID id; string indicator_code; datetime window_start; datetime window_end; decimal value; string unit; decimal coverage; decimal confidence_summary }
  class LectureSummary { UUID id; decimal average_attention; decimal average_drowsiness; decimal average_distraction; decimal overall_engagement; datetime generated_at }
  class LectureReport { UUID id; int report_version; JSON summary_data; string status; datetime generated_at }
  class Recommendation { UUID id; string recommendation_type; string rule_id; string observation; string content; string priority; string status }
  class AuditEvent { UUID id; string action; string object_type; UUID object_id; JSON metadata_redacted; datetime occurred_at }

  Institution "1" --> "0..*" User
  Institution "1" --> "0..*" Classroom
  Institution "1" --> "0..*" Subject
  Institution "1" --> "0..*" TimetableEntry
  Institution "1" --> "0..*" Lecture
  Classroom "1" --> "0..*" Camera
  Classroom "1" --> "0..*" TimetableEntry
  Subject "1" --> "0..*" TimetableEntry
  User "1" --> "0..*" TimetableEntry : teacher
  TimetableEntry "0..1" --> "0..*" Lecture
  User "1" --> "0..*" Lecture : teacher
  Classroom "1" --> "0..*" Lecture
  Subject "1" --> "0..*" Lecture
  Lecture "1" --> "0..*" Footage
  Camera "1" --> "0..*" Footage
  Footage "1" --> "0..*" ProcessingJob
  ProcessingJob "1" --> "0..*" ProcessingLog
  ProcessingJob "1" --> "0..*" CVRun
  CVRun "1" --> "0..*" CVObservation
  ProcessingJob "1" --> "0..*" AnalyticsRun
  CVRun "1" --> "0..*" AnalyticsRun
  Lecture "1" --> "0..*" AnalyticsRun
  AnalyticsRun "1" --> "0..*" IndicatorAggregate
  AnalyticsRun "1" --> "0..1" LectureSummary
  Lecture "1" --> "0..*" LectureSummary
  AnalyticsRun "1" --> "0..*" LectureReport
  Lecture "1" --> "0..*" LectureReport
  AnalyticsRun "1" --> "0..*" Recommendation
  Lecture "1" --> "0..*" Recommendation
  User "0..1" --> "0..*" AuditEvent
```

`LectureSummary` is a versioned persisted projection for a specific analytics run, added in Phase 3 per the implementation requirement. Its metrics are copied from that run for efficient lecture-level reads; they do not replace `IndicatorAggregate` as the source of truth. Reports and recommendations retain a foreign key to the precise analytics run.
