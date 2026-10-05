# Assumptions

- Development begins with sample recorded classroom videos, not a live camera feed.
- The college has some CCTV/NVR/VMS recording capability, but product access method, vendor, protocol, export format, authorization, and network boundaries are unknown.
- An institution-scoped deployment and initial roles `ADMIN` and `TEACHER` are sufficient for the first design.
- A lecture may have one or more associated footage assets over time; MVP processing is attached to one selected footage revision per job.
- Local/file storage is suitable for MVP; production capacity and backup policy remain to be specified.
- Teachers have an authorized relationship to lectures through timetable assignment or explicit admin grant.
- Observable face/head signals may be unavailable because of occlusion, camera angle, lighting, or image quality; coverage must be represented, not silently interpreted as a negative signal.
- Any actual video use, including validation data, needs appropriate institutional authorization and privacy/legal review.
