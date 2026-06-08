# KURGIN Public Export / Public Card Schema Contract V1

Status: **docs-only contract**  
Stage: **7F.0**  
Stable base: **Checkpoint 29 — Stage 7E.1 Public Layer UI Fixes**

This document defines the future public export and public card schema contract. It does not implement export, sync, site integration, PDF generation, asset management, database persistence or data mutation.

## 1. Purpose

7F.0 answers one question:

```text
What exact public-safe data contract may Admin later export for the public site / catalog card?
```

7F.0 is a documentation-only foundation. It must not:

```text
write export files
write exports/
write kurgin-data
sync with the public site
change stones_master.csv
change catalog_sections.csv
change status
change availability_status
change catalog_section
change prices
turn on allow_price_on_request
create backups
create PDFs
create assets
create orders / reserves / payments
```

## 2. Intended future flow

The future flow should be:

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

Admin remains the authority for publication decisions and prepared commercial display. The public site must not independently calculate price or decide publication.

## 3. Future export file name

The canonical future public export file should be:

```text
public_stones_v1.csv
```

This name is intentionally versioned. It should not silently replace existing legacy files such as:

```text
stones.csv
```

until the public site is explicitly migrated to the V1 contract.

## 4. Export eligibility

Only rows that passed the 7D / 7E public-layer rules may enter `public_stones_v1.csv`.

Allowed public statuses:

```text
public_numeric_price
public_price_on_request
```

Rows with these states must not be exported as public rows:

```text
not_public
data_problem
hidden_by_status
hidden_by_availability_status
hidden_by_catalog_section
missing_price
ready_but_not_published
```

Manual prices may be exported only as public display values if all public-layer conditions pass. The public export must not reveal whether the price was manual or auto-calculated.

## 5. Public card summary schema

The future public catalog card summary should use these public-safe fields:

```text
schema_version
exported_at
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
height
depth_mm
cut_grade
symmetry
polish
fluorescence
tags

availability_status_public
detail_available
kurgin_report_available
lab_report_available
main_image_available
```

`public_price_display` is part of the public card summary.

The card must show only the prepared public display price, never raw price components.

## 6. Price display contract

The export must contain:

```text
public_price_display
price_display_type
```

Canonical `price_display_type` values:

```text
numeric
price_on_request
```

Rules:

```text
numeric:
    public_price_display contains a prepared numeric customer-facing price.

price_on_request:
    public_price_display = Цена по запросу.
```

The export should not include `hidden` rows. `hidden` remains an internal audit concept, not a public export row.

The public site must not calculate price. It must display `public_price_display` as provided by Admin/export.

## 7. Public card status

The export must contain:

```text
public_card_status
```

Canonical public export values:

```text
public_numeric_price
public_price_on_request
```

Admin audit may contain additional internal statuses, but they should not become public export rows.

## 8. Public visibility reason

The export may contain:

```text
public_visibility_reason
```

For exported rows, this should be a public-safe explanation, for example:

```text
published / in_stock / public section / numeric price
published / in_stock / public section / price on request
```

Do not expose internal diagnostics, formula details, private price source or admin warnings in this field.

## 9. Public-safe field mapping

Recommended mapping from Admin / Analyzer fields:

```text
stone_id                    ← stones_master.stone_id
report_number               ← stones_master.report_number
lab                         ← stones_master.lab
catalog_section             ← stones_master.catalog_section
section_name                ← catalog_sections.section_name_ru or section_name_en
shape                       ← stones_master.shape
weight                      ← stones_master.weight
carat_label                 ← formatted weight
color                       ← stones_master.color
clarity                     ← stones_master.clarity
kurgin_score                ← public-safe KURGIN Score
kurgin_score_range_label    ← recorded score range label
public_price_display        ← stones_master.public_price_display
price_display_type          ← derived public-safe display type
min_diameter                ← public-safe measurement
max_diameter                ← public-safe measurement
height / depth_mm           ← public-safe measurement
cut_grade                   ← public-safe cut grade
symmetry                    ← stones_master.symmetry
polish                      ← stones_master.polish
fluorescence                ← display value; blank/none-like must render as None
tags                        ← public-safe tags only
```

Analyzer fields used in public export must be public-safe. Raw formula internals and private diagnostics must not be exported.

## 10. Forbidden export fields

The future public export must not include:

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
expense coefficients
formula internals
formula thresholds
formula penalties
raw diagnostics
breakdown
private API keys
private service URLs
```

The public site, public export and future PDF generator must not reveal private formula internals.

## 11. Relationship with kurgin-data

`kurgin-data` is the intended future data layer for the public MVP/site.

7F.0 only defines a contract. It does not write to `kurgin-data`.

A later controlled publish stage may place the public export in `kurgin-data` only after:

```text
public_stones_v1.csv schema is accepted
Admin preview/download is tested
site reader compatibility is confirmed
rollback/manual restore path is known
```

## 12. Relationship with existing stones.csv

Existing `kurgin-data/stones.csv` should be treated as legacy / current MVP data until migration.

Do not silently change its schema.

Recommended later migration path:

```text
1. add public_stones_v1.csv as a new file
2. make the public site read public_stones_v1.csv in a separate site stage
3. only then decide whether stones.csv is deprecated, kept, or mapped
```

## 13. Relationship with PDF / assets foundation

Public export may include future flags:

```text
detail_available
kurgin_report_available
lab_report_available
main_image_available
```

But V1 must not implement:

```text
PDF generation
PDF upload
PDF viewer
asset manager
stone_assets.csv as active table
lab report storage
photo/video/gallery storage
```

Future fields may be added later:

```text
kurgin_report_pdf_url
lab_report_pdf_url
main_image_url
gallery_images
asset_status
```

These remain future-only until V2 / assets stages.

## 14. V1 / V2 boundary

7F.0 V1 includes:

```text
public export contract
public card schema fields
allowed public price display types
forbidden internal fields
relationship with kurgin-data
future migration path
```

7F.0 V1 does not include:

```text
export generation
export download button
writing exports/
committing data files
syncing to kurgin-data
public site reader changes
PDF/assets implementation
DB persistence
```

Recommended next stage after 7F.0 rules are committed:

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
