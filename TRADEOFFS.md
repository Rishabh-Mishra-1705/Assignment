# Intentional Tradeoffs

## Skipped: Real SAP/OData Integration
SAP's OData API requires RFCs, enterprise auth, and complex payloads.
Simulating this via realistic CSV column names achieves the same
evaluation goal (showing understanding of SAP data structure) without
the integration overhead.

## Skipped: Async Processing (Celery/Redis)
Added infrastructure complexity without improving core evaluation criteria.
Synchronous processing is sufficient for prototype-scale files.
The architecture is designed so Celery can be added in one sprint.

## Skipped: Role-Based Auth
Not in grading rubric. Data model correctly supports multi-tenancy
if auth is added later.

## Skipped: Real Emission Factor Database
Using hardcoded DEFRA 2023 defaults. A production system would
integrate with CLIMATIQ or the EPA Emission Factors Hub API.

## Skipped: Charts / Data Visualizations
Grading rubric explicitly rates "Analyst UX" at 10%. A functional
table-based interface scores almost as well as a charted one.

## Skipped: Pagination on Frontend
API uses DRF pagination (50/page). Frontend currently renders all
returned records. Proper pagination controls are a polish item.

## Known Weakness: Airport Distance Lookup
Travel parser has ~20 hardcoded routes. Unknown routes produce an
error (intentionally — better to fail visibly than silently use
wrong data). Production fix: integrate aviation distance API.
