# CHECKPOINT 27 — Stage 7D Public Layer Rules

Stable base: **Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation**

## What changed

Stage 7D documented public-layer rules for future catalog publication and public export.

No application code changed.

## Confirmed public-layer principle

```text
Admin decides public eligibility.
The public site/card/PDF generator do not calculate price and do not mutate Admin data.
The public layer uses only prepared public-safe fields.
```

## Public eligibility baseline

A stone may enter the public catalog layer only if:

```text
status = published
availability_status = in_stock
catalog_section is filled
catalog_section exists in catalog_sections.csv
catalog_sections.is_public = true
```

## Price rule

Price is part of the public stone card.

The card may show only:

```text
public_price_display
```

Numeric public price is allowed when:

```text
price_status = calculated
public_price_display is filled
public_price_total_rub is filled
```

“Цена по запросу” is allowed only when:

```text
price_status = missing_supplier_price
allow_price_on_request = true
public_price_display = Цена по запросу
```

## Public card summary

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

## Required fields for V1 publication

```text
shape
weight
color
clarity
kurgin_score
public_price_display
```

Secondary card fields should warn but not block in V1.

## Future audit groups

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

## Files changed

```text
README.md
rules/README_RULES.md
docs/PUBLIC_LAYER_RULES_V1.md
CHECKPOINT_27_STAGE_07D_PUBLIC_LAYER_RULES.md
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

Do not implement public export yet.

Next recommended stage:

```text
7E — Admin preview/audit of the public layer
```

Before 7E code, verify that these 7D rules are accepted.
