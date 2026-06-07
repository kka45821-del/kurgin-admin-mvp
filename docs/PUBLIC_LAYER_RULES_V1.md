# KURGIN Public Layer Rules V1

Status: **docs-only rules**  
Stage: **7D**  
Stable base: **Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation**

This document defines the public-layer rules for future catalog publication and public export. It does not implement publication, export, UI, sync, PDF generation or data mutation.

## 1. Purpose

Stage 7D answers one question:

```text
Which stones may be shown outside Admin, and in what form?
```

7D is rules-only. It must not:

```text
write export files
change stones_master.csv
change status
change availability_status
change catalog_section
change prices
turn on allow_price_on_request
create backups
create PDFs
send data to the public site
```

## 2. Public-layer authority

Admin remains the authority for publication decisions.

The public layer must be derived from prepared Admin fields and public-safe Analyzer fields. The public site, card UI, PDF generator and Analyzer display must not calculate price, mutate Admin data or decide publication independently.

Correct future flow:

```text
stones_master.csv + catalog_sections.csv + Analyzer public-safe output
        ↓
public-layer rules
        ↓
public preview / audit
        ↓
future public export / site card
```

## 3. Required base conditions

A stone may enter the public catalog layer only if all base conditions are true:

```text
status = published
availability_status = in_stock
catalog_section is not empty
catalog_section exists in catalog_sections.csv
catalog_sections.is_public = true
```

If any base condition is false, the stone is not public.

## 4. Status rules

```text
draft      → not public
ready      → ready inside Admin, but not public
published  → may continue public checks
archived   → not public
```

`ready` must not be exported as public in V1.

## 5. Availability rules

```text
in_stock  → may continue public checks
reserved  → not public in V1
sold      → not public
removed   → not public
```

`reserved` should be handled later as a separate business rule if needed. It must not be public by default in V1.

## 6. Catalog section rules

```text
catalog_section empty        → hidden by section
catalog_section not found    → data problem
is_public != true            → hidden by section
is_public = true             → may continue public checks
```

This keeps private inventory, hidden collections and future specialist-only sections possible.

## 7. Price rules

Price is part of the public stone card.

The public card may show only:

```text
public_price_display
```

The public card, site and future PDF generator must not show or calculate:

```text
supplier price
internal price
start price
working price
margin
price_source
price_fx_usd_rub
price_calculated_at
admin price metadata
```

### 7.1 Numeric public price

A stone may be public with numeric price if:

```text
price_status = calculated
public_price_display is filled
public_price_total_rub is filled
price_source is auto_calculated or manual
```

`price_source = manual` is allowed for public display, but Admin audit must mark it as:

```text
Manual price review
```

The public user must not see the manual/auto technical marker.

### 7.2 Price on request

A stone may be public as “Цена по запросу” only if:

```text
price_status = missing_supplier_price
allow_price_on_request = true
public_price_display = Цена по запросу
```

If:

```text
price_status = missing_supplier_price
allow_price_on_request != true
```

then the stone must not enter the public commercial catalog.

## 8. Public catalog card summary

The future public card summary must include:

```text
shape
carat / weight
color
clarity
kurgin_score
public_price_display
min_diameter
max_diameter
height / depth_mm
cut_grade
symmetry
polish
fluorescence
tags
```

### Required for V1 public card

These fields are publication blockers if missing:

```text
shape
weight
color
clarity
kurgin_score
public_price_display
```

### Warning-only for V1 public card

These fields should produce an Admin audit warning if missing, but should not block publication in V1:

```text
min_diameter
max_diameter
height / depth_mm
cut_grade
symmetry
polish
fluorescence
tags
```

## 9. Detail card — future-only

Future detail card may show:

```text
same public card summary
expanded public-safe stone details
KURGIN Analyzer Report PDF/reference
lab report reference
photos/videos/assets
```

In V1 this is only a contract. No detail card UI, PDF viewer, asset manager or PDF generation is implemented.

## 10. Public export — future fields

A future public export may include only public-safe fields such as:

```text
stone_id
report_number
lab
shape
weight
color
clarity
kurgin_score
score_status
public_price_display
price_status_public
availability_status_public
catalog_section
section_name
min_diameter
max_diameter
depth_mm
cut_grade
symmetry
polish
fluorescence
tags
public_card_status
public_visibility_reason
```

Future export must not include:

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
shipment_id
supplier_name
import_id
source_file
margins
formula internals
raw diagnostics
private formula thresholds
private penalties
```

## 11. Future audit groups

The future Admin public-layer preview/audit should group stones as:

```text
Public OK — numeric price
Public OK — price on request
Ready but not published
Hidden by status
Hidden by availability_status
Hidden by catalog_section
Missing price
Manual price review
Data problems
```

7D only defines these groups. UI implementation belongs to a later stage.

## 12. Relationship with ReportPayloadV1 and PDF foundation

Public-layer rules must stay compatible with the 7D.0 foundation:

```text
ReportPayloadV1 carries prepared data.
ReportMode controls report/card context.
PriceVisibilityContext controls which prepared price display is allowed.
Visibility Policy decides which fields are visible.
```

The public catalog card and future KURGIN Report PDF may use the same payload foundation, but neither one may calculate price, mutate Admin data or reveal private formula internals.

## 13. V1 / later-stage boundary

7D V1 includes:

```text
public-layer rules
public-safe field list
status / availability / section / price visibility logic
future audit group definitions
future public export boundaries
```

7D V1 does not include:

```text
Streamlit public-layer UI
CSV export files
site sync
kurgin-data update
PDF generation
asset manager
specialist cabinet pricing
order/reserve/payment logic
```

Recommended next stage after 7D rules are committed:

```text
7E — Admin preview/audit of the public layer
```
