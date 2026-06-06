# Unified KURGIN Report / PDF / Assets Foundation V1

Status: **docs-only foundation**  
Stage: **7D.0**  
Stable base: **Checkpoint 25 — Stage 7C completed / rules locked**

This document defines the future shared foundation for KURGIN Report, PDF output, catalog stone cards and assets. It does not implement PDF generation, asset management or public export.

## 1. Purpose

The goal is to prevent separate incompatible report/PDF systems from appearing in different KURGIN applications.

Correct future principle:

```text
one shared ReportPayloadV1
one future unified KURGIN Report / PDF generator
multiple ReportMode values
mode-specific visibility rules
```

Incorrect future principle:

```text
Admin PDF generator
Private Analyzer PDF generator
Public Stone Analyzer PDF generator
Mass Analyzer PDF generator
Catalog Card PDF generator
```

## 2. Repository boundaries

### kurgin-admin-mvp

Admin remains the source for:

```text
stones_master.csv
catalog sections
admin status
availability_status
price_status
price_source
public_price_display
allow_price_on_request
future public-layer decisions
```

Admin must not become the private formula owner or a separate PDF-generator platform.

### kurgin-score-analyzer

Analyzer remains the source for:

```text
score analysis
interpretation
technical report logic
private analysis experience
current prototype PDF/report logic
```

Existing analyzer PDF/report logic is a prototype / candidate source for future shared report core. It is not the final independent production generator for every KURGIN surface.

### kurgin-streamlit-mvp

Public MVP/site remains the public presentation layer:

```text
catalog UI
public Analyzer entry points
future stone detail card
future report display
```

It must not own admin publish authority, private formula internals or independent price calculation.

### kurgin-formula-service

Future formula service should provide controlled analysis output, not public UI or PDF ownership.

### kurgin-data

Data repository remains the published/shared data layer. It should receive public-safe outputs only after Admin rules decide what can be exposed.

## 3. V1 scope

V1 is only a contract/foundation.

V1 may define:

```text
ReportPayloadV1 sections
ReportMode values
visibility rules
Catalog Stone Card Contract
future report references
future asset references
future stone_assets.csv concept
V1/V2 boundary
```

V1 must not implement:

```text
PDF generation
PDF viewer
PDF upload
active asset manager
active stone_assets.csv
automatic KURGIN Report creation
public site PDF integration
separate kurgin-report-core package
```

## 4. V2 scope

V2 may implement:

```text
unified PDF generator
shared report package / kurgin-report-core
PDF bytes/file generation
PDF viewer
report storage lifecycle
active stone_assets.csv
asset manager
lab report linking
photos/videos/gallery
integration of reports into site stone details
```

## 5. ReportPayloadV1 — logical contract

`ReportPayloadV1` is a logical data contract. In 7D.0 it is not a Python class, database table or active API schema.

### 5.1 meta

```text
payload_version
report_id
report_mode
report_status
created_at
source_system
template_version
engine_version
formula_output_version
visibility_policy_version
language
```

### 5.2 source_context

```text
source_repo
source_file
source_row_id
source_import_id
created_from
created_by
input_hash
payload_hash
```

### 5.3 stone_identity

```text
stone_id
kurgin_import_id
report_number
stock_number
lab
stone_title
identification_line
```

### 5.4 certificate_data

```text
shape
weight
color
clarity
cut_grade
polish
symmetry
fluorescence
measurements
report_issue_date
report_type
growth_method
diamond_type
treatment
inscription
certificate_comment
```

### 5.5 geometry

```text
min_diameter
max_diameter
avg_diameter
depth_mm
height
length
width
ratio
depth_percent
table_percent
crown_angle
pavilion_angle
crown_percent
pavilion_percent
girdle_percent
diameter_diff
roundness_deviation
```

### 5.6 kurgin_score

```text
kurgin_score
score_band
score_band_label_ru
verdict_local
tags
tag_light
tag_structure
tag_spread
tag_risk
tag_certificate
tag_commercial
data_completeness
report_quality_status
calculation_status
```

### 5.7 interpretation

```text
executive_summary
interpretation_short
interpretation_detail
recommendation
warning
disclaimer
limitations
```

### 5.8 commercial_context

Commercial context is provided by Admin/catalog logic. The report generator does not calculate it and does not mutate it.

```text
price_status
price_source
public_price_display
public_price_total_rub
allow_price_on_request
availability_status
catalog_section
status
```

Commercial display is optional for card/report modes. Price is not required for the identity of the stone card.

### 5.9 catalog_card_summary

Future public site card summary fields:

```text
shape
carat
color
clarity
kurgin_score
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
tags
```

This block is public-safe by default, subject to visibility policy.

### 5.10 catalog_card_detail

Future detail view may include:

```text
all catalog_card_summary fields
report_number
lab
measurements
depth_percent
table_percent
ratio
score_band
public_interpretation_short
public_recommendation
public_warning
report_refs
asset_refs
```

The detail card may show a KURGIN Analyzer Report PDF/reference when available, but the card itself does not generate PDF.

### 5.11 report_refs_future

Future-only in V1:

```text
kurgin_report_pdf_url
kurgin_report_status
kurgin_report_template_version
kurgin_report_created_at
lab_report_pdf_url
```

### 5.12 assets_future

Future-only in V1:

```text
main_image_url
gallery_images
video_urls
asset_status
asset_source
asset_updated_at
```

### 5.13 private_formula_internals

This is not public. It may exist in private analyzer/service output but must not be exposed through public report modes.

Examples:

```text
formula weights
thresholds
penalties
raw diagnostics
breakdown internals
cap logic
candidate formula internals
private API secrets
```

## 6. ReportMode

Canonical modes:

```text
internal_admin
private_analyzer
public_stone_analyzer
mass_analyzer_row
catalog_stone_card
```

### 6.1 internal_admin

For Admin and internal verification.

May show:

```text
certificate data
geometry
score
warnings
data quality
price_status
price_source
public_price_display
status
availability_status
catalog_section
future report_refs
future asset_refs
```

Must not disclose private formula internals unless separately authorized.

### 6.2 private_analyzer

For personal/internal analyzer use.

May show:

```text
fuller analysis
geometry diagnostics
risk signals
interpretation detail
recommendation
warnings
data completeness
```

Must not automatically become a public report.

### 6.3 public_stone_analyzer

For public analyzer service on the site.

May show:

```text
score / score band
short interpretation
recommendation
warning
limitations
not-a-certificate disclaimer
data completeness
```

Must not show:

```text
formula internals
raw diagnostics
thresholds
penalties
private commercial/admin fields
```

### 6.4 mass_analyzer_row

For one row of mass analysis.

May show:

```text
row_id
input identifiers
score
band
short interpretation
quality status
warnings
recommended action
```

Must not:

```text
automatically publish catalog data
create orders
create reserves
create payments
claim to be a certificate
reveal formula internals
```

### 6.5 catalog_stone_card

For public catalog card and future detail page.

Submodes:

```text
summary_view
detail_view
```

Summary view may show:

```text
shape
carat
color
clarity
kurgin_score
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
tags
```

Detail view may show:

```text
summary fields
additional public-safe certificate/geometry fields
public-safe interpretation
future KURGIN Report PDF reference
future lab report reference
future photos/videos/assets
```

The card does not generate PDF. It consumes public-safe data and future report references.

## 7. Visibility rules

Base rule:

```text
ReportPayloadV1 may contain more data than a specific mode displays.
Visibility Policy decides what is visible.
```

Public-safe by default:

```text
shape
carat
weight
color
clarity
lab
report_number
measurements
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
kurgin_score
score_band
score_band_label_ru
public tags
short interpretation
public recommendation
public warning
data completeness
report quality status
public_price_display if commercial context allows it
```

Internal-only by default:

```text
formula weights
thresholds
penalties
raw diagnostics
breakdown internals
private API details
supplier cost internals
internal margin logic
admin-only comments
```

## 8. PDF generator rules

Future generator must:

```text
accept prepared ReportPayloadV1
apply visibility policy
create PDF bytes/file
return report_id
return report_status
return template_version
return created_at
be reusable between Admin, Analyzer and site
```

Future generator must not:

```text
calculate prices
change stones_master.csv
change status
change availability_status
change catalog_section
enable allow_price_on_request
publish a stone
create order/reserve/purchase
expose private formula internals
be irreversibly tied to Streamlit Cloud
```

## 9. Portability rules

The foundation must stay portable:

```text
business contract outside Streamlit UI
no absolute Streamlit Cloud paths in rules
no dependency on st.session_state
no runtime-only data as source of truth
no automatic writes to exports/
future generator callable from Admin, Analyzer, website backend, API or batch process
```

## 10. Future stone_assets.csv concept

Future-only concept, not active in V1:

```text
stone_id
asset_id
asset_type
asset_url
asset_status
asset_source
sort_order
created_at
updated_at
```

Possible asset types:

```text
kurgin_report_pdf
lab_report_pdf
main_image
gallery_image
video
other_document
```

## 11. Stage order

```text
Checkpoint 25 — Stage 7C completed / rules locked
7D.0 — docs-only foundation for Unified Report / PDF / Assets
7D — rules for public layer
7E — read-only public-layer preview/audit in Admin
7F / 8A — export/public card schema
V1 release — without PDF generator
V2 — unified PDF generator
```

## 12. Explicit non-goals for 7D.0

```text
no code
no PDF generation
no PDF viewer
no PDF upload
no asset manager
no active stone_assets.csv
no stones_master.csv schema change
no public export
no Streamlit UI change
no ZIP for data/backups/exports
```
