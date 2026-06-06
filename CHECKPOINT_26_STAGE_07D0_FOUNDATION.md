# CHECKPOINT 26 — Stage 7D.0 Unified Report Foundation

Stable base: **Checkpoint 25 — Stage 7C completed / rules locked**

## What changed

Stage 7D.0 added a docs-only foundation for a future unified KURGIN Report / PDF / Assets system.

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
min_diameter
max_diameter
height
cut_grade
symmetry
polish
fluorescence
tags
```

Detail card may later show expanded public-safe data, KURGIN Analyzer Report PDF/reference, lab report, photos/videos/assets.

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
