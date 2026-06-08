# NEXT CHAT START HERE — KURGIN Admin

Stable checkpoint:

```text
Checkpoint 30 — Stage 7F.0 Public Export / Public Card Schema Contract
```

Previous checkpoints:

```text
Checkpoint 25 — Stage 7C completed / rules locked
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
Checkpoint 27 — Stage 7D Public Layer Rules
Checkpoint 28 — Stage 7E Public Layer Preview/Audit
Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes
```

## Current state

```text
7C writes final prices to stones_master.csv with preview + confirmation + backup.
7D documents public-layer rules.
7E adds read-only Admin preview/audit of the future public layer.
7E.1 fixes KURGIN Score range visibility, price navigation and fluorescence display.
7F.0 documents the future public export / public card schema contract.
```

## 7F.0 locked decisions

```text
Canonical future export file: public_stones_v1.csv
Do not silently replace legacy/current stones.csv.
Public site displays only prepared public_price_display.
Public site does not calculate price.
PDF generator does not calculate price.
Export must not include internal/admin/formula fields.
7F.0 does not write exports, kurgin-data, site sync, PDF/assets or CSV data.
```

## Public export boundary

Allowed public export rows later:

```text
public_numeric_price
public_price_on_request
```

Forbidden as public export rows:

```text
not_public
data_problem
hidden_by_status
hidden_by_availability_status
hidden_by_catalog_section
missing_price
ready_but_not_published
```

## Important constraints

```text
Do not write exports yet.
Do not write kurgin-data yet.
Do not publish/sync stones yet.
Do not create PDF/assets yet.
Do not change stones_master.csv from public-layer/export preview.
Do not change status / availability_status / catalog_section from public-layer/export preview.
Do not turn on allow_price_on_request from public-layer/export preview.
```

## Next reasonable topic

Discuss 7F implementation rules before code:

```text
7F — Admin in-memory public export preview/download
```

7F should:

```text
read public-layer preview
build public_stones_v1.csv in memory
show/download public-safe rows
not write exports/
not write kurgin-data
not sync with site
not mutate stones_master.csv
```

Do not start 7F code until rules are confirmed.
