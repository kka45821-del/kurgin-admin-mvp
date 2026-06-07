# NEXT CHAT START HERE — KURGIN Admin

Continue from stable checkpoint **27**.

## Stable checkpoint

```text
Checkpoint 27 — Stage 7D Public Layer Rules
```

## Previous stable checkpoints

```text
Checkpoint 25 — Stage 7C completed / rules locked
Checkpoint 26 — Stage 7D.0 Unified Report / PDF / Assets foundation
```

## Current confirmed state

```text
7C works
price write to stones_master.csv works
backup before price write is mandatory
manual prices are not silently overwritten
missing supplier price stones do not receive numeric prices
allow_price_on_request is not enabled automatically
Цена по запросу requires separate confirmed action
GitHub main contains 7C
```

## Stage 7D.0 status

```text
Unified Report / PDF / Assets foundation documented
ReportPayloadV1 future contract documented
ReportMode values documented
Catalog Stone Card future contract documented
PriceVisibilityContext future rule documented
no PDF generator
no asset manager
no export/sync
```

## Stage 7D status

```text
public-layer rules documented
no app.py changes
no modules changes
no data/schema changes
no Streamlit UI changes
no exports
no sync
```

## Public eligibility baseline

A stone may enter the future public catalog layer only if:

```text
status = published
availability_status = in_stock
catalog_section is filled
catalog_section exists in catalog_sections.csv
catalog_sections.is_public = true
```

## Price rule

Price is part of the public stone card. The public layer may show only prepared:

```text
public_price_display
```

Numeric price requires:

```text
price_status = calculated
public_price_display is filled
public_price_total_rub is filled
```

“Цена по запросу” requires:

```text
price_status = missing_supplier_price
allow_price_on_request = true
public_price_display = Цена по запросу
```

## Future public card summary

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

## Do not do without separate approval

```text
Do not implement PDF generator.
Do not add PDF viewer.
Do not upload/link real assets.
Do not activate stone_assets.csv.
Do not change stones_master.csv schema for assets.
Do not create kurgin-report-core yet.
Do not write public export files.
Do not sync to site.
Do not mutate stones_master.csv in public-layer audit.
Do not install old draft 7D ZIPs.
```

## Next recommended stage

Discuss and then implement only after approval:

```text
7E — Admin preview/audit of the public layer
```

7E should be read-only:

```text
read stones_master.csv
read catalog_sections.csv
apply Stage 7D rules
show groups and reasons in Admin
allow download of preview from memory
no CSV mutation
no exports/ writes
no backup creation
no site sync
```
