# Product overview

**Working name:** Project-X / Classroom Engagement Analytics (temporary; final name undecided).

Project-X is a planned system for college teachers and administrators to review engagement-related patterns from recorded, offline classroom lectures. Existing CCTV/NVR/VMS infrastructure is the eventual source. During development, uploaded sample recordings simulate that source. The system ingests footage, stores video files outside the database, processes them after recording through a CV pipeline, derives transparent indicators from observable visual signals, and presents lecture-level aggregates and reports.

It is not a live CCTV viewer or real-time monitoring system. It does not directly measure emotion, interest, boredom, intelligence, motivation, or any psychological or mental state. Indicators describe observable patterns under stated coverage and limitations.

## Actors

- **ADMIN:** configures institution resources, accounts, classrooms, cameras, timetable, ingestion, and processing operations within their authorized institution.
- **TEACHER:** views authorized lecture status, analytics, reports, and analytics-driven recommendations.
- **System worker:** validates, queues, processes footage, and persists structured outputs.
- **Future footage source:** an approved local, exported-file, network-share, or VMS/NVR adapter; source details are not assumed.
