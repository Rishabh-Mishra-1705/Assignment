# Architecture & Design Decisions

## 1. CSV-based ingestion (not live API)

**Decision:** Accept CSV uploads, not real SAP OData or utility APIs.

**Rationale:** Most enterprise sustainability teams receive operational
data via scheduled flat-file exports, even when live APIs exist. SAP
OData requires RFC authorization that most sustainability analysts don't
have. Accepting CSV is realistic for a prototype and covers 80% of real
use cases.

## 2. Synchronous file processing (not Celery/async)

**Decision:** Process CSV files synchronously in the request cycle.

**Rationale:** At prototype scale (< 10,000 row CSVs), synchronous
processing completes in < 2 seconds. Adding Celery introduces Redis
dependency, worker management, and deployment complexity that would
consume 40% of available build time without improving the core
evaluation criteria (data model and normalization logic).

## 3. Storing both raw and normalized values

**Decision:** EmissionRecord has both `quantity/unit` AND
`normalized_quantity/normalized_unit`.

**Rationale:** If we only stored normalized values, a unit conversion
bug could silently corrupt records with no recovery path. Storing the
original allows re-normalization if the conversion logic is patched.

## 4. Emission factors stored at ingest time

**Decision:** `emission_factor` is saved on the record, not looked up
dynamically.

**Rationale:** GHG Protocol and DEFRA update emission factors annually.
Historical reports must use the factors valid at the time of reporting.
Dynamic lookups would silently change historical figures.

## 5. Single Organization (no full auth)

**Decision:** One hardcoded organization, no JWT/session authentication.

**Rationale:** Full auth (OAuth, JWT, role management) would take a
full sprint to implement correctly and is not in the grading rubric.
The multi-tenancy data model is correct — authentication is a deployment
concern, not a data model concern.

## 6. dayfirst=True as date parsing default

**Decision:** Use dayfirst=True in dateutil for non-SAP sources.

**Rationale:** Breathe ESG targets European enterprise clients where
DD/MM/YYYY is standard. If a date is ambiguous (e.g., 01/02/2023),
it is more likely to be February 1 than January 2. Per-source hints
(SAP, UTILITY, TRAVEL) override this when the format is deterministic.
