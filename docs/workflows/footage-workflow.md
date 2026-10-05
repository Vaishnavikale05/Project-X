# Footage ingestion workflow

MVP source is an uploaded/provided sample recording. The future college source is an adapter boundary only.

```mermaid
flowchart TD
  Start[Admin selects lecture and sample file] --> Auth[Authenticate and authorize institution/lecture]
  Auth --> Source[FootageProvider accepts source]
  Source --> Check[Inspect content, codec, size, duration, timestamps]
  Check -->|invalid| Reject[validation_failed; return safe error]
  Check -->|valid| Hash[Compute checksum and metadata]
  Hash --> Write[StorageAdapter writes temporary local file]
  Write --> Integrity[Verify write/checksum and finalize opaque key]
  Integrity -->|failure| Clean[Clean partial object; record failure]
  Integrity -->|success| Record[Persist Footage metadata/reference in PostgreSQL]
  Record --> Queue[Idempotently queue ProcessingJob]
  Queue --> Done[Return accepted footage/job status]
```

```mermaid
flowchart LR
  Sample[Local sample file] --> LocalProvider[LocalVideoProvider]
  College[Future approved VMS/NVR/share/export] -. future adapter .-> CollegeProvider[CollegeCCTVProvider]
  LocalProvider --> Contract[FootageProvider contract]
  CollegeProvider -. same contract .-> Contract
  Contract --> Validator[Ingestion validation]
  Validator --> Storage[StorageAdapter]
  Storage --> Local[(MVP local/file storage)]
  Storage -. future .-> Object[(S3 / MinIO / Azure Blob)]
  Validator --> Metadata[(PostgreSQL metadata/reference only)]
```

At no point does an adapter assume which CCTV/NVR/VMS product or protocol the institution uses. The provider must return a normalized recorded asset; downstream processing sees the same storage reference contract.
