# ND13/2023 Compliance Checklist - MedViet AI Platform

## A. Data Localization
- [x] Patient data is stored in Vietnam-hosted storage buckets/databases.
- [x] Backups are configured to remain in Vietnam regions only.
- [x] Cross-border transfers are logged and blocked for restricted data by OPA policy.

## B. Explicit Consent
- [x] Consent is collected before using patient data for AI training.
- [x] Right-to-erasure workflow maps patient identity to internal `patient_id`.
- [x] Consent records include timestamp, purpose, data scope, and policy version.

## C. Breach Notification (72h)
- [x] Incident response runbook defines severity, owner, timeline, and escalation path.
- [x] Prometheus/Grafana alerts cover unusual API access and failed authorization spikes.
- [x] DPO and Security Team have a 72-hour regulator notification checklist.

## D. DPO Appointment
- [x] Data Protection Officer has been assigned.
- [x] DPO contact: dpo@medviet.example

## E. Technical Controls
| ND13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline with CCCD, phone, email, and name detection | Done | AI Team |
| Access control | Casbin RBAC in FastAPI plus OPA policy for ABAC guardrails | Done | Platform Team |
| Encryption | Envelope encryption with AES-256-GCM for sensitive values; TLS 1.3 required in deployment | Done | Infra Team |
| Audit logging | API access logs include user, role, resource, action, decision, timestamp, and request id | Planned | Platform Team |
| Breach detection | Prometheus alert rules for denied-access spikes, export attempts, and abnormal request volume | Planned | Security Team |

## F. Planned Technical Solutions

### Audit Logging
- Add FastAPI middleware to emit structured JSON audit events for every `/api/*` request.
- Store logs in append-only object storage with retention policy and daily integrity hash.
- Include Casbin decision result and OPA decision result so access reviews can be reproduced.
- Build a monthly access review report grouped by role, endpoint, and denied action.

### Breach Detection
- Export API metrics to Prometheus: request count, status code, role, endpoint, and latency.
- Add alerts for repeated 401/403 responses, raw PII access outside business hours, and export attempts where `destination_country != "VN"`.
- Route critical alerts to the incident response channel and create an incident ticket automatically.
- Keep Grafana dashboards for authorization failures, anomalous data access, and dependency/security scan status.
