# CHECKPOINT 26 — Stage 7D.0 Unified Report Foundation

Stable base: **Checkpoint 25 — Stage 7C completed / rules locked**

## What changed

Stage 7D.0 added a docs-only foundation for a future unified KURGIN Report / PDF / Assets system. It was later clarified that public catalog cards include price display and that future specialist/client views require separate price visibility contexts.

No application code changed.

## Confirmed principle

```text
one shared ReportPayloadV1
one future unified KURGIN Report / PDF generator
multiple ReportMode values
mode-specific visibility rules
```

## ReportMode values

```text
internal_admin
private_analyzer
public_stone_analyzer
mass_analyzer_row
catalog_stone_card
```

## Catalog stone card future summary

```text
shape
carat
color
clarity
kurgin_score
public_price_display
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
tags
```

Price is part of the public card summary only as prepared public display. Raw/internal price fields are not public.

Detail card may later show expanded public-safe data, KURGIN Analyzer Report PDF/reference, lab report, photos/videos/assets.


## Future price visibility contexts

```text
internal_admin
specialist_private
specialist_client_view
public_catalog
public_analyzer
```

These contexts are future-only in V1. They reserve the rule that a specialist's private cabinet and a specialist's client-facing view may show different prepared price displays.

Do not implement specialist pricing, price tiers or account-specific price calculation in this checkpoint.

## V1 boundary

V1 is rules/contracts only for this foundation.

Do not implement in V1:

```text
PDF generation
PDF viewer
PDF upload
active stone_assets.csv
asset manager
automatic KURGIN Report creation
public site PDF integration
separate kurgin-report-core package
```

## V2 boundary

V2 may implement the actual shared generator and active report/assets pipeline.

## Files changed

```text
README.md
rules/README_RULES.md
docs/UNIFIED_KURGIN_REPORT_FOUNDATION_V1.md
CHECKPOINT_26_STAGE_07D0_FOUNDATION.md
NEXT_CHAT_START_HERE.md
```

## Must not be in Changes

```text
app.py
modules/
data/
backups/
exports/
__pycache__/
tmp/
current_working_code/
test files
```

## Next step

Discuss Stage 7D rules for the public layer before writing any code.
