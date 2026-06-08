# Checkpoint 30 — Stage 7F.0 Public Export / Public Card Schema Contract

Stable base before this checkpoint:

```text
Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes
```

## Status

```text
7F.0 completed as docs-only foundation.
No code changed.
No export generated.
No data changed.
No PDF/assets/site integration implemented.
```

## What was documented

```text
future public export contract
future public card schema fields
canonical public_stones_v1.csv name
allowed public export statuses
price_display_type values
forbidden internal/admin/formula fields
relationship with kurgin-data
legacy stones.csv migration boundary
future PDF/assets flags
V1/V2 boundary
```

## Canonical future export file

```text
public_stones_v1.csv
```

`public_stones_v1.csv` must not silently replace existing/legacy `stones.csv`. The public site must be explicitly migrated to the new schema in a separate stage.

## Future flow

```text
KURGIN Admin
↓
7E public-layer preview/audit
↓
7F public export preview/download
↓
8A controlled publish path
↓
kurgin-data
↓
public site / catalog card
```

## 7F.0 allowed

```text
write documentation
lock public export contract
lock public-safe card fields
lock forbidden export fields
lock kurgin-data boundary
```

## 7F.0 forbidden

```text
change app.py
change modules/
change stones_master.csv
change catalog_sections.csv
write exports/
write kurgin-data
sync with site
generate PDF
create asset manager
create database persistence
```

## Public export can include only public-safe prepared fields

Key future fields:

```text
stone_id
report_number
lab
catalog_section
section_name
public_card_status
public_visibility_reason
shape
weight
carat_label
color
clarity
kurgin_score
kurgin_score_range_label
public_price_display
price_display_type
min_diameter
max_diameter
height / depth_mm
cut_grade
symmetry
polish
fluorescence
tags
availability_status_public
future detail/report/asset flags
```

## Price contract

```text
The public site displays only public_price_display.
The public site does not calculate price.
The future PDF generator does not calculate price.
Raw/internal price fields are never public export fields.
```

`price_display_type` values:

```text
numeric
price_on_request
```

## Forbidden public export fields

```text
supplier_price_*
internal_price_*
start_price_*
working_price_*
price_fx_usd_rub
price_calculated_at
price_source
price_warning
admin_note
price_comment
shipment_id
supplier_id
supplier_name
import_id
updated_import_id
last_source_file
raw_source_file
margins
formula internals
raw diagnostics
breakdown
private API keys
private service URLs
```

## Next possible stage

```text
7F — Admin in-memory public export preview/download
```

7F must still be safe:

```text
read public-layer preview
build public_stones_v1.csv in memory
show/download public-safe rows
not write exports/
not write kurgin-data
not sync with site
not mutate stones_master.csv
```

No 7F code should be written until its implementation rules are confirmed.
