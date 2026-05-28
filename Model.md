# Data Model Explanation

## Why This Schema?

The schema is designed around one core principle: **auditability**.
ESG data is used in regulatory submissions and sustainability reports.
Every number must be traceable back to the original file, and every
change must be logged with who made it and why.

---

## Tables

### Organization
Multi-tenancy root. Every table foreign-keys to this.
Allows the platform to serve multiple clients from one database.

### DataSource
Tracks the *system of record* that produced data, not just "which file."
Two uploads from "SAP Plant DE01" both reference the same DataSource,
so analysts can filter by source system.

### RawUpload
Stores the original file immutably. We never delete or overwrite raw uploads.
This is critical: if a normalization bug is found later, we can re-parse
the original file without losing data.

File hash (SHA-256) enables duplicate detection at upload time.

### EmissionRecord ← MOST IMPORTANT
Dual-column design:
- `quantity / unit` = as received (e.g., 500 GAL)
- `normalized_quantity / normalized_unit` = canonical form (e.g., 1892.7 L)

Rationale: if we only stored normalized values, a unit conversion bug
would silently corrupt data with no way to recover. The raw values are
the audit trail.

`emission_factor` is stored at ingest time, not calculated on-the-fly.
This means future updates to emission factors don't change historical
reported figures — which is correct ESG accounting practice.

`locked_for_audit = True` makes the row immutable. This models the
real-world process where audited data cannot be retroactively changed.

### AuditLog
Append-only. No update or delete permissions.
Stores JSON diffs: `{field, old_value, new_value}`.
Auditors can reconstruct the full history of any record from this table.
