# Storage strategy

## Responsibility split

- **PostgreSQL:** lecture/camera/footage metadata, lifecycle and processing status, checksums, file sizes, dimensions/duration, opaque storage references, structured observations/analytics or artifact references, audit metadata.
- **Local/file storage (MVP):** original video bytes and any retained structured CV artifact too large for relational rows. Video binaries are never stored in PostgreSQL.
- **Redis:** Celery broker/cache only; not authoritative job or footage state.

## Interface

The Phase 2 `StorageProvider` port defines `save(stream, suffix) -> StoredObject(provider, key, size_bytes, checksum_sha256)`, `retrieve(key) -> readable stream`, `exists(key)`, `delete(key)`, and `metadata(key)`. Future adapters implement the same port; business code stores provider + opaque key and never constructs a filesystem path. Local adapter confines resolved paths to configured root, generates opaque keys, uses atomic writes, checks checksums and rejects traversal/symlink escape. Media is served only through authorization-checked endpoints or short-lived approved access.

The Phase 2 `FootageSource` port defines `describe(source_reference) -> SourceAsset` and `open(source_reference) -> readable stream`. `LocalSampleVideoProvider` is the planned sample-file adapter contract. A future `CollegeCCTVProvider` may wrap an approved VMS/NVR API, network share, SMB/SFTP, or exported files only after discovery; no specific mechanism is assumed. Providers return the same normalized source type and do not change the downstream processing contract.

## Lifecycle and operations

Ingestion validates and stores to a temporary target, computes checksum, then atomically finalizes storage metadata. Failures remove incomplete temporary content and record a safe error. Deletion/retention must coordinate database state and external bytes with retryable reconciliation; do not rely on a single cross-system transaction. Backups must include both database and storage with a tested restore mapping. Capacity, retention, encryption-at-rest, backup, and deletion periods are open deployment/privacy decisions.
