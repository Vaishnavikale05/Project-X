# Functional requirements

IDs are stable references for acceptance criteria and future implementation.

| ID | Requirement |
|---|---|
| FR-01 | Authenticate users and authorize all actions by role plus institution/object scope. |
| FR-02 | Admins manage institution-scoped classrooms, cameras, subjects, timetable entries, and users. |
| FR-03 | A lecture links its institution, classroom, camera context, subject, timetable occurrence, teacher, and planned/actual time range. |
| FR-04 | Ingest footage through a provider interface; MVP provider accepts sample local files and validates media, size/duration policy, and checksum. |
| FR-05 | Store video bytes in local/file storage; persist provider/key and descriptive metadata in PostgreSQL only. |
| FR-06 | Create an idempotent asynchronous processing job, expose lifecycle/status, bounded retry, safe error summary, and processing logs. |
| FR-07 | CV layer extracts frames, persons, tracks, face/landmark observations and temporal observable features into a versioned schema. |
| FR-08 | Analytics layer converts CV output into documented, classroom-level attention-, drowsiness-, and distraction-related indicators, reporting coverage/confidence and limitations. These are proxies derived from visual signals, not mental-state measurements. |
| FR-09 | Teachers view only authorized lecture status, analytics, report, and recommendations. |
| FR-10 | Generate reports from a defined analytics version and deterministic rule set. |
| FR-11 | Recommendations are rule/analytics-driven, traceable to observation and evidence; optional future language generation cannot invent metrics. |
| FR-12 | Record audit fields and selected security-sensitive actions; provide operational status for jobs and system components to admins. |
| FR-13 | Support future footage-source and storage providers through stable interfaces without changing downstream processing contracts. |
