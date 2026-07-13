# Data classification and retention

| Class | WasteOps examples | Handling |
|---|---|---|
| Public | Application name, approved public documentation | May be published after review. |
| Internal | Aggregated operational metrics and release metadata | Authenticated users; no public object URLs. |
| Confidential | Truck, bin, workforce, documents, procedures, prompts, feedback, traces | Least privilege, encryption, private storage, audited administrative reads. |
| Restricted | Tokens, API keys, database/Redis credentials, identity and security configuration | Secret manager only; never logs, traces, prompts, client bundles, or backups without encryption. |

Collect only operationally necessary fields. Workforce analytics are informational and must never trigger automatic disciplinary decisions. Access requires an approved business role and periodic review.

Defaults are traces 30 days, evaluations and feedback 365 days, failed jobs 90 days, and audit events 730 days. Legal or operational holds override cleanup. Cleanup records counts and failures but never content. Active prompt versions and knowledge documents are excluded from generic cleanup.

Deletion requests are authenticated, authorized, reviewed against holds, and recorded in the audit log. Where records must remain for integrity, direct identifiers are irreversibly hashed or anonymized. Original uploads follow the organization object-storage lifecycle policy. Feedback is anonymized before analytics when identity is unnecessary.
