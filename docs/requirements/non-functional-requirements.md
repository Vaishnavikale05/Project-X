# Non-functional requirements

- **Privacy:** data minimization, restricted access, retention/deletion policy, no student identity recognition in MVP, and approved/de-identified validation data.
- **Security:** secure password hashing, protected APIs and media, least privilege, secret management, input validation, auditability, and safe failure messages.
- **Reliability:** processing is asynchronous, idempotent, observable, retry-bounded, and recoverable after worker restart.
- **Maintainability:** modular monolith, explicit interfaces, migrations, testable services, versioned contracts, and architecture decision records.
- **Performance:** video work must not block HTTP requests. Throughput/latency targets await representative duration, resolution, hardware, and concurrency data.
- **Scalability:** allow worker concurrency and storage provider changes independently; do not require microservices for MVP.
- **Usability/accessibility:** clear processing states, data coverage/caveats, responsive layouts, keyboard accessibility, and explicit empty/error states.
- **Portability:** local development and deployable components described through environment configuration and later containerization.
- **Observability:** correlate footage, processing job, pipeline version, and analytics; logs exclude secrets, raw frames, and unnecessary personal data.
- **Compatibility:** version API and CV contracts; schema/data migrations preserve supported records.

Numeric availability, retention, throughput, accessibility conformance, and recovery objectives require stakeholder/deployment decisions.
